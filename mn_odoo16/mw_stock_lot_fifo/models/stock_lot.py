# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class StockLot(models.Model):
    _inherit = 'stock.lot'
    _order = 'product_id, company_id'

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    expiration_date = fields.Datetime(related='lot_id.expiration_date', store=True, readonly=True)

    @api.model
    def _get_removal_strategy_order(self, removal_strategy):
        if removal_strategy == 'fefo':
            return 'expiration_date, in_date, id'
        return super(StockQuant, self)._get_removal_strategy_order(removal_strategy)