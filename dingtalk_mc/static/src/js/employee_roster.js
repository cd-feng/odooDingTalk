odoo.define('dingtalk.mc.employee.roster.buttons', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');
    let KanbanController = require('web.KanbanController');
    let KanbanView = require('web.KanbanView');

    function renderHrmRosterButton() {
        if (this.$buttons) {
            let self = this;
            this.$buttons.on('click', '.synchronize_insured_scheme_employee', function () {
                self.do_action({
                    name: '同步花名册',
                    type: 'ir.actions.act_window',
                    res_model: 'dingtalk.employee.roster.synchronous',
                    target: 'new',
                    views: [[false, 'form']],
                    context: [],
                }, {
                    on_close: function () {
                        self.reload();
                    }
                });
            });
            this.$buttons.on('click', '.synchronize_hrm_to_employee', function () {
                self._rpc({
                    model: 'dingtalk.employee.roster.synchronous',
                    method: 'sync_to_employees',
                    args: [],
                    context: self.odoo_context,
                }).then(function(result){
                    self.reload();
                })
            });
        }
    }

    var DingTalkMcEmployeeRosterController = ListController.extend({
        willStart: function() {
            var self = this;
            var ready = this.getSession().user_has_group('dingtalk_mc.dingtalk_mc_roster_group')
                .then(function (is_sale_manager) {
                    if (is_sale_manager) {
                        self.buttons_template = 'ListView.DingtalkMcHrmRosterListButtons';
                    }
                });
            return Promise.all([this._super.apply(this, arguments), ready]);
        },
        renderButtons: function () {
            this._super.apply(this, arguments);
            renderHrmRosterButton.apply(this, arguments);
        }
    });

    var DingTalkMcEmployeeRosterTreeListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingTalkMcEmployeeRosterController,
        }),
    });

    let DingTalkMcEmployeeRosterKanbanController = KanbanController.extend({
        willStart: function () {
            let self = this;
            let ready = this.getSession().user_has_group('dingtalk_mc.dingtalk_mc_roster_group')
                .then(function (is_sale_manager) {
                    if (is_sale_manager) {
                        self.buttons_template = 'DingtalkMcHrmRosterKanbanView.buttons';
                    }
                });
            return Promise.all([this._super.apply(this, arguments), ready]);
        },
        renderButtons: function () {
            this._super.apply(this, arguments);
            renderHrmRosterButton.apply(this, arguments);
        }
    })

    let DingTalkMcEmployeeRosterKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: DingTalkMcEmployeeRosterKanbanController,
        }),
    });

    viewRegistry.add('dingtalk_employee_roster_tree', DingTalkMcEmployeeRosterTreeListView);
    viewRegistry.add('dingtalk_employee_roster_kanban', DingTalkMcEmployeeRosterKanbanView);
});
