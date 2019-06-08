odoo.define('dingding.chat.list.tree', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');
    let KanbanController = require('web.KanbanController');
    let KanbanView = require('web.KanbanView');

    let DingDingChatListController = ListController.extend({
        buttons_template: 'DingDingChatListView.dingding_chat_buttons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.o_button_get_dingding_chat_list', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'get.dingding.chat.list',
                        target: 'new',
                        views: [[false, 'form']],
                        context: [],
                    });
                });
            }
        }
    });

    let GetDingDingChatListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingDingChatListController,
        }),
    });


    let DingDingChatKanbanController = KanbanController.extend({
        renderButtons: function ($node) {
            // return DingDingChatKanbanButtons.apply(this, arguments);
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'dingding.chat') {
                let but = "<button type=\"button\" class=\"btn btn-secondary\">获取群会话</button>";
                let button2 = $(but).click(this.proxy('getDingDingChatKanbanButton'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        getDingDingChatKanbanButton: function () {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'get.dingding.chat.list',
                target: 'new',
                views: [[false, 'form']],
                context: [],
            });
        },
    });

    let GetDingDingChatKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: DingDingChatKanbanController,
        }),
    });

    viewRegistry.add('dingding_chat_list_tree', GetDingDingChatListView);
    viewRegistry.add('dingding_chat_list_kanban', GetDingDingChatKanbanView);
});
