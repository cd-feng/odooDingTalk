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

odoo.define('odoo.wage.insured.monthly.statement.tree.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');

    let OdooWageManageListViewController = ListController.extend({
        buttons_template: 'OdooWageManageListView.wage_insured_monthly_statement_buttons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                let self = this;
                this.$buttons.on('click', '.wage_insured_monthly_statement_but_class', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'compute.wage.insured.monthly.statement',
                        target: 'new',
                        views: [[false, 'form']],
                        context: [],
                    });
                });
            }
        }
    });

    let OdooWageManageListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: OdooWageManageListViewController,
        }),
    });

    viewRegistry.add('compute_wage_insured_monthly_statement', OdooWageManageListView);
});
