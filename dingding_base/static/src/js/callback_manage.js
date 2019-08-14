odoo.define('dingding.callback.manage.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let Dialog = require('web.Dialog');
    let core = require('web.core');
    let QWeb = core.qweb;
    let rpc = require('web.rpc');

    let save_data = function () {
        rpc.query({
            model: 'dingding.callback.manage',
            method: 'get_all_call_back',
            args: [],
        }).then(function (result) {
            if (result.state) {
                location.reload();
            } else {
                new Dialog.confirm(this, result.msg, {
                    'title': '结果提示',
                });
            }
        });
    };

    ListController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingding.callback.manage') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'dingding.callback.manage'\" class=\"btn btn-primary\">获取回调列表</button>";
                let button2 = $(but).click(this.proxy('pull_dingding_callback_manage'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        pull_dingding_callback_manage: function () {
            new Dialog(this, {
                title: "拉取回调列表",
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
                $content: $(QWeb.render('PullDinDinUserCallback', {widget: this, data: []}))
            }).open();
        },
    });
});
