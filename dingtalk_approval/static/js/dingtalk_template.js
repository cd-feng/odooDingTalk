odoo.define('dingtalk.approval.template.buttons', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');
    let KanbanController = require('web.KanbanController');
    let KanbanView = require('web.KanbanView');

    let DingTalkApprovalTemplateController = ListController.extend({
        buttons_template: 'ListView.DingTalkDingTalkApprovalTemButtons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.get_dingtalk_approval_template_class', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'dingtalk.approval.template.tran',
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

    let DingTalkApprovalTemplateTreeListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingTalkApprovalTemplateController,
        }),
    });

    viewRegistry.add('dingtalk_approval_tem_tree_class', DingTalkApprovalTemplateTreeListView);



    let DingTalkApprovalTemplateKanbanController = KanbanController.extend({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingtalk.approval.template') {
                let but = "<button type=\"button\" class=\"btn btn-secondary\">获取审批模板</button>";
                let button2 = $(but).click(this.proxy('getDingTalkApprovalTemBut'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        getDingTalkApprovalTemBut: function () {
            var self = this;
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'dingtalk.approval.template.tran',
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

    let DingTalkApprovalTemplateKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: DingTalkApprovalTemplateKanbanController,
        }),
    });

    viewRegistry.add('dingtalk_approval_tem_kanban_class', DingTalkApprovalTemplateKanbanView);
});
