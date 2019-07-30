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

odoo.define('ding.hr.leaves.list.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');

    ListController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'hr.leaves.list') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'hr.leaves.list'\" class=\"btn btn-primary\" groups=\"dingding_base.manage_groups\">查询请假状态</button>";
                let button2 = $(but).click(this.proxy('open_hr_leaves_list_tran_action'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        open_hr_leaves_list_tran_action: function () {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'hr.leaves.list.tran',
                target: 'new',
                views: [[false, 'form']],
                context: [],
            });
        },
    });
});
