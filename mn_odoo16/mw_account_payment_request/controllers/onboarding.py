# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


class OnboardingController(http.Controller):

    @http.route('/mw_account_payment_request/payment_request_onboarding_panel', auth='user', type='json')
    def payment_request_onboarding(self):
        """ Returns the `banner` for the sale onboarding panel.
            It can be empty if the user has closed it or if he doesn't have
            the permission to see it. """
#         print ('request.env ',request.env.context)
        company = request.env.company
        print ('a1231231')
        cr = request.cr
        query = "select onboarding_state,user_id,id from payment_request where user_id =%s order by id desc limit 1  " % request.env.context.get('uid',1)
        cr.execute(query)
        rr = cr.fetchall()
#         print ('rr ',rr)
        if len(rr)>0 and rr[0][0]=='closed':
            return {}            
#         if not request.env.is_admin() or \
#            company.sale_quotation_onboarding_state == 'closed':
#             return {}


        return {
#             'html': request.env.ref('mw_account_payment_request.payment_request_onboarding_panel').render({
            'html': request.env.ref('mw_account_payment_request.request_close_onboarding_panel').render({
                'company': company,
                'state': {'see_state':'note_done'}
            })
        }

#         return {
#             'html': request.env.ref('account.account_invoice_onboarding_panel').render({
#                 'company': company,
#                 'state': {'see_state':'note_done'}
#             })
#         }
        
