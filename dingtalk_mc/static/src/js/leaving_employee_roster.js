odoo.define('dingtalk.leaving.employee.roster.buttons', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');
    let KanbanController = require('web.KanbanController');
    let KanbanView = require('web.KanbanView');

    function renderHrmLeavingButton() {
        if (this.$buttons) {
            let self = this;
            this.$buttons.on('click', '.synchronize_leaving_employees', function () {
                self.do_action({
                    name: '同步离职员工信息',
                    type: 'ir.actions.act_window',
                    res_model: 'dingtalk.synchronize.leaving.employees',
                    target: 'new',
                    views: [[false, 'form']],
                    context: [],
                }, {
                    on_close: function () {
                        self.reload();
                    }
                });
            });
            this.$buttons.on('click', '.synchronize_leaving_to_employee', function () {
                self._rpc({
                    model: 'dingtalk.leaving.employee.roster',
                    method: 'sync_to_employees',
                    args: [],
                    context: self.odoo_context,
                }).then(function(result){
                    self.reload();
                })
            });
        }
    }

    var DingtalkMcLeavingEmployeesListController = ListController.extend({
        willStart: function() {
            var self = this;
            var ready = this.getSession().user_has_group('dingtalk_mc.dingtalk_mc_roster_group')
                .then(function (result) {
                    if (result) {
                        self.buttons_template = 'DingtalkMcLeavingEmployeesListView.buttons';
                    }
                });
            return Promise.all([this._super.apply(this, arguments), ready]);
        },
        renderButtons: function () {
            this._super.apply(this, arguments);
            renderHrmLeavingButton.apply(this, arguments);
        }
    });

    var DingtalkMcLeavingEmployeesListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingtalkMcLeavingEmployeesListController,
        }),
    });


    viewRegistry.add('dingtalk_leaving_employee_roster_tree', DingtalkMcLeavingEmployeesListView);


})