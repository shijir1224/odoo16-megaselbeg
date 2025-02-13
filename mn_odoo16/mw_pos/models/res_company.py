# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResCompany(models.Model):
    _inherit = "res.company"
 
    ebarimt_endpoint_url = fields.Char('EBarimt URL', default='https://services.elibrary.mn/noatus/put?lib=')
    ebarimt_customer_check_url = fields.Char( string='EBarimt Partner Check URL', default='http://info.ebarimt.mn/rest/merchant/info?regno=')
