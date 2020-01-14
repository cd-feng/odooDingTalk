# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
import base64
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.modules import get_module_resource
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class DingTalkEmployee(models.Model):
    _name = 'dingtalk.add.employee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '待入职员工'

    @api.model
    def _default_image(self):
        image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
        return base64.b64encode(open(image_path, 'rb').read())

    USERSTATE = [
        ('new', '草稿'),
        ('ok', '已添加')
    ]
    EMPLOYEETYPE = [
        ('0', '无类型'),
        ('1', '全职'),
        ('2', '兼职'),
        ('3', '实习'),
        ('4', '劳务派遣'),
        ('5', '退休返聘'),
        ('6', '劳务外包'),
    ]
    active = fields.Boolean(string='有效', default=True)
    ding_id = fields.Char(string='钉钉用户Id')
    name = fields.Char(string='员工姓名', required=True)
    mobile = fields.Char(string='手机号', required=True)
    pre_entry_time = fields.Datetime(string='预期入职时间', required=True)
    op_userid = fields.Many2one(comodel_name='hr.employee', string=u'操作人', domain=[('ding_id', '!=', False)], required=True)
    depts = fields.Many2many(comodel_name='hr.department', string='入职部门', domain=[('ding_id', '!=', False)])
    mainDeptId = fields.Many2one(comodel_name='hr.department', string=u'主部门', domain=[('ding_id', '!=', False)], required=True)
    position = fields.Many2one(comodel_name='hr.job', string=u'职位')
    workPlace = fields.Char(string='工作地点')
    employeeType = fields.Selection(string=u'员工类型', selection=EMPLOYEETYPE)
    jobNumber = fields.Char(string='员工工号', required=True)

    company_id = fields.Many2one('res.company', '公司', default=lambda self: self.env.user.company_id.id)
    image = fields.Image("Image", max_width=100, max_height=100, default=_default_image)
    state = fields.Selection(string='状态', selection=USERSTATE, default='new', track_visibility='onchange')

    def add_employee(self):
        """
        智能人事添加企业待入职员工
        :param param: 添加待入职入参
        """
        for res in self:
            din_client = dingtalk_api.get_client(self)
            logging.info(">>>添加待入职员工start")
            name = res.name
            mobile = res.mobile
            pre_entry_time = res.pre_entry_time
            op_userid = res.op_userid.ding_id or ''
            depts = ''
            for dept in res.depts:
                depts = depts + '|{}'.format(dept.ding_id)
            extend_info = {
                'depts': depts,
            }
            if res.mainDeptId:
                extend_info['mainDeptId'] = res.mainDeptId.ding_id
                extend_info['mainDeptName'] = res.mainDeptId.name
            if res.position:
                extend_info['position'] = res.position.name
            if res.workPlace:
                extend_info['workPlace'] = res.workPlace
            if res.jobNumber:
                extend_info['jobNumber'] = res.jobNumber
            if res.employeeType:
                extend_info['employeeType'] = res.employeeType
            try:
                result = din_client.employeerm.addpreentry(name, mobile, pre_entry_time, op_userid, extend_info)
                logging.info(">>>添加待入职员工返回结果%s", result)
                res.write({
                    'ding_id': result.get('userid'),
                    'state': 'ok'
                })
                res.message_post(body=u"已添加到钉钉待入职员工列表。 *_*!", message_type='notification')
            except Exception as e:
                raise UserError(e)
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def count_pre_entry(self):
        """
        智能人事查询公司待入职员工列表,返回待入职总人数
        智能人事业务，企业/ISV分页查询公司待入职员工id列表

        :param offset: 分页起始值，默认0开始
        :param size: 分页大小，最大50
        """
        din_client = dingtalk_api.get_client(self)
        try:
            result = din_client.employeerm.querypreentry(offset=0, size=50)
            logging.info(">>>查询待入职员工列表返回结果%s", result)
            if result['data_list']['string']:
                pre_entry_list = result['data_list']['string']
                return len(pre_entry_list)
        except Exception as e:
            raise UserError(e)

    def unlink(self):
        for res in self:
            if res.state == 'ok':
                raise UserError(_("已上传到钉钉的待入职信息不允许删除。 *_*!"))
            return super(DingTalkEmployee, self).unlink()
