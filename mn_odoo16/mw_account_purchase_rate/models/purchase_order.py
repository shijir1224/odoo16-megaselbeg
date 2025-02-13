from odoo.models import Model


class PurchaseOrder(Model):
    _inherit = 'purchase.order'

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        if self.currency_id != self.company_id.currency_id and self.current_rate:
            res.update({'rate_manual': True,
                        'rate_manual_amount': self.current_rate})
        return res

    def prepare_invoice_vals(self, reference_val, currency_id, partner, journal_ids, name, invoice_date, invoice_line, n):
        res = super(PurchaseOrder, self).prepare_invoice_vals(reference_val, currency_id, partner, journal_ids, name, invoice_date, invoice_line, n)
        if currency_id != self.company_id.currency_id and self.current_rate:
            res.update({'rate_manual': True,
                        'rate_manual_amount': self.current_rate})
        return res
