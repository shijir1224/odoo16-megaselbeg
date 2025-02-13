# -*- coding: utf-8 -*-

from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from functools import lru_cache

class account_invoice(models.Model):
    _inherit = 'account.move'

    rate_date = fields.Date('Puchase date',readonly=True, copy=False,
        states={'draft': [('readonly', False)]},)#store=True,  compute='_compute_rate_date',
    rate_manual = fields.Boolean('Manual rate?',readonly=True, copy=False,
        states={'draft': [('readonly', False)]},)
    rate_manual_amount = fields.Float('Manual rate',readonly=True, copy=False,
        states={'draft': [('readonly', False)]},)


class account_invoice_line(models.Model):
    _inherit = 'account.move.line'


    @api.depends('currency_id', 'company_id', 'move_id.date','move_id.rate_date','move_id.rate_manual_amount')
    def _compute_currency_rate(self):
        @lru_cache()
        def get_rate(from_currency, to_currency, company, date):
            rate=0
            if self.move_id.rate_manual and self.move_id.rate_manual_amount:
                rate = 1/self.move_id.rate_manual_amount
            elif self.move_id.rate_date:
                date= self.move_id.rate_date
                rate = self.env['res.currency']._get_conversion_rate(
                    from_currency=from_currency,
                    to_currency=to_currency,
                    company=company,
                    date=date,
                )
            else:
                rate=self.env['res.currency']._get_conversion_rate(
                    from_currency=from_currency,
                    to_currency=to_currency,
                    company=company,
                    date=date,
                )
            return rate
        
        for line in self:
            if line.currency_id:
                rr=get_rate(
                    from_currency=line.company_currency_id,
                    to_currency=line.currency_id,
                    company=line.company_id,
                    date=line.move_id.invoice_date or line.move_id.date or fields.Date.context_today(line),
                )
                line.currency_rate = rr
            else:
                line.currency_rate = 1

            
