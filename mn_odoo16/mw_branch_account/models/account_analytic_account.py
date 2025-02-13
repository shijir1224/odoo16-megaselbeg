# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    branch_id = fields.Many2one('res.branch', 'Branch')


    # @api.depends('line_ids')
    # def _compute_invoice_count(self):
    #     sale_types = self.env['account.move'].get_sale_types(include_receipts=True)
    #
    #     query = self.env['account.move.line']._search([
    #         ('parent_state', '=', 'posted'),
    #         ('move_id.move_type', 'in', sale_types),
    #     ])
    #     query.add_where(
    #         'account_move_line.analytic_distribution ?| %s',
    #         [[str(account_id) for account_id in self.ids]],
    #     )
    #
    #     query.order = None
    #     query_string, query_param = query.select(
    #         'jsonb_object_keys(account_move_line.analytic_distribution) as account_id',
    #         'COUNT(DISTINCT(account_move_line.move_id)) as move_count',
    #     )
    #     query_string = f"{query_string} GROUP BY jsonb_object_keys(account_move_line.analytic_distribution)"
    #
    #     self._cr.execute(query_string, query_param)
    #     data = {int(record.get('account_id')): record.get('move_count') for record in self._cr.dictfetchall()}
    #     for account in self:
    #         account.invoice_count = data.get(account.id, 0)
