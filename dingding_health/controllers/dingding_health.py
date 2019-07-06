# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class OnboardingController(http.Controller):

    @http.route('/healths/dingding_health_onboarding_panel', auth='user', type='json')
    def dingding_health_onboarding(self):
        company = request.env.user.company_id
        # if not request.env.user._is_admin() or \
        #    company.sale_quotation_onboarding_state == 'closed':
        #     return {}
        return {
            'html': request.env.ref('dingding_health.dingding_health_onboarding_panel').render({
                'company': company,
                'state': company.get_and_update_sale_quotation_onboarding_state()
            })
        }