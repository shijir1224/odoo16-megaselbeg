# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging



class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	contract_document_id = fields.Many2one('contract.document.real', 'Гэрээ', domain="[('partner_id','=',partner_id)]")


class PurchaseOrder(models.Model):
	_inherit = "purchase.order"

	contract_id = fields.Many2one('contract.document.real', 'Гэрээ', domain="[('partner_id','=',partner_id)]",
								  tracking=True)

	def create_auto_invoice(self, from_purchase_method, picking=False):
		res = super(PurchaseOrder, self).create_auto_invoice(from_purchase_method, picking)
		if res:
			for r in res:
				if self.contract_id:
					for line in r.line_ids:
						line.contract_document_id = self.contract_id.id
		return res


class ContractDocumentReal(models.Model):
	_inherit = "contract.document.real"

	aml_ids = fields.One2many('account.move.line', 'contract_document_id', string=u'Төлсөн төлбөрүүд')
	purchase_ids = fields.One2many('purchase.order', 'contract_id', string=u'Худалдан авалтууд')
	amount_balance = fields.Float('Үлдэгдэл дүн', compute='_compute_amount_balance', store=True)
	amount_paid = fields.Float('Төлсөн дүн', compute='_compute_all', store=True)
	amount_total = fields.Float('Гэрээний дүн',compute='_compute_amount_total', store=True)
	

	@api.depends('payment_line_ids.disburse_amount', 'payment_line_ids')
	def _compute_all(self):
		for item in self:
			item.amount_paid = sum(item.payment_line_ids.mapped('disburse_amount'))

	@api.depends('amount_total', 'amount_paid')
	def _compute_amount_balance(self):
		for item in self:
			item.amount_balance = item.amount_total - item.amount_paid
	

	@api.depends('payment_type', 'payment_line_ids','payment_sum')
	def _compute_amount_total(self):
		for item in self:
			amount_total= 0
			if item.payment_type == 'type3':
				amount_total = sum(item.payment_line_ids.mapped('paid_amount'))
			else:
				amount_total = item.payment_sum
			item.amount_total = amount_total
		   

class ContractRealPaymentLine(models.Model):
	_inherit = 'contract.real.payment.line'

	disburse_date = fields.Date(string=u'Төлсөн огноо сүүлийн', compute='_compute_payment', store=True)
	disburse_amount = fields.Float(string=u'Төлсөн дүн', compute='_compute_payment', store=True)
	line_line_ids = fields.Many2many('contract.real.payment.line.line', string=u'Төлөгдсөн төлбөрүүд',
									 compute='_compute_payment')
	percent = fields.Float('Хувь')
	
				# print('\n\kkkkkkkk')
				# for pp in paid_lines:
				# 	print('\n\n000000',pp)
				# 	co_pay_lines.create({
				# 		'contract_amount_graph_id':pp.contract_document_id.id,
				# 		'paid_date':pp.date,
				# 		'paid_amount':pp.amount,	
				# 		})
				# 	print('\n\co_pay_lines',co_pay_lines)
				# 	pay_lines = co_pay_lines

	@api.onchange('percent')
	def _onchange_percent(self):
		amount = self.contract_amount_graph_id.payment_sum * self.percent/100
		self.paid_amount = amount
	

	@api.depends('contract_amount_graph_id', 'contract_amount_graph_id.aml_ids',
				 'contract_amount_graph_id.aml_ids.debit', 'contract_amount_graph_id.aml_ids.credit', 'paid_amount')
	def _compute_payment(self):
		for item in self:
			paid_lines = self.env['account.move.line'].sudo().search(
				[('id', 'in', item.contract_amount_graph_id.aml_ids.ids)], order='date asc')
			co_pay_lines = self.env['contract.real.payment.line']
			paid_new_lines = []
			for paid in paid_lines:
				paid_new_lines.append({
					'date': paid.date,
					'amount': paid.debit or paid.credit,
				})
			item.disburse_date = False
			item.disburse_amount = 0
			print('\n\dddddd')
			pay_lines = item.contract_amount_graph_id.payment_line_ids
			pay_lines.update({'disburse_amount': 0})
			pay_lines.update({'disburse_date': False})
			line_lines = []
			len_pay_lines = len(pay_lines)
			j = 0
			while (j < len_pay_lines):
				p = pay_lines[j]
				i = 0
				len_lines = len(paid_new_lines)
				while (i < len_lines):
					pa = paid_new_lines[i]
					rate_id = self.env['res.currency.rate'].search(
						[('currency_id', '=', item.contract_amount_graph_id.res_currency_id.id),
						('name', '<=', pa['date'])], order='name desc')
					rate = 1
					if rate_id:
						rate = rate_id[0].rate
					else:
						rate = 1
					pa_amount = pa['amount'] / rate
					while (pa_amount > 0):  # Тухайн мөнгөн дүнг дуустал давтах
						tulsun_dun = p.disburse_amount + pa_amount
						if tulsun_dun > p.paid_amount:  # Мөнгөн дүн төлөх дүнгээс их бол төлөх дүнг шууд авна p.disburse_amount
							save_disburse_amount = p.disburse_amount
							p.disburse_amount = p.paid_amount
							p.disburse_date = pa['date']
							pa_amount = tulsun_dun - p.disburse_amount
							if p == item:
								line_lines.append((0, 0, {
									'aml_date': pa['date'],
									'aml_paid_amount': p.paid_amount - save_disburse_amount,
								}))  # Аль төлөлтөөс дүүргэгдэж байгааг хадгална
							j += 1
							if j >= len_pay_lines:
								break
							p = pay_lines[j]

						else:  # Мөнгөн дүн бага бол тухайн дүнг авна pa_amount
							p.disburse_amount += pa_amount
							p.disburse_date = pa['date']
							if p == item:
								line_lines.append((0, 0, {
									'aml_date': pa['date'],
									'aml_paid_amount': pa_amount,
								}))  # Аль төлөлтөөс дүүргэгдэж байгааг хадгална
							pa_amount = 0
							pa['amount'] = 0
					i += 1
				j += 1
			item.line_line_ids = line_lines


class ContractRealPaymentLineLine(models.Model):
	_name = 'contract.real.payment.line.line'
	_description = "Contract Real Payment Line"

	aml_date = fields.Date('Төлсөн огноо')
	aml_paid_amount = fields.Float('Төлсөн дүн')
