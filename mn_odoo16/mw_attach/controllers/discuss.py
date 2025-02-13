# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.mail.controllers.discuss import DiscussController
from odoo.exceptions import AccessError, MissingError
from collections import OrderedDict
from odoo.http import request

class DiscussController(DiscussController):

    @http.route('/mail/thread/data', methods=['POST'], type='json', auth='user')
    def mail_thread_data(self, thread_model, thread_id, request_list, **kwargs):
        res = {}
        thread = request.env[thread_model].with_context(active_test=False).search([('id', '=', thread_id)])
        if 'attachments' in request_list:
            # if thread._name=='insurance.claim':
            #     ss=thread.env['ir.attachment'].search([('res_id', '=', thread.id), 
            #                                                          ('res_model', '=', thread._name)], order='id desc')
            #     sss=thread.env['ir.attachment'].search([('res_id', 'in', thread.required_material_line.ids), 
            #                                                          ('res_model', '=', 'insurance.claim.required.material.line')], order='id desc')
            #     guarantee=thread.env['insurance.claim.guarantee'].search([('claim_id', '=', thread.id)], order='id desc')
            #     if guarantee:
            #         ssss = thread.env['ir.attachment'].search([
            #             ('res_id', 'in', guarantee.required_material_line.ids), 
            #             ('res_model', '=', 'insurance.claim.required.material.line')
            #         ], order='id desc')
            #         ss+=ssss
            #     ss+=sss
            #     s=ss._attachment_format()
            #     res['attachments'] = s
            # elif thread._name=='insurance.contract':
            #     ss=thread.env['ir.attachment'].search([('res_id', '=', thread.id), 
            #                                                          ('res_model', '=', thread._name)], order='id desc')
            #     sss=thread.env['ir.attachment'].search([('res_id', 'in', thread.policy_ids.ids), 
            #                                                          ('res_model', '=', 'insurance.contract.policy')], order='id desc')
            #     ss+=sss
            #     s=ss._attachment_format()
            #     res['attachments'] = s
            # elif thread._name=='insurance.claim.bundle':
            #     ss=thread.env['ir.attachment'].search([('res_id', '=', thread.id), 
            #                                                          ('res_model', '=', thread._name)], order='id desc')
            #     sss=thread.env['ir.attachment'].search([('res_id', 'in', thread.required_material_line.ids), 
            #                                                          ('res_model', '=', 'insurance.claim.bundle.required.material.line')], order='id desc')
            #     ss+=sss
            #     s=ss._attachment_format()
            #     res['attachments'] = s
            # elif thread._name=='insurance.claim.guarantee':
            #     ss=thread.env['ir.attachment'].search([('res_id', '=', thread.id), 
            #                                                          ('res_model', '=', thread._name)], order='id desc')
            #     sss=thread.env['ir.attachment'].search([('res_id', 'in', thread.required_material_line.ids), 
            #                                                          ('res_model', '=', 'insurance.claim.required.material.line')], order='id desc')
            #     ss+=sss
            #     s=ss._attachment_format()
            #     res['attachments'] = s
            # else:
            res['attachments'] = thread.env['ir.attachment'].search([('res_id', '=', thread.id), 
                                                                    ('res_model', '=', thread._name)], order='id desc')._attachment_format()
        return thread._get_mail_thread_data(request_list)