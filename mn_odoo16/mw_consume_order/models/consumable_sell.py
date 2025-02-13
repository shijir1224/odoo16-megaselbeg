# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ConsumableMaterialSell(models.TransientModel):
    _name = 'consumable.material.sell'
    _description = 'Sell Consumable Material'
    _inherit = 'analytic.mixin'

    using_id = fields.Many2one('consumable.material.in.use', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    action = fields.Selection([('sell', 'Sell'), ('dispose', 'Dispose')], required=True, default='sell')
    account_id = fields.Many2one('account.account', string="Account")
    invoice_id = fields.Many2one('account.move', string="Customer Invoice", help="The disposal invoice is needed in order to generate the closing journal entry.", domain="[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]")
    invoice_line_id = fields.Many2one('account.move.line', help="There are multiple lines that could be the related to this asset", domain="[('move_id', '=', invoice_id)]")
    select_invoice_line_id = fields.Boolean(compute="_compute_select_invoice_line_id")
    is_qty = fields.Boolean(string="Тоо хэмжээгээр эсэх", default=False)
    qty = fields.Integer(string="Актлах тоо хэмжээ", default=0)

    date = fields.Date(string="Date")
    gain_or_loss = fields.Selection([('gain', 'Gain'), ('loss', 'Loss'), ('no', 'No')], compute='_compute_gain_or_loss', help="Technical field to know is there was a gain or a loss in the selling of the asset")

    @api.depends('invoice_id', 'action')
    def _compute_select_invoice_line_id(self):
        for record in self:
            record.select_invoice_line_id = record.action == 'sell' and len(record.invoice_id.invoice_line_ids) > 1

    @api.onchange('action')
    def _onchange_action(self):
        if self.action == 'sell' and self.using_id.depreciation_line_ids.filtered(lambda a: a.state in ('draft', 'open')):
            raise UserError("You cannot automate the journal entry for an asset that has a running gross increase. Please use 'Dispose' on the increase(s).")

    @api.depends('using_id', 'invoice_id', 'invoice_line_id')
    def _compute_gain_or_loss(self):
        for record in self:
            line = record.invoice_line_id or len(record.invoice_id.invoice_line_ids) == 1 and record.invoice_id.invoice_line_ids or self.env['account.move.line']
            record.gain_or_loss = 'no'

    def do_action(self):
        self.ensure_one()
        invoice_line = self.env['account.move.line'] if self.action == 'dispose' else self.invoice_line_id or self.invoice_id.invoice_line_ids
        # if self.account_id:
        # else:
        # return self.using_id.set_to_close(invoice_line_id=invoice_line, date=self.date, sell_type=self.action)
        return self.using_id.set_to_close(invoice_line_id=invoice_line, date=self.date, account_id=self.account_id if self.account_id else None, analytic_distribution=self.analytic_distribution if self.analytic_distribution else None, sell_type=self.action)
