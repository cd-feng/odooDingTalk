odoo.define('hr.attendance.result.tree.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');

    let DingDingAttendanceRecordController = ListController.extend({
        buttons_template: 'ListView.UserAttendanceResultButtons',
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
    viewRegistry.add('dingtalk_attendance_result_class', GetDingDingAttendanceRecordView);




    let DingtalkMonthAttendanceController = ListController.extend({
        buttons_template: 'ListView.HrMonthAttendanceButtons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.dingtalk_month_attendance_tree', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'calculate.month.attendance',
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
                this.$buttons.on('click', '.dingtalk_duration_tree', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'dingtalk.users.duration',
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
    let DingtalkMonthAttendanceView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingtalkMonthAttendanceController,
        }),
    });
    viewRegistry.add('calculate_month_attendance_class', DingtalkMonthAttendanceView);

});
