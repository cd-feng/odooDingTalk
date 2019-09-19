/**
 *    Copyright (C) 2019 SuXueFeng
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or (at your option) any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 **/

odoo.define('dingding_base.pull.dindin.approval.button', function (require) {
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
            model: 'dingding.approval.template',
            method: 'get_template',
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
            if (tree_model == 'dingding.approval.template') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'dingding.approval.template'\" class=\"btn btn-secondary o_pull_dindin_approval_template\">拉取审批模板</button>";
                let button2 = $(but).click(this.proxy('open_action'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        open_action: function () {
            new Dialog(this, {
                title: "拉取审批模板",
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
                $content: $(QWeb.render('PullDinDinApprovalTemplate', {widget: this, data: []}))
            }).open();
        },

    });

    let DingDingApprovalTemplateKanbanController = KanbanController.extend({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingding.approval.template') {
                let but = "<button type=\"button\" class=\"btn btn-secondary\">拉取审批模板</button>";
                let button2 = $(but).click(this.proxy('getDingApprovalTemplateKanbanButton'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        getDingApprovalTemplateKanbanButton: function () {
            new Dialog(this, {
                title: "拉取审批模板",
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
                $content: $(QWeb.render('PullDinDinApprovalTemplate', {widget: this, data: []}))
            }).open();
        },
    });

    let GetDingDingApprovalTemplateKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: DingDingApprovalTemplateKanbanController,
        }),
    });

    viewRegistry.add('dingding_approval_template_kanban', GetDingDingApprovalTemplateKanbanView);
});
