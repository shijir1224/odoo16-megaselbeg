# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2014-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _get_default_branch(self):
        user_obj = self.env['res.users']
        branch_id = user_obj.browse(self.env.user.id).branch_id
        return branch_id

    branch_id = fields.Many2one('res.branch', 'Branch', required=True , default=_get_default_branch)
    
    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals = super(sale_order, self)._prepare_invoice()
        invoice_vals['branch_id'] = self.branch_id.id or False
        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res['branch_id'] = self.order_id.branch_id.id or False
        return res
