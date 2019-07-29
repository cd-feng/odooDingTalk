odoo.define('dingding.employee.roster.tree.button', function (require) {
    "use strict";

    let core = require('web.core');
    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');
    let qweb = core.qweb;

    let DingDingEmployeeRosterController = ListController.extend({
        buttons_template: 'HrmListView.hrm_buttons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.o_button_get_dingding_employee_roster_list', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'dingding.get.hrm.list',
                        target: 'new',
                        views: [[false, 'form']],
                        context: [],
                    });
                });
            }
        }
    });

    let GetDingDingEmployeeRosterView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingDingEmployeeRosterController,
        }),
    });

    viewRegistry.add('dingding_employee_roster_tree', GetDingDingEmployeeRosterView);
});
