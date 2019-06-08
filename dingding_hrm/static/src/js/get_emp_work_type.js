odoo.define('dingding.hrm.get.employees.work.type.tree', function (require) {
    "use strict";

    let core = require('web.core');
    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');

    let DingDingHrmWorkTypeListController = ListController.extend({
        buttons_template: 'HrmListView.get_emp_work_type_buttons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.o_button_get_emp_work_type_button', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'get.hrm.employee.state',
                        target: 'new',
                        views: [[false, 'form']],
                        context: [],
                    });
                });
            }
        }
    });

    let GetDingDingHrmWorkTypeListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingDingHrmWorkTypeListController,
        }),
    });

    viewRegistry.add('get_dingding_emp_work_type', GetDingDingHrmWorkTypeListView);
});
