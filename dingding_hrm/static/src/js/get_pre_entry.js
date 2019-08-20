odoo.define('dingding_hrm.get.dingding.pre.entry.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let Dialog = require('web.Dialog');
    let core = require('web.core');
    let QWeb = core.qweb;
    let rpc = require('web.rpc');
    let viewRegistry = require('web.view_registry');
    let KanbanController = require('web.KanbanController');
    let KanbanView = require('web.KanbanView');

    let save_data = function () {
        this.do_notify("请稍后...", "查询完成后需要刷新界面方可查看！!");
        getTemplate();
    };

    let getTemplate = function () {
        let def = rpc.query({
            model: 'dingding.add.employee',
            method: 'count_pre_entry',
            args: [],
        }).then(function () {
            console.log("查询成功");
            location.reload();
        });
    };

    ListController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingding.add.employee') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'dingding.add.employee'\" class=\"btn btn-secondary o_get_dingding_pre_entry\">拉取待入职人员</button>";
                let button2 = $(but).click(this.proxy('open_action'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        open_action: function () {
            new Dialog(this, {
                title: "拉取待入职人员",
                size: 'medium',
                buttons: [
                    {
                        text: "开始拉取",
                        classes: 'btn-primary',
                        close: true,
                        click: save_data
                    }, {
                        text: "取消",
                        close: true
                    }
                ],
                $content: $(QWeb.render('GetDingDingPreEntry', {widget: this, data: []}))
            }).open();
        },

    });

    let GetDingDingPreEntryKanbanController = KanbanController.extend({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingding.add.employee') {
                let but = "<button type=\"button\" class=\"btn btn-secondary\">拉取待入职人员</button>";
                let button2 = $(but).click(this.proxy('GetDingDingPreEntryKanbanButton'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        GetDingDingPreEntryKanbanButton: function () {
            new Dialog(this, {
                title: "拉取待入职人员",
                size: 'medium',
                buttons: [
                    {
                        text: "拉取",
                        classes: 'btn-primary',
                        close: true,
                        click: save_data
                    }, {
                        text: "取消",
                        close: true
                    }
                ],
                $content: $(QWeb.render('GetDingDingPreEntry', {widget: this, data: []}))
            }).open();
        },
    });

    let GetDingDingPreEntryKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: GetDingDingPreEntryKanbanController,
        }),
    });

    viewRegistry.add('dindin_get_preentry_kanban', GetDingDingPreEntryKanbanView);
});
