
# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api

class ContractAmountReport(models.Model):
	_name = 'contract.amount.report'
	_description = 'Contract Amount Report'
	_auto = False
	_order='id'

	id=fields.Many2one('contract.real.payment.line', 'Гэрээний мөр',readonly=True)
	line_id=fields.Many2one('contract.real.payment.line', 'Гэрээний мөр',readonly=True)
	contract_id=fields.Many2one('contract.document.real', 'Гэрээ',readonly=True)
	date_from = fields.Date('Эхлэх огноо',tracking=True)
	date_to = fields.Date('Дуусах огноо',tracking=True)
	disburse_date = fields.Date('Төлсөн огноо')
	paid_date = fields.Date('Төлөх огноо')
	disburse_amount = fields.Float('Төлсөн дүн')
	paid_amount = fields.Float('Төлөх дүн')
	amount_balance = fields.Float('Нийт үлдэгдэл дүн')
	amount_paid = fields.Float('Нийт төлсөн дүн')
	amount_total = fields.Float('Нийт гэрээний дүн')
	partner_id = fields.Many2one('res.partner','Харилцагч',tracking=True)
	pay_sel = fields.Selection([('yes','Нийлүүлэгч'),('no','Захиалагч')],'Гэрээнд оролцох хэлбэр',tracking=True)
	payment_type = fields.Selection([('type1','Үнийн дүнтэй'),('type2','Үнийн дүнгүй'),('type3','Тооцоо нийлснээр'),('type4','Бартераар')],'Төлбөрийн хэлбэр',tracking=True)
	process_type = fields.Selection([('processing','Хэрэгжиж буй'),('closed','Хаагдсан'),('canceled','Цуцлагдсан'),('warrenty','Баталгаат хугацаа')],'Гэрээний явцын төлөв',tracking=True)


	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self._cr.execute("""
			CREATE or REPLACE view  %s as
			SELECT 
				con.id as contract_id,
				con.amount_balance as amount_balance,
				con.amount_paid as amount_paid,
				con.payment_sum as amount_total,
				con.date_from as date_from,		 
		        con.date_to as date_to,		 
		        con.partner_id as partner_id,		 
                con.pay_sel as pay_sel,	
		   		con.payment_type as payment_type,		 
		   		con.process_type as process_type,		 
				line.id as id,
				line.id as line_id,
				line.disburse_date as disburse_date,
				line.disburse_amount as disburse_amount,
				line.paid_date as paid_date,
				line.paid_amount as paid_amount
			FROM contract_real_payment_line line
			LEFT JOIN contract_document_real con ON con.id=line.contract_amount_graph_id
			WHERE con.payment_type in ('type1','type3')
			ORDER by id
			"""% (self._table))
		
