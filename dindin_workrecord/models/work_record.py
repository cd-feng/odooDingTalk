# -*- coding: utf-8 -*-
import datetime
import json
import logging
import time

import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DinDinWorkRecord(models.Model):
    _name = 'dindin.work.record'
    _description = "钉钉待办事项"
    _inherit = ['mail.thread']
    _rec_name = 'name'

    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)
    name = fields.Char(string='标题', required=True)
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'待办用户', required=True)
    record_time = fields.Datetime(string=u'待办时间', default=datetime.datetime.now())
    record_url = fields.Char(string='待办URL链接', required=True)
    state = fields.Selection(string=u'发送状态', selection=[('00', '草稿'), ('01', '已发送'), ('02', '完成')], default='00')
    line_ids = fields.One2many(comodel_name='dindin.work.record.list', inverse_name='record_id', string=u'待办事项表单')
    record_id = fields.Char(string='待办任务ID', help="用于发送到钉钉后接受返回的id，通过id可以修改待办")
    record_type = fields.Selection(string=u'待办类型', selection=[('out', '发起'), ('put', '接收'), ], default='out')
    record_state = fields.Selection(string=u'待办状态', selection=[('00', '已通知'), ('01', '已更新'), ], default='00')

    @api.multi
    def send_record(self):
        """发送待办事项函数"""
        logging.info(">>>开始钉钉发送工作消息")
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'workrecord_add')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        formItemList = list()
        for line in self.line_ids:
            formItemList.append({
                'title': line.title,
                'content': line.content
            })
        c_time = int(time.mktime(time.strptime(str(self.record_time), "%Y-%m-%d %H:%M:%S")))
        data = {
            'userid': self.emp_id.din_id,
            'create_time': c_time,
            'title': self.name,
            'url': self.record_url if self.record_url else '',
            'formItemList': formItemList,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=30)
            result = json.loads(result.text)
            logging.info(">>>发送待办事项返回结果{}".format(result))
            if result.get('errcode') == 0:
                self.write({'state': '01', 'record_id': result.get('record_id')})
            else:
                raise UserError('发送消息失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")
        self.message_post(body=u"待办事项已推送到钉钉!", message_type='notification')

    @api.model
    def get_workrecord(self):
        """获取所有用户的待办事项"""
        logging.info(">>>Start getting to-do items")
        din_ids = self.env['hr.employee'].search_read([('din_id', '!=', '')], fields=['din_id'])
        offset = 0  # 分页游标
        limit = 50  # 分页大小
        for emp in din_ids:
            result = self.get_workrecord_url(emp.get('din_id'), offset, limit)
            if 'list' in result:
                for res in result.get('list'):
                    record = self.env['dindin.work.record'].search(
                        [('record_id', '=', res.get('record_id')), ('record_type', '!=', 'out')])
                    rec_line = list()
                    for res_line in res.get('forms'):
                        rec_line.append((0, 0, {'title': res_line.get('title'), 'content': res_line.get('content')}))
                    data = {
                        'name': res.get('title'),
                        'emp_id': emp.get('id'),
                        'record_url': res.get('url'),
                        'record_type': 'put',
                        'record_id': res.get('record_id'),
                        'line_ids': rec_line,
                    }
                    if record:
                        return False
                    else:
                        self.env['dindin.work.record'].create(data)
        logging.info(">>>Stop getting to-do items")

    @api.model
    def get_workrecord_url(self, user_id, offset, limit):
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'workrecord_getbyuserid')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'userid': user_id,
            'offset': offset,
            'limit': limit,
            'status': 0,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=30)
            result = json.loads(result.text)
            logging.info(">>>{}".format(result))
            if result.get('errcode') == 0:
                return result.get('records')
        except ReadTimeout:
            logging.info("获取所有用户的待办事项网络连接超时")

    @api.multi
    def record_update(self):
        """待办更新"""
        for res in self:
            logging.info("待办更新")
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'workrecord_update')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            data = {
                'userid': res.emp_id.din_id,
                'record_id': res.record_id,
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=30)
                result = json.loads(result.text)
                logging.info(">>>{}".format(result))
                if result.get('errcode') == 0:
                    if result.get('result'):
                        res.message_post(body=u"待办状态已更新!", message_type='notification')
                        res.write({'record_state': '01'})
                    else:
                        res.message_post(body=u"待办状态更新失败!", message_type='notification')
            except ReadTimeout:
                logging.info("获取所有用户的待办事项网络连接超时")


class DinDinWorkRecordList(models.Model):
    _name = 'dindin.work.record.list'
    _rec_name = 'title'
    _description = "待办事项表单"

    title = fields.Char(string='标题', required=True)
    content = fields.Char(string='内容', required=True)
    record_id = fields.Many2one(comodel_name='dindin.work.record', string=u'待办', ondelete='cascade')
