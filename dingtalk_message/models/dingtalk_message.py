# -*- coding: utf-8 -*-
import json
import babel
import logging
import requests
from odoo import api, models, tools, http, _, SUPERUSER_ID
import threading
from odoo.addons.dingtalk_mc.tools import dingtalk_tool
from werkzeug import urls
import datetime
import copy
import functools
import time
import dateutil.relativedelta as relativedelta
from babel.dates import format_date
from odoo.addons.web.controllers.main import DataSet
from odoo.http import request

from source.odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
try:
    from jinja2.sandbox import SandboxedEnvironment
    mako_template_env = SandboxedEnvironment(
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="${",
        variable_end_string="}",
        comment_start_string="<%doc>",
        comment_end_string="</%doc>",
        line_statement_prefix="%",
        line_comment_prefix="##",
        trim_blocks=True,               # do not output newline after blocks
        autoescape=True,                # XML/HTML automatic escaping
    )
    mako_template_env.globals.update({
        'str': str,
        'quote': urls.url_quote,
        'urlencode': urls.url_encode,
        'datetime': datetime,
        'len': len,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'filter': filter,
        'reduce': functools.reduce,
        'map': map,
        'round': round,
        'relativedelta': lambda *a, **kw: relativedelta.relativedelta(*a, **kw),
    })
    mako_safe_template_env = copy.copy(mako_template_env)
    mako_safe_template_env.autoescape = False
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


def format_datetime(env, dt, tz=False, dt_format='medium', lang_code=False):
    try:
        return tools.format_datetime(env, dt, tz=tz, dt_format=dt_format, lang_code=lang_code)
    except babel.core.UnknownLocaleError:
        return dt


class DingTalkMessageTool(models.TransientModel):
    _name = 'dingtalk.message.tool'

    @api.model
    def send_create_user_message(self, company, ding_id, msg_body, user_id):
        """
        发送通知消息给指定用户
        :return:
        """
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                # ------
                dingtalk_config = dingtalk_tool.get_dingtalk_config(self, company)
                client = dingtalk_tool.get_client(self, dingtalk_config)
                msg_body = self.render_msg_body(msg_body, 'res.users', user_id)
                if msg_body:
                    single_url = self.env['ir.config_parameter'].with_user(SUPERUSER_ID).get_param('web.base.url')
                    msg = {
                        "msgtype": "action_card",
                        "action_card": {
                            "title": "账户消息通知",
                            "markdown": msg_body,
                            "single_title": "登陆系统",
                            "single_url": single_url,
                        }
                    }
                    try:
                        result = client.post('topapi/message/corpconversation/asyncsend_v2', {
                            'agent_id': dingtalk_config.agent_id,
                            'userid_list': ding_id,
                            'msg': msg,
                        })
                    except Exception as e:
                        result = str(e)
                        _logger.info(">>> 发送创建用户消息通知失败！原因：{}".format(result))
                    # 创建消息日志
                    self.env['dingtalk.message.log'].create({
                        'company_id': company.id,
                        'name': "创建用户通知",
                        'msg_type': "work",
                        'body': msg_body,
                        'result': result,
                    })
        return True

    @api.model
    def render_msg_body(self, template_txt, model, res_id):
        """
        读取模板内容
        :param template_txt:  消息模板
        :param model:         源模型
        :param res_id:        源记录id
        :return:
        """
        time.sleep(10)
        mako_env = mako_safe_template_env if self.env.context.get('safe') else mako_template_env
        template = mako_env.from_string(tools.ustr(template_txt))
        record = self.env[model].browse(res_id)
        # variables = {
        #     'format_date': lambda date, format=False, context=self._context: format_date(self.env, date, format),
        #     'format_tz': lambda dt, tz=False, format=False, context=self._context: format_tz(self.env, dt, tz, format),
        #     'format_amount': lambda amount, currency, context=self._context: format_amount(self.env, amount, currency),
        #     'user': self.env.user,
        #     'ctx': self._context,
        #     'object': record
        # }
        variables = {
            'format_date': lambda date, date_format=False, lang_code=False: format_date(self.env, date, date_format, lang_code),
            'format_datetime': lambda dt, tz=False, dt_format=False, lang_code=False: format_datetime(self.env, dt, tz, dt_format, lang_code),
            'format_amount': lambda amount, currency, lang_code=False: tools.format_amount(self.env, amount, currency, lang_code),
            'format_duration': lambda value: tools.format_duration(value),
            'user': self.env.user,
            'ctx': self._context,
            'object': record
        }
        try:
            render_result = template.render(variables)
        except Exception as e:
            _logger.info(str(e))
            return False
        return render_result

    @api.model
    def send_notice_message(self, config_id, res_model, res_id, company):
        """
        发送通知消息
        :param config_id:   消息模板id
        :param res_model:   发生消息单据
        :param res_id:     发生消息单据id
        :param company:    公司
        :return:
        """
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                # 获取源模型
                msg_config = self.env['dingtalk.message.config'].search([('id', '=', config_id)])
                res_model = self.env[res_model].with_user(SUPERUSER_ID).search([('id', '=', res_id)])
                msg_body = self.render_msg_body(msg_config.msg_body, res_model._name, res_id)
                dingtalk_config = dingtalk_tool.get_dingtalk_config(self, company)
                msg_data = {'agent_id': dingtalk_config.agent_id}
                client = dingtalk_tool.get_client(self, dingtalk_config)
                result = None
                # 工作通知
                if msg_config.ttype == 'notice':
                    result = self.send_work_config_message(msg_data, msg_config, msg_body, client)
                # 通知到企业群
                elif msg_config.ttype == 'chat':
                    msg_data = {
                        'chatid': msg_config.chat_id.chat_id,
                        'msg': {
                            "msgtype": "action_card",
                            "action_card": {
                                "title": msg_config.msg_title or _('单据变更通知'),
                                "markdown": msg_body,
                                "single_title": "详情",
                                "single_url": self.env['ir.config_parameter'].with_user(SUPERUSER_ID).get_param('web.base.url'),
                            }
                        }
                    }
                    # 发送消息
                    try:
                        result = client.post('chat/send', msg_data)
                        _logger.info(result)
                    except Exception as e:
                        result = str(e)
                        _logger.info(">>> 通知到企业群失败！原因：{}".format(result))
                # 通知到群机器人
                else:
                    headers = {'Content-Type': 'application/json'}
                    data = {
                        "msgtype": "actionCard",
                        "actionCard": {
                            "title": msg_config.msg_title or _('单据变更通知'),
                            "text": msg_body,
                            "singleTitle": "详情",
                            "singleURL": self.env['ir.config_parameter'].with_user(SUPERUSER_ID).get_param('web.base.url'),
                        }
                    }
                    try:
                        result = requests.post(url=msg_config.robot_id.webhook, headers=headers, data=json.dumps(data))
                        result = result.text
                        _logger.info(result)
                    except Exception as e:
                        result = str(e)
                        _logger.info(">>> 通知到群机器人失败！原因：{}".format(result))
                # 创建消息日志
                self.env['dingtalk.message.log'].create({
                    'company_id': company.id,
                    'name': msg_config.name,
                    'msg_type': "work",
                    'body': msg_body,
                    'result': result,
                })

    @api.model
    def send_work_config_message(self, msg_data, msg_config, msg_body, client):
        """
        组织工作通知消息并发送
        :param msg_data:
        :param msg_config:
        :param msg_body:
        :param client:
        :return: result
        """
        msg_data['msg'] = {
            "msgtype": "action_card",
            "action_card": {
                "title": msg_config.msg_title or _('单据变更通知'),
                "markdown": msg_body,
                "single_title": _("详情"),
                "single_url": self.env['ir.config_parameter'].with_user(SUPERUSER_ID).get_param('web.base.url'),
            }
        }
        if msg_config.to_all_user:
            msg_data['to_all_user'] = True
        elif len(msg_config.department_ids) > 0:
            dept_str = ''
            for dept in msg_config.department_ids:
                if dept_str == '':
                    dept_str = dept_str + "{}".format(dept.ding_id)
                else:
                    dept_str = dept_str + ",{}".format(dept.ding_id)
            msg_data['dept_id_list'] = dept_str
        elif len(msg_config.user_ids) > 0:
            user_str = ''
            for user in msg_config.user_ids:
                if user.ding_id:
                    if user_str == '':
                        user_str = user_str + "{}".format(user.ding_id)
                    else:
                        user_str = user_str + ",{}".format(user.ding_id)
            msg_data['userid_list'] = user_str
        else:
            return
        # 发送消息
        try:
            result = client.post('topapi/message/corpconversation/asyncsend_v2', msg_data)
            _logger.info(result)
        except Exception as e:
            result = str(e)
            _logger.info(">>> 工作通知失败！原因：{}".format(result))
        return result


class MessageDataSet(DataSet):
    """ 处理单据按钮消息 """

    @http.route('/web/dataset/call_button', type='json', auth="user")
    def call_button(self, model, method, args, kwargs):
        ir_model = request.env['ir.model'].with_user(SUPERUSER_ID).search([('model', '=', model)], limit=1)
        uid = kwargs.get('context').get('uid')
        user = request.env['res.users'].search([('id', '=', uid)])
        domain = [('model_id', '=', ir_model.id), ('company_id', '=', user.company_id.id),
                  ('state', '=', 'open'), ('msg_opportunity', '=', 'button')]
        msg_configs = request.env['dingtalk.message.config'].with_user(SUPERUSER_ID).search(domain)
        for msg_config in msg_configs:
            buttons_list = list()
            for button in msg_config.button_ids:
                buttons_list.append(button.function)
            if method in buttons_list:
                # 获取当前单据的id
                if args[0]:
                    res_id = args[0][0]
                else:
                    params = args[1].get('params')
                    res_id = params.get('id')
                # 获取当前单据
                now_model = request.env[model].with_user(SUPERUSER_ID).search([('id', '=', res_id)])
                message_tool = request.env['dingtalk.message.tool']
                threading.Thread(target=message_tool.send_notice_message,
                                 args=(msg_config.id, model, now_model.id, user.company_id)).start()
        return super(MessageDataSet, self).call_button(model, method, args, kwargs)
