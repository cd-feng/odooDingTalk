odoo.define('dingtalk.add.employee.buttons', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');
    let KanbanController = require('web.KanbanController');
    let KanbanView = require('web.KanbanView');

    let DingTalkAddEmployeeListController = ListController.extend({
        buttons_template: 'ListView.DingTalkAddEmployeeListButtons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.get_dingtalk_query_preen_try_class', function () {
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

    let DingTalkAddEmployeeListTreeListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingTalkAddEmployeeListController,
        }),
    });

    let DingTalkAddEmployeeListKanbanController = KanbanController.extend({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingtalk.add.employee') {
                let but = "<button type=\"button\" class=\"btn btn-secondary\">查询待入职员工</button>";
                let button2 = $(but).click(this.proxy('getDingTalkAddEmpKanbanButton'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        getDingTalkAddEmpKanbanButton: function () {
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

    let DingTalkAddEmployeeListKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: DingTalkAddEmployeeListKanbanController,
        }),
    });

    viewRegistry.add('get_query_preen_try_class', DingTalkAddEmployeeListTreeListView);
    viewRegistry.add('get_query_preen_try_kanban_class', DingTalkAddEmployeeListKanbanView);
});
