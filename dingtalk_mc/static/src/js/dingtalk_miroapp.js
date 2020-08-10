odoo.define('dingtalk.mc.dingtalk.miroapp.list.buttons', function (require) {
    "use strict";

    let viewRegistry = require('web.view_registry');
    let KanbanController = require('web.KanbanController');
    let KanbanView = require('web.KanbanView');

    let DingTalkMiroappeController = KanbanController.extend({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingtalk.miroapp.list') {
                let but = "<button type=\"button\" class=\"btn btn-secondary\">获取应用列表</button>";
                let button2 = $(but).click(this.proxy('getDingTalkMiroappList'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        getDingTalkMiroappList: function () {
            var self = this;
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'dingtalk.miroapp.list.wizard',
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

    let DingTalkMiroappeKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: DingTalkMiroappeController,
        }),
    });

    viewRegistry.add('dingtalk_miroapp_list_kanban_js_class', DingTalkMiroappeKanbanView);
});
