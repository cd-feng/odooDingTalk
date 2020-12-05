odoo.define('hcm.location.manage.tree.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');

    let HcmLocationManageListViewController = ListController.extend({
        buttons_template: 'odoo_hcm.user_location_tree_buttons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                let self = this;
                this.$buttons.on('click', '.get_user_location_tran', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'get.user.location.tran',
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

    let HcmLocationManageListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: HcmLocationManageListViewController,
        }),
    });

    viewRegistry.add('hcm_location_manage_class', HcmLocationManageListView);
});
