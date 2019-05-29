odoo.define('dingding.get.user.report.list', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');

    let DingDingGetUserReportController = ListController.extend({
        buttons_template: 'DingDingReportView.get_user_dingding_report_buttons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.o_button_get_user_dingding_report_list', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'get.dingding.user.report.list',
                        target: 'new',
                        views: [[false, 'form']],
                        context: [],
                    });
                });
            }
        }
    });

    let GetDingDingReportListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingDingGetUserReportController,
        }),
    });

    viewRegistry.add('dingding_get_user_report', GetDingDingReportListView);
});
