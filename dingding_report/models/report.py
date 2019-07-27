# -*- coding: utf-8 -*-
import json
import logging
import requests
import time
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingDingReportUser(models.Model):
    _name = 'dingding.report.user'
    _description = "用户日志"
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(default=True)
    name = fields.Char(string=u'日志名称', required=True)
    report_type = fields.Many2one(comodel_name='dingding.report.template', string=u'日志类型')
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门')
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', domain=[('ding_id', '!=', '')], required=True)
    report_id = fields.Char(string='日志Id')
    remark = fields.Text(string='日志备注')
    report_date = fields.Date(string=u'创建日期')
    company_id = fields.Many2one('res.company', string='公司', default=lambda self: self.env.user.company_id.id)
    line_ids = fields.One2many(comodel_name='dingding.report.user.line', inverse_name='rep_id', string=u'日志列表')
    read_num = fields.Integer(string='已读人数', default=0)
    comment_num = fields.Integer(string='评论个数', default=0)
    comment_user_num = fields.Integer(string='去重后评论数', default=0)
    like_num = fields.Integer(string='点赞人数', default=0)
    people_read_list = fields.Many2many(comodel_name='hr.employee', relation='d_report_user_and_read_list_rel',
                                        column1='report_id', column2='emp_id', string=u'已读人员')
    people_receive_list = fields.Many2many(comodel_name='hr.employee', relation='d_report_user_and_receive_list_rel',
                                           column1='report_id', column2='emp_id', string=u'日志接收人')
    people_like_list = fields.Many2many(comodel_name='hr.employee', relation='d_report_user_and_like_list_rel',
                                        column1='report_id', column2='emp_id', string=u'点赞人员')
    comment_ids = fields.One2many(comodel_name='dingding.report.comments.list', inverse_name='rep_id', string=u'评论列表')

    @api.multi
    def get_report_number_info(self):
        """
        获取日志统计数据（已读人数、评论个数、去重个数、点赞人数）
        :return:
        """
        for res in self:
            url = self.env['dingding.parameter'].search([('key', '=', 'report_statistics')]).value
            token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
            data = {
                'report_id': res.report_id,
            }
            headers = {'Content-Type': 'application/json'}
            try:
                result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=2)
                result = json.loads(result.text)
                logging.info(">>>获取日志统计数据返回结果{}".format(result))
                if result.get('errcode') == 0:
                    d_res = result.get('result')
                    data = {
                        'read_num': d_res.get('read_num'),
                        'comment_num': d_res.get('comment_num'),
                        'comment_user_num': d_res.get('comment_user_num'),
                        'like_num': d_res.get('like_num'),
                    }
                    res.write(data)
                else:
                    raise UserError('获取日志统计数据失败，详情为:{}'.format(result.get('errmsg')))
            except ReadTimeout:
                raise UserError("网络连接超时！")
            # 获取日志相关人员列表
            self.get_report_receivers(res)
            # 获取日志接收人列表
            self.get_report_receives(res)
            # 获取评论详情
            self.get_report_comments(res)

    @api.model
    def get_report_receivers(self, res):
        """
        获取获取已读人员he 点赞人员列表
        :param res:
        :return:
        """
        url = self.env['dingding.parameter'].search([('key', '=', 'report_statistics_listbytype')]).value
        token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
        # 获取已读人员
        data = {
            'report_id': res.report_id,
            'type': 0,
            'offset': 0,
            'size': 100,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=3)
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                d_res = result.get('result')
                people_read_list = list()
                for user_id in d_res.get('userid_list'):
                    emp = self.env['hr.employee'].search([('ding_id', '=', user_id)])
                    if emp:
                        people_read_list.append(emp.id)
                res.write({'people_read_list': [(6, 0, people_read_list)]})
            else:
                raise UserError('获取日志相关人员列表失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")
        # 获取点赞人员
        data = {
            'report_id': res.report_id,
            'type': 2,
            'offset': 0,
            'size': 100,
        }
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=3)
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                d_res = result.get('result')
                people_like_list = list()
                for user_id in d_res.get('userid_list'):
                    emp = self.env['hr.employee'].search([('ding_id', '=', user_id)])
                    if emp:
                        people_like_list.append(emp.id)
                res.write({'people_like_list': [(6, 0, people_like_list)]})
            else:
                raise UserError('获取日志相关人员列表失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")
        return True

    @api.model
    def get_report_receives(self, res):
        """
        获取日志接收人列表
        :param res:
        :return:
        """
        url = self.env['dingding.parameter'].search([('key', '=', 'report_receiver_list')]).value
        token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
        data = {
            'report_id': res.report_id,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=3)
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                d_res = result.get('result')
                people_receive_list = list()
                for user_id in d_res.get('userid_list'):
                    emp = self.env['hr.employee'].search([('ding_id', '=', user_id)])
                    if emp:
                        people_receive_list.append(emp.id)
                res.write({'people_receive_list': [(6, 0, people_receive_list)]})
            else:
                raise UserError('获取日志接收人列表数据失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")
        return True

    @api.model
    def get_report_comments(self, res):
        """
        获取日志评论详情
        :param res:
        :return:
        """
        url = self.env['dingding.parameter'].search([('key', '=', 'report_comment_list')]).value
        token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
        data = {
            'report_id': self.report_id,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=3)
            result = json.loads(result.text)
            if result.get('errcode') == 0:
                d_res = result.get('result')
                comment_list = list()
                for comment in d_res.get('comments'):
                    emp = self.env['hr.employee'].sudo().search([('ding_id', '=', comment.get('userid'))])
                    if emp:
                        comment_list.append((0, 0, {
                            'emp_id': emp[0].id,
                            'report_comment': comment.get('content'),
                            'report_create_time': comment.get('create_time'),
                            'rep_id': res.id,
                        }))
                res.comment_ids = False
                res.write({'comment_ids': comment_list})
            else:
                raise UserError('获取日志评论数据失败，详情为:{}'.format(result.get('errmsg')))
        except ReadTimeout:
            raise UserError("网络连接超时！")
        return True


class DingDingReportUserLine(models.Model):
    _name = 'dingding.report.user.line'
    _description = "日志列表"
    _rec_name = 'rep_id'

    rep_id = fields.Many2one(comodel_name='dingding.report.user', string=u'用户日志', ondelete='cascade')
    sequence = fields.Integer(string=u'序号')
    title = fields.Char(string='标题')
    content = fields.Text(string=u'内容')


class GetUserDingDingReportList(models.TransientModel):
    _name = 'get.dingding.user.report.list'
    _description = "获取员工日志列表"
    _rec_name = 'start_time'

    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', domain=[('ding_id', '!=', '')])
    start_time = fields.Datetime(string=u'开始日期', required=True, default=str(fields.datetime.now()))
    end_time = fields.Datetime(string=u'结束日期', required=True, default=str(fields.datetime.now()))
    report_type = fields.Many2one(comodel_name='dingding.report.template', string=u'日志类型')

    @api.multi
    def get_report_by_user(self):
        """
        拉取员工日志列表
        :return:
        """
        for res in self:
            group = self.env.user.has_group('dingding_report.dd_get_user_report_list')
            if not group:
                raise UserError("不好意思，你没有权限进行本操作！")
            url = self.env['dingding.parameter'].search([('key', '=', 'report_list')]).value
            token = self.env['dingding.parameter'].search([('key', '=', 'token')]).value
            cursor = 0
            size = 20
            while True:
                data = {
                    'start_time': int(time.mktime(self.start_time.timetuple()) * 1000),
                    'end_time': int(time.mktime(self.end_time.timetuple()) * 1000),
                    'cursor': cursor,
                    'size': size,
                }
                if res.employee_id:
                    data.update({'userid': res.employee_id.ding_id})
                if res.report_type:
                    data.update({'template_name': res.report_type.name})
                headers = {'Content-Type': 'application/json'}
                try:
                    result = requests.post(url="{}{}".format(url, token), headers=headers, data=json.dumps(data), timeout=5)
                    result = json.loads(result.text)
                    if result.get('errcode') == 0:
                        logging.info(result)
                        d_res = result.get('result')
                        for data_list in d_res.get('data_list'):
                            emp = self.env['hr.employee'].search([('name', '=', data_list.get('creator_name'))])
                            template = self.env['dingding.report.template'].search([('name', '=', data_list.get('template_name'))])
                            data = {
                                'name': data_list.get('template_name'),
                                'report_type': template[0].id if template else False,
                                'remark': data_list.get('remark'),
                                'report_id': data_list.get('report_id'),
                                'department_id': emp[0].department_id.id if emp and emp.department_id else False,
                                'employee_id': emp[0].id if emp else False,
                                'report_date': self.get_time_stamp(data_list.get('create_time')),
                            }
                            report_list = list()
                            for content in data_list.get('contents'):
                                report_list.append((0, 0, {
                                    'sequence': int(content.get('sort')),
                                    'title': content.get('key'),
                                    'content': content.get('value'),
                                }))
                            data.update({'line_ids': report_list})
                            report = self.env['dingding.report.user'].search([('report_id', '=', data_list.get('report_id'))])
                            if report:
                                report.line_ids = False
                                report.write(data)
                            else:
                                self.env['dingding.report.user'].create(data)
                        if d_res.get('has_more'):
                            cursor = d_res.get('next_cursor')
                            size = 20
                        else:
                            break
                    else:
                        raise UserError('获取日志列表失败，详情为:{}'.format(result.get('errmsg')))
                except ReadTimeout:
                    raise UserError("网络连接超时！")
        action = self.env.ref('dingding_report.dingding_report_user_action').read()[0]
        return action

    @api.model
    def get_time_stamp(self, time_number):
        """
        将13位时间戳转换为时间
        :param time_number:
        :return:
        """
        if time_number:
            time_stamp = float(time_number / 1000)
            time_array = time.localtime(time_stamp)
            return time.strftime("%Y-%m-%d %H:%M:%S", time_array)


class DingDingReportCommentsList(models.Model):
    _name = 'dingding.report.comments.list'
    _description = "日志评论列表"
    _rec_name = 'rep_id'

    sequence = fields.Integer(string=u'序号')
    emp_id = fields.Many2one('hr.employee', string='评论人', required=True)
    report_comment = fields.Text(string='评论内容')
    report_create_time = fields.Char(string='评论时间')
    rep_id = fields.Many2one('dingding.report.user', string='用户日志')
