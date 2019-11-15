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

odoo.define('hr.attendance.result.tree.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');
    let KanbanController = require('web.KanbanController');
    let KanbanView = require('web.KanbanView');

    let DingDingAttendanceRecordController = ListController.extend({
        buttons_template: 'ListView.GetUserAttendanceResultButtons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.dingtalk_user_attendance_result_tree', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'hr.attendance.tran',
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

    let GetDingDingAttendanceRecordView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingDingAttendanceRecordController,
        }),
    });

    viewRegistry.add('dingtalk_hr_attendance_result_tree', GetDingDingAttendanceRecordView);



     let AttendanceResultKanbanController = KanbanController.extend({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'hr.attendance.result') {
                let but = "<button type=\"button\" class=\"btn btn-secondary\">获取打卡结果</button>";
                let button2 = $(but).click(this.proxy('getAttendanceResultTran'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        getAttendanceResultTran: function () {
            var self = this;
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'hr.attendance.tran',
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

    let AttendanceResultKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: AttendanceResultKanbanController,
        }),
    });

    viewRegistry.add('dingtalk_hr_attendance_result_kanban', AttendanceResultKanbanView);

});
