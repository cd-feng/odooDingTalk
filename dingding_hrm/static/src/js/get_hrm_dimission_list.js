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

odoo.define('dingding.hrm.dimission.list.tree', function (require) {
    "use strict";

    let core = require('web.core');
    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');
    let qweb = core.qweb;

    let DingDingHrmDimissionListController = ListController.extend({
        buttons_template: 'HrmListView.hrm_dimission_buttons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.o_button_get_dingding_hrm_dimission_list', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'dingding.get.hrm.dimission.list',
                        target: 'new',
                        views: [[false, 'form']],
                        context: [],
                    });
                });
            }
        }
    });

    let GetDingDingHrmDimissionListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingDingHrmDimissionListController,
        }),
    });

    viewRegistry.add('dingding_hrm_dimission_list_tree', GetDingDingHrmDimissionListView);
});
