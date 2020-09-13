odoo.define('dingtalk.mc.callback.manage.buttons', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');

    let DingTalkCallBackManageController = ListController.extend({
        buttons_template: 'ListView.DingtalkMcCallbackListButtons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.get_dingtalk_callback_class', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'get.dingtalk.callback',
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
                });
            }
        }
    });

    let DingTalkCallBackManageTreeListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingTalkCallBackManageController,
        }),
    });

    viewRegistry.add('dingtalk_callback_manage_tree', DingTalkCallBackManageTreeListView);

});
