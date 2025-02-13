# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class PosSessionInherit(models.Model):
    _inherit = 'pos.session'

    def _loader_params_pos_payment_method(self):
        result = super()._loader_params_pos_payment_method()
        result['search_params']['fields'].append('dtb_go_conn_payment_identifier')
        return result

    go_conn_description = fields.Text(string='DTB go conn description', readonly=True)
    go_conn_sale_count = fields.Float(string='DTB go conn sale_count', default=0, readonly=True)
    go_conn_sale_total = fields.Float(string='DTB go conn sale_total', default=0, readonly=True)
    go_conn_void_count = fields.Float(string='DTB go conn void_count', default=0, readonly=True)
    go_conn_void_total = fields.Float(string='DTB go conn void_total', default=0, readonly=True)
