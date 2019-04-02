# -*- coding: utf-8 -*-
import json
import logging
from odoo import http, _
from odoo.addons.web.controllers.main import Home
from odoo.http import request
from . import tool

_logger = logging.getLogger(__name__)


class BpmsCallBack(Home, http.Controller):

    # 审批事件
    @http.route('/callback/bpms', type='json', auth='none', methods=['POST'], csrf=False)
    def callback_users(self, **kw):
        logging.info(">>>钉钉回调-审批事件")
        json_str = request.jsonrequest
        call_back, din_corpId = tool.get_bash_attr('03')
        msg = tool.encrypt_result(json_str.get('encrypt'), call_back[0].aes_key, din_corpId)
        logging.info("-------------------------------------------")
        logging.info(">>>解密消息结果:{}".format(msg))
        logging.info("-------------------------------------------")
        msg = json.loads(msg)
        if msg.get('EventType') == 'bpms_task_change':
            logging.info(">>>钉钉回调-审批任务开始，结束，转交")
        # 返回加密结果
        return tool.result_success(call_back[0].aes_key, call_back[0].token, din_corpId)
