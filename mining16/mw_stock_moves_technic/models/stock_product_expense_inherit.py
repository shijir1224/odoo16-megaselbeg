# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError

from datetime import datetime, time
import collections
import time
import xlsxwriter
from io import BytesIO
import base64
from datetime import datetime, timedelta

class StockProductOtherExpenseInherit(models.Model):
    _inherit = 'stock.product.other.expense'

    # Columns
    technic_id = fields.Many2one('technic.equipment', u'Техник', copy=False,
        states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})

    # Техник сонгосон бол техникийн move дээр цэнэглэнэ
    def get_prepare_stock_move_line(self, line, sp_id, price_unit, desc, dest_loc):
        vals = super(StockProductOtherExpenseInherit, self).get_prepare_stock_move_line(line, sp_id, price_unit, desc, dest_loc)
        vals['technic_id2'] = self.technic_id.id or False
        return vals

class StockProductOtherExpenseLine(models.Model):
    _inherit = 'stock.product.other.expense.line'

    technic_id = fields.Many2one(related='parent_id.technic_id')

    @api.depends('parent_id', 'parent_id.analytic_distribution', 'product_id', 'parent_id.transaction_value_id')
    def _compute_analytic_mining_distribution(self):
        for line in self:
            print ('linelineine: ',line.parent_id, line.parent_id.transaction_value_id)
            if line.parent_id and line.parent_id.analytic_distribution:
                line.analytic_distribution = line.parent_id.analytic_distribution
            if line.parent_id and line.parent_id.transaction_value_id:
                line.account_id = line.parent_id.transaction_value_id.account_id.id if line.parent_id.transaction_value_id else False
            if line.parent_id.technic_id:
                config_id = self.env['product.account.config'].search([('technic_ids','in',line.parent_id.technic_id.id)], limit=1)
                line.account_id = config_id.account_id.id