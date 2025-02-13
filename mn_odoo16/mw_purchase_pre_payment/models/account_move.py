from odoo.models import Model
from odoo import fields, api

class AccountMove(Model):
	_inherit = 'account.move'

	purchase_initial_invoice_line_id = fields.Many2one('purchase.initial.invoice.line', ondelete='set null')
	prepayment_count = fields.Integer(string='Урьдчилгаа төлбөр', compute='_prepayment_count')
	def button_cancel(self):
		if self.mapped('purchase_initial_invoice_line_id'):
			self.mapped('purchase_initial_invoice_line_id').to_cancel()
		return super(AccountMove, self).button_cancel()

	def button_draft(self):
		if self.mapped('purchase_initial_invoice_line_id'):
			self.mapped('purchase_initial_invoice_line_id').to_invoice_created()
		return super(AccountMove, self).button_draft()

	def _prepayment_count(self):
		for move in self:
			# if move.state != 'posted' :
			# 	print('posted')
			# 	continue
			# if move.payment_state not in ('not_paid', 'partial'):
			# 	print('payment_state')
			# 	continue
			# if not move.is_invoice(include_receipts=True):
			# 	print('is_invoice')
			# 	continue
			account_ids =  self.env['account.account'].search([
				('account_type', '=', 'asset_prepayments'),
				])
			domain = [
				('account_id', 'in', account_ids.ids),
				('parent_state', '=', 'posted'),
				('partner_id', '=', move.commercial_partner_id.id),
				('reconciled', '=', False),
				'|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
				]
			res = self.env['account.move.line'].search_count([('id', 'in', self.env['account.move.line'].search(domain).mapped('id'))])
			# res = 0
			move.prepayment_count = res if res else 0

	def compute_payments_purchase_prepayments(self):
		for move in self:
			if move.state != 'posted' \
					or move.payment_state not in ('not_paid', 'partial') \
					or not move.is_invoice(include_receipts=True):
				continue

			account_ids =  self.env['account.account'].search([
				('account_type', '=', 'asset_prepayments'),
				])
			domain = [
				('account_id', 'in', account_ids.ids),
				('parent_state', '=', 'posted'),
				('partner_id', '=', move.commercial_partner_id.id),
				('reconciled', '=', False),
				'|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
				]
			action = self.env.ref('account.action_account_moves_all').read()[0]
			action['domain'] = ['|',('id','in', self.env['account.move.line'].search([('move_id','=',self.id),('account_id.account_type','in',('asset_receivable','liability_payable'))]).mapped('id')),('id','in', self.env['account.move.line'].search(domain).mapped('id'))]
			action['context'] = {}
			return action
