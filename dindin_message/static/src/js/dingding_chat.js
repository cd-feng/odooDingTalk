odoo.define('dingding.chat.list.tree', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');

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

    viewRegistry.add('dingding_chat_list_tree', GetDingDingChatListView);
});
