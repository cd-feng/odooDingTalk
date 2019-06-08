# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DinDinApprovalTemplate(models.Model):
    _name = 'dindin.approval.template'
    _description = "审批模板"
    _rec_name = 'name'

    name = fields.Char(string='模板名', required=True)
    icon_url = fields.Char(string='图标url')
    process_code = fields.Char(string='模板唯一标识')
    url = fields.Char(string='模板跳转url')
    company_id = fields.Many2one(comodel_name='res.company',
                                 string=u'公司', default=lambda self: self.env.user.company_id.id)

    @api.model
    def get_template(self):
        """获取审批模板"""
        logging.info(">>>获取审批模板...")
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'process_listbyuserid')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'offset': 0,
            'size': 100,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=20)
            result = json.loads(result.text)
            # logging.info(">>>获取审批模板返回结果{}".format(result))
            if result.get('errcode') == 0:
                d_res = result.get('result')
                for process in d_res.get('process_list'):
                    data = {
                        'name': process.get('name'),
                        'icon_url': process.get('icon_url'),
                        'process_code': process.get('process_code'),
                        'url': process.get('url'),
                    }
                    template = self.env['dindin.approval.template'].search(
                        [('process_code', '=', process.get('process_code'))])
                    if template:
                        template.write(data)
                    else:
                        self.env['dindin.approval.template'].create(data)
            else:
                raise UserError('获取审批模板失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")
        logging.info(">>>获取审批模板结束...")

    @api.model
    def get_get_template_number_by_user(self):
        """
        根据当前用户获取该用户的待审批数量
        :return:
        """
        emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)])
        if len(emp) > 1:
            return {'state': False, 'number': 0, 'msg': '登录用户关联了多个员工'}
        if emp and emp.din_id:
            url = self.env['ali.dindin.system.conf'].search([('key', '=', 'process_gettodonum')]).value
            token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
            data = {
                'userid': emp.din_id,
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
                result = json.loads(result.text)
                if result.get('errcode') == 0:
                    return {'state': True, 'number': result.get('count')}
                else:
                    return {'state': False, 'number': 0, 'msg': result.get('errmsg')}
            except ReadTimeout:
                return {'state': False, 'number': 0, 'msg': '网络连接超时'}
            except Exception:
                return {'state': False, 'number': 0, 'msg': "网络连接失败"}
        else:
            return {'state': False, 'number': 0, 'msg': 'None'}

    # TODO 需要进步完善获取单个实例后写入到odoo对应的单据中
    @api.model
    def get_processinstance(self, pid, pcode):
        """
        获取单个审批实例
        :param pid:
        :param pcode:
        :return:
        """
        url = self.env['ali.dindin.system.conf'].search([('key', '=', 'processinstance_get')]).value
        token = self.env['ali.dindin.system.conf'].search([('key', '=', 'token')]).value
        data = {
            'process_instance_id': pid,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                process_instance = result.get('process_instance')
                temp = self.env['dindin.approval.template'].sudo().search([('process_code', '=', pcode)])
                if temp:
                    appro = self.env['dindin.approval.control'].sudo().search([('template_id', '=', temp[0].id)])
                    if appro:
                        oa_model = self.env[appro.oa_model_id.model].sudo().search([('process_instance_id', '=', pid)])
                        if not oa_model:
                            # 获取发起人
                            emp = self.env['hr.employee'].sudo().search([('din_id', '=', process_instance.get("originator_userid"))])
                            data = {
                                'title': process_instance.get('title'),
                                'create_date': process_instance.get("create_time"),
                                'originator_user_id': emp.id if emp else False,
                            }
                            # 审批状态
                            if process_instance.get("status") == 'NEW':
                                data.update({'oa_state': '00'})
                            elif process_instance.get("status") == 'RUNNING':
                                data.update({'oa_state': '01'})
                            else:
                                data.update({'oa_state': '02'})

            else:
                logging.info('>>>获取单个审批实例-失败，原因为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            logging.info('>>>获取单个审批实例-网络连接超时')

        # {
        #     "EventType": "bpms_instance_change",
        #     "processInstanceId": "ad253df6-e175caf-68085c60ba8a",
        #     "corpId": "ding2c4d8175651",
        #     "createTime": 1495592259000,
        #     "title": "自测-1016",
        #     "type": "start",
        #     "staffId": "er5875",
        #     "url": "https://aflow.dingtalk.com/dingtalk/mobile/homepage.htm",
        #     "processCode": "xxx"
        # }