odoo.define('dingding_report.report.template.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let Dialog = require('web.Dialog');
    let core = require('web.core');
    let QWeb = core.qweb;
    let rpc = require('web.rpc');

    let save_data = function () {
        rpc.query({
            model: 'dingding.report.template',
            method: 'get_all_template',
            args: [],
        }).then(function () {
            location.reload();
        });
    };

    ListController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingding.report.template') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'dingding.report.template'\" class=\"btn btn-secondary\">" +
                    "获取日志模板</button>";
                let button2 = $(but).click(this.proxy('open_download_report_tmplate_action'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        open_download_report_tmplate_action: function () {
            new Dialog(this, {
                title: "获取日志模板",
                size: 'medium',
                buttons: [
                    {
                        text: "获取",
                        classes: 'btn-primary',
                        close: true,
                        click: save_data
                    }, {
                        text: "告辞",
                        close: true
                    }
                ],
                $content: $(QWeb.render('PullDingDingReportTemplate', {widget: this, data: []}))
            }).open();
        },

    });
});
