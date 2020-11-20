odoo.define('dingtalk.mc.employee.roster.buttons', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');
    let KanbanController = require('web.KanbanController');
    let KanbanView = require('web.KanbanView');

    let DingTalkMcEmployeeRosterController = ListController.extend({
        buttons_template: 'ListView.DingtalkMcHrmRosterListButtons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.get_dingtalk_mc_roster_class', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'dingtalk.employee.roster.synchronous',
                        target: 'new',
                        views: [[false, 'form']],
                        context: [],
                    },{
                        on_reverse_breadcrumb: function () {
                            self.reload();
                        },
                          on_close: function () {
                            self.reload();
                        }
                     });
                });
            }
        }
    });
    let DingTalkMcEmployeeRosterTreeListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingTalkMcEmployeeRosterController,
        }),
    });
    viewRegistry.add('dingtalk_employee_roster_tree', DingTalkMcEmployeeRosterTreeListView);

    let DingTalkMcEmployeeRosterKanbanController = KanbanController.extend({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingtalk.employee.roster') {
                let but = "<button type=\"button\" class=\"btn btn-secondary\">同步花名册</button>";
                let button2 = $(but).click(this.proxy('getDingTalkMcKanbanButton'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        getDingTalkMcKanbanButton: function () {
            var self = this;
            self.call('notification', 'notify', {
                title: "提示",
                message: "同步获取钉钉上的员工花名册...",
                sticky: false
            });
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'dingtalk.employee.roster.synchronous',
                target: 'new',
                views: [[false, 'form']],
                context: [],
            },{
                on_reverse_breadcrumb: function () {
                    self.reload();
                },
                on_close: function () {
                    self.reload();
                    self.call('notification', 'notify', {
                        title: "提示",
                        message: "刷新结果...",
                        sticky: false
                    });
                }
            });
        },
    });
    let DingTalkMcEmployeeRosterKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: DingTalkMcEmployeeRosterKanbanController,
        }),
    });
    viewRegistry.add('dingtalk_employee_roster_kanban', DingTalkMcEmployeeRosterKanbanView);
});
