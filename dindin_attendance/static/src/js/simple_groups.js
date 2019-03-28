odoo.define('dindin.simple.groups.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let Dialog = require('web.Dialog');
    let core = require('web.core');
    let QWeb = core.qweb;
    let rpc = require('web.rpc');

    let save_data = function () {
        this.do_notify("请稍后...", "正在查询！!");
        getSimpleGroups();
    };

    let getSimpleGroups = function () {
        let def = rpc.query({
            model: 'dindin.simple.groups',
            method: 'get_simple_groups',
            args: [],
        }).then(function (result) {
            if (result) {
                location.reload();
            }
        });
    };

    ListController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dindin.simple.groups') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'dindin.simple.groups'\" class=\"btn btn-primary o_pull_dindin_simple_groups\">拉取考勤组</button>";
                let button2 = $(but).click(this.proxy('open_simple_action'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        open_simple_action: function () {
            new Dialog(this, {
                title: "拉取考勤",
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
                $content: $(QWeb.render('PullDinDinSimpleGroups', {widget: this, data: []}))
            }).open();
        },

    });
});
