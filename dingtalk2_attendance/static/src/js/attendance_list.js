odoo.define('dingtalk2.attendance.list.tree', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');

    let Dingtalk2AttendanceListController = ListController.extend({
        buttons_template: 'ListView.Dingtalk2AttendanceListButtons',

        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                const self = this;
                this.$buttons.on('click', '.dingtalk2_get_attendance_list', function () {
                    self.do_action({
                        name: "获取钉钉打卡结果",
                        type: 'ir.actions.act_window',
                        res_model: 'dingtalk2.get.attendance.list',
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

    let Dingtalk2AttendanceListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: Dingtalk2AttendanceListController,
        }),
    });
    viewRegistry.add('class_dingtalk2_attendance_list', Dingtalk2AttendanceListView);


    // let DingtalkMonthAttendanceController = ListController.extend({
    //     buttons_template: 'ListView.HrMonthAttendanceButtons',
    //     renderButtons: function () {
    //         this._super.apply(this, arguments);
    //         if (this.$buttons) {
    //             var self = this;
    //             this.$buttons.on('click', '.dingtalk_month_attendance_tree', function () {
    //                 self.do_action({
    //                     name: "计算考勤",
    //                     type: 'ir.actions.act_window',
    //                     res_model: 'calculate.month.attendance',
    //                     target: 'new',
    //                     views: [[false, 'form']],
    //                     context: [],
    //                 },{
    //                     on_reverse_breadcrumb: function () {
    //                         self.reload();
    //                     },
    //                       on_close: function () {
    //                         self.reload();
    //                     }
    //                  });
    //             });
    //             this.$buttons.on('click', '.dingtalk_duration_tree', function () {
    //                 self.do_action({
    //                     name: "计算预计算时长",
    //                     type: 'ir.actions.act_window',
    //                     res_model: 'dingtalk.users.duration',
    //                     target: 'new',
    //                     views: [[false, 'form']],
    //                     context: [],
    //                 },{
    //                     on_reverse_breadcrumb: function () {
    //                         self.reload();
    //                     },
    //                       on_close: function () {
    //                         self.reload();
    //                     }
    //                  });
    //             });
    //         }
    //     }
    // });
    // let DingtalkMonthAttendanceView = ListView.extend({
    //     config: _.extend({}, ListView.prototype.config, {
    //         Controller: DingtalkMonthAttendanceController,
    //     }),
    // });
    // viewRegistry.add('calculate_month_attendance_class', DingtalkMonthAttendanceView);

});
