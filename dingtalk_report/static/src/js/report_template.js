odoo.define('dingtalk.report.template.buttons', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');
    let KanbanController = require('web.KanbanController');
    let KanbanView = require('web.KanbanView');

    let DingtalkReportTemplateController = ListController.extend({
        buttons_template: 'ListView.DingtalkReportTemplateButtons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.get_dingtalk_report_template_class', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'dingtalk.report.template.tran',
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

    let DingtalkReportTemplateTreeListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingtalkReportTemplateController,
        }),
    });

    viewRegistry.add('dingtalk_report_template_tree_class', DingtalkReportTemplateTreeListView);


    let DingtalkReportTemplateKanbanController = KanbanController.extend({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingtalk.report.template') {
                let but = "<button type=\"button\" class=\"btn btn-secondary\">拉取钉钉日志模板</button>";
                let button2 = $(but).click(this.proxy('getDingTalkReportTemBut'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        getDingTalkReportTemBut: function () {
            var self = this;
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'dingtalk.report.template.tran',
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

    let DingtalkReportTemplateKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: DingtalkReportTemplateKanbanController,
        }),
    });

    viewRegistry.add('dingtalk_report_template_kanban_class', DingtalkReportTemplateKanbanView);
});
