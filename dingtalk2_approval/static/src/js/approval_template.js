odoo.define('dingtalk.approval.template.buttons', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');

    function renderDingTalkApprovalTemplateButton() {
        if (this.$buttons) {
            let self = this;
            this.$buttons.on('click', '.get_dingtalk_approval_template_class', function () {
                self.do_action({
                    name: '拉取钉钉审批模板',
                    type: 'ir.actions.act_window',
                    res_model: 'dingtalk.approval.template.tran',
                    target: 'new',
                    views: [[false, 'form']],
                    context: [],
                }, {
                    on_close: function () {
                        self.reload();
                    }
                });
            });
        }
    }

    let DingTalkApprovalTemplateListController = ListController.extend({
        buttons_template: 'ListView.DingTalkApprovalTemplateButtons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            renderDingTalkApprovalTemplateButton.apply(this, arguments);
        }
    });

    let DingTalkApprovalTemplateListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingTalkApprovalTemplateListController,
        }),
    });

    viewRegistry.add('dingtalk_approval_template_tree', DingTalkApprovalTemplateListView);

});
