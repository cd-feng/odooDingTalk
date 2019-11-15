odoo.define('dingtalk.employee.roster.buttons', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');
    let KanbanController = require('web.KanbanController');
    let KanbanView = require('web.KanbanView');

    let DingTalkEmployeeRosterController = ListController.extend({
        buttons_template: 'ListView.DingtalkHrmRosterListButtons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.get_dingtalk_hrm_roster_class', function () {
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

    let DingTalkEmployeeRosterTreeListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingTalkEmployeeRosterController,
        }),
    });

    let DingTalkEmployeeRosterKanbanController = KanbanController.extend({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingtalk.employee.roster') {
                let but = "<button type=\"button\" class=\"btn btn-secondary\">获取员工花名册</button>";
                let button2 = $(but).click(this.proxy('getDingTalkChatKanbanButton'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        getDingTalkChatKanbanButton: function () {
            var self = this;
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
                }
            });
        },
    });

    let DingTalkEmployeeRosterKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: DingTalkEmployeeRosterKanbanController,
        }),
    });

    viewRegistry.add('dingtalk_get_hrm_tree_list', DingTalkEmployeeRosterTreeListView);
    viewRegistry.add('dingtalk_get_hrm_kanban_list', DingTalkEmployeeRosterKanbanView);
});
