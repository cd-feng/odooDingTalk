odoo.define('dindin.blackboard.info', function (require) {
    "use strict";

    let Dialog = require('web.Dialog');
    let core = require('web.core');
    let QWeb = core.qweb;
    let rpc = require('web.rpc');
    let AbstractAction = require('web.AbstractAction');



    let DinDinDashboard = AbstractAction.extend({
        template: 'DingDingDashboardMain',
        // events: {
        //     'click .my_feedback_bug': '_onFeedback_clicked',
        // },

        setBlackboardData: function (data) {
            let self = this;
            self.$el.find('#blackboard_list').html(QWeb.render("DindinDashboardInfoLine", {
                widget: self,
                data: data,
            }));
        },
        setBlackboardFalseData: function (data) {
            let self = this;
            self.$el.find('#blackboard_list').html(QWeb.render("DindinDashboardInfoLineFalse", {
                widget: self,
                data: data,
            }));
        },
        setBlackboardDataNull: function () {
            let self = this;
            self.$el.find('#blackboard_list').html(QWeb.render("DindinDashboardInfoLineNull", {
                widget: self,
                data: [],
            }));
        },
        setWorkRecordNumber: function (result) {
            this.$('.my-val1').html(result);
        },
        getUserApprovalNumber: function (result) {
            if (result.state) {
                this.$('.my-val3').html(result.number);
            } else {
                this.$('.my-val3').html(result.msg);
            }
        },

        start: function () {
            let self = this;
            //获取我的待办
            rpc.query({
                model: 'dindin.work.record',
                method: 'get_record_number',
                args: [],
            }).then(function (result) {
                self.setWorkRecordNumber(result);
            });
            //获取待审批数
            rpc.query({
                model: 'dindin.approval.template',
                method: 'get_get_template_number_by_user',
                args: [],
            }).then(function (result) {
                self.getUserApprovalNumber(result);
            });
            // 获取公告
            rpc.query({
                model: 'dindin.blackboard',
                method: 'get_blackboard_by_user',
                args: [],
            }).then(function (result) {
                if (result.state) {
                    if (result.data.length == 0) {
                        self.setBlackboardDataNull();
                    } else {
                        self.setBlackboardData(result.data);
                        self.$('.my-val2').html(result.number);
                    }
                } else {
                    self.setBlackboardFalseData(result);
                }
            });
        },

        // _onFeedback_clicked: function (ev) {
        //     let self = this;
        //     self.do_action({
        //         type: 'ir.actions.act_window',
        //         res_model: 'dingding.user.feedback',
        //         // target: 'new',
        //         views: [[false, 'list']],
        //         // context: [],
        //     });
        // },

    });

    core.action_registry.add('dindin_dashboard', DinDinDashboard);
    return DinDinDashboard;
});