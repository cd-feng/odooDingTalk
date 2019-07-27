# -*- coding: utf-8 -*-
# ----------------------------------------------------------
# OpenERP HTTP layer
# ----------------------------------------------------------

import logging
import json
import odoo
from odoo.tools import date_utils
from odoo.http import WebRequest, Response


def _json_response(self, result=None, error=None):

    response = {
        'jsonrpc': '2.0',
        'id': self.jsonrequest.get('id')
    }
    # 修复钉钉注册回调事件时报错
    if isinstance(result, dict) and result is not None and result.get('json'):
        mime = 'application/json'
        body = json.dumps(result.get('data'))
        return Response(body, status=200, headers=[('Content-Type', mime), ('Content-Length', len(body))])
    if error is not None:
        response['error'] = error
    if result is not None:
        response['result'] = result
    mime = 'application/json'
    body = json.dumps(response, default=date_utils.json_default)
    return Response(
        body, status=error and error.pop('http_status', 200) or 200,
        headers=[('Content-Type', mime), ('Content-Length', len(body))]
    )

odoo.http.JsonRequest._json_response = _json_response