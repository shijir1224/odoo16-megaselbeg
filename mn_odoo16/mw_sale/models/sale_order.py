# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    search_invoice_id = fields.Many2one('account.move', string='Нэхэмжлэх ID', store=False)
    uldegdel_tulbur = fields.Float(string='Үлдэгдэл төлбөр', compute='com_uldegdel_tulbur', store=True, tracking=True)
    tulsun_tulbur = fields.Float(string='Төлсөн төлбөр', compute='com_tulsun_tulbur', store=True, tracking=True)
    invoice_dates = fields.Char(string='Нэхэмжлэх огноо', compute='com_invoice_dates', store=True, tracking=True)

    @api.depends('invoice_ids','invoice_ids.invoice_date')
    def com_invoice_dates(self):
        for item in self:
            dd = [str(x.invoice_date)+' '+str(x.display_name) for x in item.invoice_ids]
            item.invoice_dates = '\n'.join(dd)

    @api.depends('invoice_ids','invoice_ids.amount_residual','amount_total','state')
    def com_tulsun_tulbur(self):
        for item in self:
            if item.invoice_ids:
                item.tulsun_tulbur = item.amount_total - sum(item.invoice_ids.mapped('amount_residual'))
            else:
                item.tulsun_tulbur = 0 

    @api.depends('invoice_ids','invoice_ids.amount_residual')
    def com_uldegdel_tulbur(self):
        for item in self:
            item.uldegdel_tulbur = sum(item.invoice_ids.mapped('amount_residual'))

    def action_cancel(self):
        return self._action_cancel()
