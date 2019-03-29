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

    let get_sim_emps_data = function () {
        let def = rpc.query({
            model: 'dindin.simple.groups',
            method: 'get_sim_emps',
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
                let but3 = "<button type=\"button\" t-if=\"widget.modelName == 'dindin.simple.groups'\" class=\"btn btn-secondary\">获取考勤组成员</button>";
                let button3 = $(but3).click(this.proxy('get_simple_emps_action'));
                this.$buttons.append(button3);
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
        get_simple_emps_action: function () {
            new Dialog(this, {
                title: "获取考勤组成员",
                size: 'medium',
                buttons: [
                    {
                        text: "确定",
                        classes: 'btn-primary',
                        close: true,
                        click: get_sim_emps_data
                    }, {
                        text: "取消",
                        close: true
                    }
                ],
                $content: $(QWeb.render('GetDinDinSimpleGroupsEmps', {widget: this, data: []}))
            }).open();
        },


    });
});
