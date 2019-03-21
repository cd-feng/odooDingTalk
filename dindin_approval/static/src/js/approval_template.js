odoo.define('dindin_approval.pull_dindin_approval_button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let Dialog = require('web.Dialog');
    let core = require('web.core');
    let QWeb = core.qweb;

    let save_data = function () {
             alert("ok");
    };
    let searchBankCardInfo = function(){
        let self = this;
            var def = rpc.query({
                model: 'union.pay.search.bank.card.info',
                method: 'search_bank_card_info',
                args: [cardNo],
            }).then(function (data) {
                // Result
                console.log(data);
                self.do_notify(_t("查询成功.")), _t("查询成功...");
                self.setSearchResult(data)
            });
    };

    ListController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dindin.approval.template') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'dindin.approval.template'\" class=\"btn btn-secondary o_pull_dindin_approval_template\">" +
                    "拉取审批模板</button>";
                let button2 = $(but).click(this.proxy('open_action'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        open_action: function () {
            new Dialog(this, {
                title: "开始拉取审批模板",
                size: 'medium',
                buttons: [
                    {
                        text: "确定",
                        classes: 'btn-primary',
                        close: true,
                        click: save_data
                    }, {
                        text: "取消",
                        close: true
                    }
                ],
                $content: $(QWeb.render('PullDinDinApprovalTemplate', {widget: this, data: []}))
            }).open();
        },

    });
});
