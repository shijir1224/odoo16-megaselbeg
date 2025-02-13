# -*- coding: utf-8 -*-
from odoo import models
from datetime import date


class PurchaseOrderExpenses(models.Model):
    _inherit = 'purchase.order.expenses'

    def get_invoice_values(self, journal_id, partner, company_id, currency_id, n):
        res = super(PurchaseOrderExpenses, self).get_invoice_values(journal_id, partner, company_id, currency_id, n)
        # purchase_order = self.mapped('order_id')[0]
        purchase_order = (self.order_id and self.order_id) \
			or (self.purchase_lines and self.purchase_lines[0].order_id)\
			 or (self.add_cost_id.po_line_ids and self.add_cost_id.po_line_ids[0].order_id)
        rate = self.mapped('current_cur')[0]
        if not currency_id == purchase_order.currency_id:
            res.update({'rate_manual_amount': rate, 'rate_manual': True,})
        return res
