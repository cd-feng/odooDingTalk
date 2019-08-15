// Part of web_progress. See LICENSE file for full copyright and licensing details.
odoo.define('web.progress.loading', function (require) {
"use strict";

/**
 * Loading Progress Bar
 */

var core = require('web.core');
var Loading = require('web.Loading');

var _t = core._t;
var progress_timeout = 5000;

Loading.include({

    init: function(parent) {
        this._super(parent);
        this.progress_timers = {};
        core.bus.on('rpc_progress_request', this, this.addProgress);
        core.bus.on("rpc_progress_result", this, this.removeProgress);
        core.bus.on("rpc_progress_cancel", this, this.cancelProgress);
        core.bus.on("rpc_progress_background", this, this.moveToBackground);
    },
    destroy: function() {
        for (var key in this.progress_timers) {
            if (this.progress_timers.hasOwnProperty(key)) {
                clearTimeout(this.progress_timers[key]);
            }
        }
        this._super();
    },
    notifyProgressCode: function(progress_code) {
        core.bus.trigger('rpc_progress_set_code', progress_code);
    },
    getProgressViaRPC: function(progress_code) {
        var self = this;
        this._rpc({
                model: 'web.progress',
                method: 'get_progress',
                args: [progress_code]
            }, {'shadow': true}).then(function (result_list) {
                // console.debug(result_list);
                if (result_list.length > 0) {
                    var result = result_list[0];
                    if (['ongoing', 'done'].indexOf(result.state) >= 0) {
                        core.bus.trigger('rpc_progress_first', result_list)
                    }
                    if (progress_code in self.progress_timers) {
                        self.progress_timers[progress_code] = setTimeout(function () {
                            self.getProgressViaRPC(progress_code)
                        }, progress_timeout);
                    }
                }
        })
    },
    moveToBackground: function() {
        this.count = 0;
        // TODO: add move to background
    },
    cancelProgress: function(progress_code) {
        var self = this;
        this._rpc({
                model: 'web.progress',
                method: 'cancel_progress',
                args: [progress_code]
            }, {'shadow': true}).then(function() {})
    },
    addProgress: function(progress_code) {
        var self = this;
        this.progress_timers[progress_code] = setTimeout(function () {
            self.notifyProgressCode(progress_code);
        }, progress_timeout);
    },
    removeProgress: function(progress_code) {
        if (progress_code in this.progress_timers) {
            clearTimeout(this.progress_timers[progress_code]);
            delete this.progress_timers[progress_code];
        }
    }
});

return {
    Loading: Loading,
    progress_timeout: progress_timeout,
};
});

