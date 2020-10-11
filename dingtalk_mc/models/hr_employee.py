# -*- coding: utf-8 -*-
import base64
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.addons.dingtalk_mc.tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    OfficeStatus = [
        ('2', '试用期'), ('3', '正式'), ('5', '待离职'), ('-1', '无状态')
    ]

    ding_id = fields.Char(string='钉钉Id', index=True)
    din_unionid = fields.Char(string='Union标识', index=True)
    din_jobnumber = fields.Char(string='员工工号')
    ding_avatar = fields.Html('钉钉头像', compute='_compute_ding_avatar')
    ding_avatar_url = fields.Char('头像url')
    din_hiredDate = fields.Date(string='入职时间')
    din_isAdmin = fields.Boolean("是管理员", default=False)
    din_isBoss = fields.Boolean("是老板", default=False)
    din_isLeader = fields.Boolean("是部门主管", default=False)
    din_isHide = fields.Boolean("隐藏手机号", default=False)
    din_isSenior = fields.Boolean("高管模式", default=False)
    din_active = fields.Boolean("是否激活", default=True)
    din_orderInDepts = fields.Char("所在部门序位")
    din_isLeaderInDepts = fields.Char("是否为部门主管")
    work_status = fields.Selection(string=u'入职状态', selection=[('1', '待入职'), ('2', '在职'), ('3', '离职')], default='2')
    office_status = fields.Selection(string=u'在职子状态', selection=OfficeStatus, default='-1')
    department_ids = fields.Many2many('hr.department', 'emp_dept_dingtalk_rel', string='所属部门')

    @api.depends('ding_avatar_url')
    def _compute_ding_avatar(self):
        for res in self:
            if res.ding_avatar_url:
                res.ding_avatar = """
                <img src="{avatar_url}" style="width:80px; height=80px;">""".format(avatar_url=res.ding_avatar_url)
            else:
                res.ding_avatar = False

    @api.constrains('user_id')
    def _constrains_dingtalk_oauth(self):
        """
        当修改关联用户时，将员工的钉钉ID写入到系统用户中
        :return:
        """
        if self.user_id and self.ding_id:
            # 把员工的钉钉id和手机号写入到系统用户oauth
            users = self.env['res.users'].with_user(SUPERUSER_ID).search([('ding_user_id', '=', self.ding_id), ('company_id', '=', self.company_id.id)])
            if users:
                users.with_user(SUPERUSER_ID).write({'ding_user_id': False, 'ding_user_phone': False})
            self.user_id.with_user(SUPERUSER_ID).write({
                'ding_user_id': self.ding_id,
                'ding_user_phone': self.mobile_phone,
            })

    def create_ding_employee(self):
        """
        上传员工到钉钉
        :return:
        """
        for res in self:
            self._check_user_identity(res)
            client = dt.get_client(self, dt.get_dingtalk_config(self, res.company_id))
            # 获取部门ding_id
            department_list = list()
            if not res.department_id:
                raise UserError("请选择员工部门!")
            elif res.department_ids:
                department_list = res.department_ids.mapped('ding_id')
                department_list.append(res.department_id.ding_id)
            else:
                department_list.append(res.department_id.ding_id)
            data = {
                'name': res.name,  # 名称
                'department': department_list,  # 部门
                'position': res.job_title if res.job_title else '',  # 职位
                'mobile': res.mobile_phone if res.mobile_phone else res.work_phone,  # 手机
                'tel': res.work_phone if res.work_phone else res.mobile_phone,  # 手机
                'workPlace': res.work_location if res.work_location else '',  # 办公地址
                'remark': res.notes if res.notes else '',  # 备注
                'email': res.work_email if res.work_email else '',  # 邮箱
                'jobnumber': res.din_jobnumber if res.din_jobnumber else '',  # 工号
                'hiredDate': dt.datetime_to_stamp(res.din_hiredDate) if res.din_hiredDate else '',  # 入职日期
            }
            try:
                result = client.user.create(data)
                res.write({'ding_id': result})
                res.message_post(body=u"已上传至钉钉", message_type='notification')
            except Exception as e:
                raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    def update_ding_employee(self):
        """
        修改员工时同步至钉钉
        :return:
        """
        for res in self:
            self._check_user_identity(res)
            client = dt.get_client(self, dt.get_dingtalk_config(self, res.company_id))
            # 获取部门ding_id
            department_list = list()
            if not res.department_id:
                raise UserError("请选择员工部门!")
            elif res.department_ids:
                department_list = res.department_ids.mapped('ding_id')
                if res.department_id.ding_id not in res.department_ids.mapped('ding_id'):
                    department_list.append(res.department_id.ding_id)
            else:
                department_list.append(res.department_id.ding_id)
            data = {
                'userid': res.ding_id,  # userid
                'name': res.name,  # 名称
                'department': department_list,  # 部门
                'position': res.job_title if res.job_title else '',  # 职位
                'mobile': res.mobile_phone if res.mobile_phone else res.work_phone,  # 手机
                'tel': res.work_phone if res.work_phone else '',  # 手机
                'workPlace': res.work_location if res.work_location else '',  # 办公地址
                'remark': res.notes if res.notes else '',  # 备注
                'email': res.work_email if res.work_email else '',  # 邮箱
                'jobnumber': res.din_jobnumber if res.din_jobnumber else '',  # 工号
                'isSenior': res.din_isSenior,  # 高管模式
                'isHide': res.din_isHide,  # 隐藏手机号
            }
            if res.din_hiredDate:
                hiredDate = dt.datetime_to_stamp(res.din_hiredDate)
                data.update({'hiredDate': hiredDate})
            try:
                result = client.user.update(data)
                _logger.info(_(result))
                res.message_post(body=u"已成功更新至钉钉", message_type='notification')
            except Exception as e:
                raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    def delete_ding_employee(self):
        if not self.user_has_groups('dingtalk_mc.manage_groups'):
            raise UserError("非钉钉管理员不允许删除员工信息！")
        for res in self:
            if not res.ding_id:
                continue
            self._delete_dingtalk_employee_by_id(res.ding_id, res.company_id)
            res.write({'ding_id': False})
            res.message_post(body=u"已在钉钉上删除员工。 *_*!", message_type='notification')
        return {'type': 'ir.actions.act_window_close'}

    def _delete_dingtalk_employee_by_id(self, ding_id, company):
        """
        删除钉钉员工
        :param ding_id:
        :param company:
        :return:
        """
        client = dt.get_client(self, dt.get_dingtalk_config(self, company))
        try:
            result = client.user.delete(ding_id)
            _logger.info(_("已在钉钉上删除Id:{}的员工".format(result)))
        except Exception as e:
            raise UserError(e)
        return

    def unlink(self):
        """
        重写删除函数
        :return:
        """
        for res in self:
            if res.ding_id and dt.get_config_is_delete(self, res.company_id):
                self._delete_dingtalk_employee_by_id(res.ding_id, res.company_id)
        return super(HrEmployee, self).unlink()

    def using_dingtalk_avatar(self):
        """
        替换为钉钉头像
        :return:
        """
        for emp in self:
            self._check_user_identity(emp)
            if emp.ding_avatar_url:
                binary_data = base64.b64encode(requests.get(emp.ding_avatar_url).content)
                emp.with_user(SUPERUSER_ID).write({'image_1920': binary_data})

    @api.model
    def _check_user_identity(self, employee):
        """
        检查操作的当前员工表是否为本人
        :param employee
        :return:
        """
        if not self.user_has_groups('dingtalk_mc.manage_groups'):
            if not employee.user_id or self.env.user.id != employee.user_id.id:
                raise UserError("您不能操作其他员工的钉钉信息！")

    @api.model
    def process_dingtalk_chat(self, result_msg, company):
        """
        接受来自钉钉回调的处理
        :param result_msg: 回调消息
        :param company: 公司
        :return:
        """
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                event_type = result_msg.get('EventType')  # 消息类型
                user_ids = result_msg.get('UserId')       # 用户id
                if event_type == 'user_leave_org':
                    # 用户离职
                    domain = [('ding_id', 'in', user_ids), ('company_id', '=', company.id)]
                    employees = self.env['hr.employee'].with_user(SUPERUSER_ID).search(domain)
                    if employees:
                        employees.with_user(SUPERUSER_ID).write({'active': False})
                else:
                    # 用户增加和变更时获取该用户详情
                    for user_id in user_ids:
                        self.get_employee_info(user_id, event_type, company)
        return True

    @api.model
    def get_employee_info(self, user_id, event_type, company):
        """
        获取用户详情执行函数
        :param user_id:
        :param event_type:
        :param company:
        :return:
        """
        try:
            client = dt.get_client(self, dt.get_dingtalk_config(self, company))
            result = client.user.get(user_id)
        except Exception as e:
            _logger.info("获取用户详情失败：{}".format(e))
            return
        if result.get('errcode') == 0:
            data = {
                'name': result.get('name'),  # 员工名称
                'ding_id': result.get('userid'),  # 钉钉用户Id
                'din_unionid': result.get('unionid'),  # 钉钉唯一标识
                'mobile_phone': result.get('mobile'),  # 手机号
                'work_phone': result.get('tel'),  # 分机号
                'work_location': result.get('workPlace'),  # 办公地址
                'notes': result.get('remark'),  # 备注
                'job_title': result.get('position'),  # 职位
                'work_email': result.get('email'),  # email
                'din_jobnumber': result.get('jobnumber'),  # 工号
                'ding_avatar_url': result.get('avatar') if result.get('avatar') else '',  # 钉钉头像url
                'din_isSenior': result.get('isSenior'),  # 高管模式
                'din_isAdmin': result.get('isAdmin'),  # 是管理员
                'din_isBoss': result.get('isBoss'),  # 是老板
                'din_isHide': result.get('isHide'),  # 隐藏手机号
                'din_active': result.get('active'),  # 是否激活
                'din_isLeaderInDepts': result.get('isLeaderInDepts'),  # 是否为部门主管
                'din_orderInDepts': result.get('orderInDepts'),  # 所在部门序位
                'company_id': company.id
            }
            # 支持显示国际手机号
            if result.get('stateCode') != '86':
                data.update({
                    'mobile_phone': '+{}-{}'.format(result.get('stateCode'), result.get('mobile')),
                })
            if result.get('hiredDate'):
                date_str = dt.timestamp_to_local_date(result.get('hiredDate'), obj=self)
                data.update({'din_hiredDate': date_str})
            if result.get('department'):
                dep_ding_ids = result.get('department')
                dep_list = self.env['hr.department'].with_user(SUPERUSER_ID).search([('ding_id', 'in', dep_ding_ids), ('company_id', '=', company.id)])
                data.update({'department_ids': [(6, 0, dep_list.ids)], 'department_id': dep_list[0].id if dep_list else False})
            # 当为新建时以名称进行搜索
            if event_type == 'user_add_org':
                employee = self.env['hr.employee'].with_user(SUPERUSER_ID).search([('name', '=', result.get('name')), ('company_id', '=', company.id)], limit=1)
                if not employee:
                    self.env['hr.employee'].with_user(SUPERUSER_ID).create(data)
                else:
                    employee.with_user(SUPERUSER_ID).write(data)
            else:
                employee = self.env['hr.employee'].with_user(SUPERUSER_ID).search([('ding_id', '=', user_id), ('company_id', '=', company.id)], limit=1)
                if employee:
                    employee.with_user(SUPERUSER_ID).write(data)
        else:
            _logger.info("从钉钉同步员工时发生意外，原因为:{}".format(result.get('errmsg')))
        return True
