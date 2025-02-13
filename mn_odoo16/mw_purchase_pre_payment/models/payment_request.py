from datetime import date
from odoo.exceptions import UserError
from odoo.models import Model
from odoo import fields

class PaymentRequest(Model):
	_inherit = 'payment.request'

	purchase_initial_invoice_line = fields.Many2one('purchase.initial.invoice.line',
													string='Purchase initial invoice', ondelete='cascade')

	def unlink(self):
		for obj in self:
			if obj.purchase_initial_invoice_line:
				raise UserError('Худалдан авалтын урьдчилгаа төлбөрөөс үүссэн байна.\nУрьдчилгаанаасаа устгана уу.')
		return super(PaymentRequest, self).unlink()

	def create_payment(self, form):
		res = super(PaymentRequest, self).create_payment(form)
		for obj in self:
			if obj.purchase_initial_invoice_line:
				obj.purchase_initial_invoice_line.date = date.today()
				obj.purchase_initial_invoice_line.change_currency_rate()
		return res
