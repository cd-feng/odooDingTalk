// Part of web_progress. See LICENSE file for full copyright and licensing details.
odoo.define('web.progress.bar', function (require) {
"use strict";

/**
 * Display Progress Bar when blocking UI
 */

var core = require('web.core');
var Widget = require('web.Widget');
var progress_loading = require('web.progress.loading');
var framework = require('web.framework');
var session = require('web.session');

var _t = core._t;
var QWeb = core.qweb;
var progress_timeout = progress_loading.progress_timeout;
var progress_timeout_warn = progress_timeout*10;
var framework_blockUI = framework.blockUI;
var framework_unblockUI = framework.unblockUI;


var ProgressBar = Widget.extend({
    template: "WebProgressBar",
    progress_timer: false,
    init: function(parent, code, $spin_container) {
        this._super(parent);
        this.progress_code = code;
        this.$spin_container = $spin_container;
        this.systray = !$spin_container;
        this.cancel_html = QWeb.render('WebProgressBarCancel', {});
        this.cancel_confirm_html = QWeb.render('WebProgressBarCancelConfirm', {});
    },
    start: function() {
        this.$progress_frame = this.$("#progress_frame");
        this.$progress_message = this.$("#progress_message");
        this.$progress_cancel = this.$("#progress_cancel");
        this.$progress_bar = this.$("#progress_bar");
        this.$progress_user = this.$("#progress_user");
        core.bus.on('rpc_progress_set_code', this, this.defineProgressCode);
        core.bus.on('rpc_progress', this, this.showProgress);
    },
    defineProgressCode: function(progress_code) {
        if (!this.progress_code) {
            this.progress_code = progress_code;
        }
    },
    showProgress: function(progress_list) {
        var self = this;
        var top_progress = progress_list[0];
        var progress_code = top_progress.code;
        var uid = session.uid;
        var is_admin = session.is_admin;
        if (this.progress_code !== progress_code || !is_admin && uid !== top_progress.uid) {
            return;
        }
        var progress_html = '<div class="text-left">';
        var progress_time_html = '';
        var progress = 0.0;
        var progress_total = 100;
        var cancellable = true;
        var level = '';
        _.each(progress_list, function(el) {
            var message = el.msg || "";
            progress_html += "<div>" + level + " " + el.progress + "%" + " (" + el.done + "/" + el.total + ")" + " " + message + "</div>"
            if (el.progress && el.total) {
                progress += el.progress * progress_total / 100;
            }
            if (el.total) {
                progress_total /= el.total;
            }
            cancellable = cancellable && el.cancellable;
            level += '▶';
            });
        progress_html += '</div>';
        if (top_progress['time_left']) {
            progress_time_html += _t("Est. time left: ") + top_progress['time_left']
        }
        if (top_progress['time_total']) {
            progress_time_html += " / " + top_progress['time_total']
        }
        if (progress_time_html) {
            progress_html = '<div class="text-left">' + progress_time_html + '</div>' + progress_html;
        }
        self.$progress_frame.css("visibility", 'visible');
        if (self.$spin_container) {
            // this is main progress bar
            self.$spin_container.find(".oe_throbber_message").css("display", 'none');
        } else {
            // this is a systray progress bar
            self.$progress_message.removeClass('o_progress_message');
            self.$progress_message.addClass('o_progress_message_systray');
            self.$progress_user.css("visibility", 'visible');
            if (is_admin) {
                self.$progress_user.html(top_progress.user);
            }
        }
        if (cancellable) {
            self._normalCancel();
        } else {
            self.$progress_cancel.html('');
        }
        self.$progress_bar.animate({width: progress + '%'}, progress_timeout);
        this.$progress_message.html(progress_html);
        self._cancelTimeout();
        self._setTimeout();
        },
    _confirmCancel: function () {
        var self = this;
        self.$progress_cancel.html(self.cancel_confirm_html);
        if (this.systray) {
            self.$progress_cancel.find('#cancel_message').addClass('o_cancel_message_systray');
            self.$progress_cancel.find('.btn').addClass('btn-default');
        }
        var $progress_cancel_confirm_yes = self.$progress_cancel.find('#progress_cancel_yes');
        var $progress_cancel_confirm_no = self.$progress_cancel.find('#progress_cancel_no');
        $progress_cancel_confirm_yes.off();
        $progress_cancel_confirm_yes.one('click', function (event) {
            event.stopPropagation();
            self._confirmCancelYes();
        });
        $progress_cancel_confirm_no.off();
        $progress_cancel_confirm_no.one('click', function (event) {
            event.stopPropagation();
            self._normalCancel();
        });
    },
    _confirmCancelYes: function () {
        var self = this;
        core.bus.trigger('rpc_progress_cancel', self.progress_code);
        self.$progress_cancel.html(_t("Cancelling..."));
        if (this.systray) {
            self.$progress_cancel.addClass('o_cancel_message_systray');
        } else {
            self.$progress_cancel.addClass('o_progress_message');
        }
    },
    _normalCancel: function () {
        var self = this;
        self.$progress_cancel.html(self.cancel_html);
        if (this.systray) {
            self.$progress_cancel.find('#cancel_message').addClass('o_cancel_message_systray');
            self.$progress_cancel.find('.btn').addClass('btn-default');
        }
        var $progress_cancel_confirm = self.$progress_cancel.find('#progress_cancel_confirm');
        $progress_cancel_confirm.off();
        $progress_cancel_confirm.one('click', function (event) {
            event.stopPropagation();
            self._confirmCancel();
        });
    },
    _setTimeout: function () {
        var self = this;
        if (!this.progress_timer) {
            this.progress_timer = setTimeout(function () {
                self._notifyTimeoutWarn();
            }, progress_timeout_warn);
        }
    },
    _cancelTimeout: function () {
        if (this.progress_timer) {
            this.$progress_bar.removeClass('o_progress_bar_timeout');
            this.$progress_bar.removeClass('o_progress_bar_timeout_destroy');
            clearTimeout(this.progress_timer);
            this.progress_timer = false;
        }
    },
    _notifyTimeoutWarn: function () {
        var self = this;
        this.$progress_bar.removeClass('o_progress_bar_timeout_destroy');
        this.$progress_bar.addClass('o_progress_bar_timeout');
        this.progress_timer = setTimeout(function () {
            self._notifyTimeoutDestr();
        }, progress_timeout_warn);
    },
    _notifyTimeoutDestr: function () {
        var self = this;
        this.$progress_bar.removeClass('o_progress_bar_timeout');
        this.$progress_bar.addClass('o_progress_bar_timeout_destroy');
        this.progress_timer = setTimeout(function () {
            core.bus.trigger('rpc_progress_destroy', self.progress_code);
        }, progress_timeout_warn);
        self.progress_timer = false;
    },
});

var progress_bars = [];

function blockUI() {
    var tmp = framework_blockUI();
    var $spin_container = $(".oe_blockui_spin_container");
    var progress_bar = new ProgressBar(false, false, $spin_container);
    progress_bars.push(progress_bar);
    progress_bar.appendTo($spin_container);
    return tmp;
}

function unblockUI() {
    _.invoke(progress_bars, 'destroy');
    progress_bars = [];
    return framework_unblockUI();
}

framework.blockUI = blockUI;
framework.unblockUI = unblockUI;

return {
    blockUI: blockUI,
    unblockUI: unblockUI,
    ProgressBar: ProgressBar,
};

});
