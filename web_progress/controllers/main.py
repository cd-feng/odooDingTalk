import json
from odoo import http
from odoo.addons.web.controllers.main import ReportController, request

class WPReportController(ReportController):

    @http.route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token):
        """
        Pass web progress code from request content to the context
        """
        requestcontent = json.loads(data)
        if len(requestcontent) > 2:
            request_context = requestcontent[2]
            if 'progress_code' in request_context:
                context = request.env.context.copy()
                context.update(request_context)
                request._env = request.env(context=context)
                request._context = context
        web_progress_obj = request.env['web.progress']
        web_progress_obj.web_progress_percent(0, 'Report')
        ret = super(WPReportController, self).report_download(data, token)
        web_progress_obj.web_progress_percent(100, 'Report done')
        return ret