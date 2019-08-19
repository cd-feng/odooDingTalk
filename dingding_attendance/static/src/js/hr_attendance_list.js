odoo.define('dingding_attendance.attendance.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');


    ListController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'hr.attendance') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'hr.attendance'\" class=\"btn btn-primary o_pull_dingtalk_simple_groups\">获取钉钉考勤信息</button>";
                let button2 = $(but).click(this.proxy('open_attendance_list_action_v2'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        open_attendance_list_action_v2: function () {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'hr.attendance.tran.v2',
                target: 'new',
                views: [[false, 'form']],
                context: [],
            });
        },
    });
});
