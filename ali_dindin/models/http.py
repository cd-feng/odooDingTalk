# -*- coding: utf-8 -*-
#----------------------------------------------------------
# OpenERP HTTP layer
#----------------------------------------------------------
import ast
import collections
import contextlib
import datetime
import functools
import hashlib
import hmac
import inspect
import logging
import mimetypes
import os
import pprint
import random
import re
import sys
import threading
import time
import traceback
import warnings
from os.path import join as opj
from zlib import adler32

import babel.core
from datetime import datetime, date
import passlib.utils
import psycopg2
import json
import werkzeug.contrib.sessions
import werkzeug.datastructures
import werkzeug.exceptions
import werkzeug.local
import werkzeug.routing
import werkzeug.wrappers
import werkzeug.wsgi
from werkzeug import urls
from werkzeug.wsgi import wrap_file

try:
    import psutil
except ImportError:
    psutil = None

import odoo
from odoo import fields
from odoo.service.server import memory_info
from odoo.service import security, model as service_model
from odoo.tools.func import lazy_property
from odoo.tools import ustr, consteq, frozendict, pycompat, unique, date_utils

# from .modules.module import module_manifest

_logger = logging.getLogger(__name__)
rpc_request = logging.getLogger(__name__ + '.rpc.request')
rpc_response = logging.getLogger(__name__ + '.rpc.response')

class JsonRequest(WebRequest):

    def _json_response(self, result=None, error=None):

        response = {
            'jsonrpc': '2.0',
            'id': self.jsonrequest.get('id')
            }
        if isinstance(result, dict) and result is not None and result.get('json'):
            mime = 'application/json'
            body = json.dumps(result.get('data'))
            return Response(body, status=200, headers=[('Content-Type', mime), ('Content-Length', len(body))])
        if error is not None:
            response['error'] = error
        if result is not None:
            response['result'] = result

        if self.jsonp:
            # If we use jsonp, that's mean we are called from another host
            # Some browser (IE and Safari) do no allow third party cookies
            # We need then to manage http sessions manually.
            response['session_id'] = self.session.sid
            mime = 'application/javascript'
            body = "%s(%s);" % (self.jsonp, json.dumps(response, default=date_utils.json_default))
        else:
            mime = 'application/json'
            body = json.dumps(response, default=date_utils.json_default)

        return Response(
            body, status=error and error.pop('http_status', 200) or 200,
            headers=[('Content-Type', mime), ('Content-Length', len(body))]
        )
