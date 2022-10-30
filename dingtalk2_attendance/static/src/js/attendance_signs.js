odoo.define('dingtalk2.attendance.signs.tree', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');

    let Dingtalk2AttendanceSignsListController = ListController.extend({
        buttons_template: 'ListView.Dingtalk2AttendanceSignsButtons',

        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                const self = this;
                this.$buttons.on('click', '.dingtalk2_get_attendance_signs', function () {
                    self.do_action({
                        name: "获取钉钉签到记录",
                        type: 'ir.actions.act_window',
                        res_model: 'dingtalk2.get.attendance.signs',
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

    let Dingtalk2AttendanceSignsListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: Dingtalk2AttendanceSignsListController,
        }),
    });
    viewRegistry.add('class_dingtalk2_attendance_signs', Dingtalk2AttendanceSignsListView);

});
