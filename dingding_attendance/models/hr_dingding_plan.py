# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import models, fields, api


class HrDingdingPlan(models.Model):
    _name = "hr.dingding.plan"
    _rec_name = 'user_id'
    _description = "排班列表"

    plan_id = fields.Char(string='排班id')
    check_type = fields.Selection(string=u'打卡类型', selection=[('OnDuty', '上班打卡'), ('OffDuty', '下班打卡')])
    approve_id = fields.Char(string='审批id', help="没有的话表示没有审批单")
    user_id = fields.Many2one(comodel_name='hr.employee', string=u'员工')
    class_id = fields.Char(string='考勤班次id')
    class_setting_id = fields.Char(string='班次配置id', help="没有的话表示使用全局班次配置")
    plan_check_time = fields.Date(string=u'打卡时间')
    group_id = fields.Many2one(comodel_name='dingding.simple.groups', string=u'考勤组')


class HrDingdingPlanTran(models.TransientModel):
    _name = "hr.dingding.plan.tran"
    _description = "排班列表查询"

    work_date = fields.Date(string=u'排期日期')

    @api.multi
    def get_plan_lists(self):
        """
        获取企业考勤排班详情
        :return:
        """
        self.ensure_one()
        self.start_pull_plan_lists(str(self.work_date))
        action = self.env.ref('dingding_attendance.hr_dingding_plan_action')
        action_dict = action.read()[0]
        return action_dict

    @api.model
    def start_pull_plan_lists(self, work_date):
        """
        拉取排班信息
        :param work_date: string 查询的日期
        :return:
        """
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('attendance_listschedule')
        offset = 0
        size = 200
        while True:
            data = {'offset': offset, 'size': size, 'workDate': work_date}
            result = self.env['dingding.api.tools'].send_post_request(url, token, data)
            if result.get('errcode') == 0:
                res_result = result['result']
                for schedules in res_result['schedules']:
                    plan_data = {
                        'class_setting_id': schedules['class_setting_id'] if 'class_setting_id' in schedules else "",
                        'check_type': schedules['check_type'] if 'check_type' in schedules else "",
                        'plan_id': schedules['plan_id'] if 'plan_id' in schedules else "",
                        'class_id': schedules['class_id'] if 'class_id' in schedules else "",
                        'plan_check_time': schedules['plan_check_time'] if 'plan_check_time' in schedules else False,
                    }
                    simple = self.env['dingding.simple.groups'].search([('group_id', '=', schedules['group_id'])], limit=1)
                    employee = self.env['hr.employee'].search([('ding_id', '=', schedules['userid'])], limit=1)
                    plan_data.update({
                        'group_id': simple.id if simple else False,
                        'user_id': employee.id if employee else False,
                    })
                    plan = self.env['hr.dingding.plan'].search([('plan_id', '=', schedules['plan_id'])])
                    if not plan:
                        self.env['hr.dingding.plan'].create(plan_data)
                    else:
                        plan.write(plan_data)
                if not res_result['has_more']:
                    break
                else:
                    offset += 1
            else:
                raise UserError("获取企业考勤排班详情失败: {}".format(result['errmsg']))
        return True
