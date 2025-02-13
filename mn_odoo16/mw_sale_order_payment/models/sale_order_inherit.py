# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

MAP_INVOICE_TYPE_PARTNER_TYPE = {
	'out_invoice': 'customer',
	'out_refund': 'customer',
	'out_receipt': 'customer',
	'in_invoice': 'supplier',
	'in_refund': 'supplier',
	'in_receipt': 'supplier',
}

class ResUsers(models.Model):
	_inherit = 'res.users'
    # Columns
	cash_journal_ids = fields.Many2many('account.journal','user_cash_hournal_rel','user_id','journal_id',
		string='Allowed Cash journals',domain=[('type', 'in', ['bank','cash'])])

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	@api.model
	def _get_payment_lines(self):
		lll = []
		for jj in self.env.user.cash_journal_ids:
			vals = { 'journal_id': jj.id }
			pl = self.env['mw.sale.order.payment.line'].create(vals)
			lll.append(pl.id)
		return [(6,0, lll)]

	mw_payment_lines = fields.One2many('mw.sale.order.payment.line', 'order_id', 
		string='Payment lines', default=_get_payment_lines,
# 		states={'done':[('readonly',True)]}
		)
	payment_user_id = fields.Many2one('res.users', string=u'Төлбөр хийсэн', readonly=True)
	p_journal_id = fields.Many2one(related='mw_payment_lines.journal_id', string="Журнал",store=True)	

	def action_invoice_payment_lines(self):
		invoices = self.invoice_ids.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
		residual=sum(invoices.mapped('amount_residual'))
		total_amount=sum(invoices.mapped('amount_total'))
		if not self.invoice_ids or total_amount<self.amount_total:
			# Нэхэмжлэх батлах
			context = {
				"active_model": 'sale.order',
				"active_ids": [self.id],
				"active_id": self.id,
				'open_invoices': False,
			}
			payment = self.env['sale.advance.payment.inv'].with_context(context).create({
				'advance_payment_method': 'delivered',
				'deduct_down_payments':True
			})
			payment.with_context(context).create_invoices()
			self.invoice_ids.action_post()
			
		if 'posted' not in self.invoice_ids.mapped('state'):
			raise UserError(('Батлагдсан нэхэмжлэх олдсонгүй!'))

		if self.mw_payment_lines:
			payment_obj = self.env['account.payment']
			for inv in self.invoice_ids.filtered(lambda a: a.state == 'posted' and a.amount_residual>0):
				_logger.info(" ========SO invoice==%s=====\n", inv.name)
				for line in self.mw_payment_lines:
					if line.amount > 0 and not line.is_paid:
						payment_wiz = self.env['account.payment.register'].with_context(active_model='account.move',active_ids=inv.ids).create({
		                        'journal_id': line.journal_id.id,
		                        'amount': abs(line.amount),
		                        'currency_id': inv.currency_id.id,
		                        'payment_date': fields.Date.today(),
		                        'communication': inv.ref})
						res = payment_wiz.action_create_payments()
      # _logger.info(" ========PAYMENT done======= \n\n")
# 						payment_methods = line.journal_id.inbound_payment_method_line_ids
# 						p_vals = {}
# 						p_vals['currency_id'] = inv.currency_id.id
# 						p_vals['partner_type'] = 'inbound'
# 						p_vals['amount'] = abs(line.amount)
# 						p_vals['payment_type'] = 'inbound' if line.amount > 0 else 'outbound'
# 						p_vals['partner_id']= inv.commercial_partner_id.id
# 						p_vals['partner_type'] = MAP_INVOICE_TYPE_PARTNER_TYPE[inv.move_type]
# 						p_vals['move_id'] = inv.id
#       # p_vals['ref'] = (inv.ref or inv.name) + ': '+ (line.note or '')
# 						p_vals['payment_method_id'] = payment_methods and payment_methods[0].id or False
#       # p_vals['journal_id'] = line.journal_id.id
# # 						p_vals['deduct_down_payments'] =True
# 						payment = payment_obj.sudo().create(p_vals)
# 						line.is_paid = True
# 						payment.post()
			# =====================================
			self.payment_user_id = self.env.user.id
		else:
			raise UserError(('Төлбөрийн мэдээллийг оруулна уу!'))
		return

class MwSaleOrderPaymentLine(models.Model):
	_name = 'mw.sale.order.payment.line'
	_description = 'mw.sale.order.payment.line'
	_order = 'journal_id'

	order_id = fields.Many2one('sale.order', string=u'SaleOrder', ondelete='cascade')
	journal_id = fields.Many2one('account.journal', string=u'Журнал', required=True)
	amount = fields.Float(u'Дүн', copy=False, default=0, required=True )
	note = fields.Char(u'Тайлбар', copy=False, )
	is_paid = fields.Boolean(u'Төлөлт хийгдсэн эсэх', copy=False, default=False, readonly=True)
	