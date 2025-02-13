# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections
from calendar import monthrange
import logging
from odoo.tools import float_is_zero, float_compare, pycompat

_logger = logging.getLogger(__name__)

MAP_INVOICE_TYPE_PARTNER_TYPE = {
	'out_invoice': 'customer',
	'out_refund': 'customer',
	'in_invoice': 'supplier',
	'in_refund': 'supplier',
}

class SalePaymentInfo(models.Model):
	_name = 'sale.payment.info'
	_description = "sale payment info"

	name = fields.Char('Number', required=True, copy=True)
	date = fields.Datetime('Created date', readonly=True, default=fields.Datetime.now(), copy=False)
	date_start = fields.Date('Start date', copy=True, required=True)
	date_end = fields.Date('End date', copy=True, required=True)
	partner_id = fields.Many2one('res.partner', 'Partner', required=True)
	note = fields.Text('Note', )
	
	so_id = fields.Many2one('sale.order', 'SO', )
	pay_amount = fields.Float('Amount',)
#	 journal_id = fields.Many2one('account.partner', 'Partner', required=True)
	
	def compute_partner_sale_payment(self):
#		res1 = self._compute_partner_sale_payment(partner_id=self.partner_id.id,date_start=self.date_start,date_end=self.date_end)
#		print 'res1 ',res1
#		 _logger.info(u'===========payment---res1----\n%s: '%(res1))	
#		 res = self._compute_sale_payment_by_method(partner_id=self.partner_id.id,date_start=self.date_start,date_end=self.date_end)
# #		 print 'res ',res
#		 _logger.info(u'===========payment-------\n%s: '%(res))	

		return True
	
		data={'date':'2018-10-10','partner_id':False}
		_logger.info("------ mobile -----get_payment_so_list %s  %s", str(data), type(data))
		sale_orders = []
		sale_obj = self.env['sale.order']
		m_date = data['date'][:7]+'%'
		current_date = data['date']
		sdate = data['date'].split('-')[0]+'-'+data['date'].split('-')[1]+'-01'
		edate = data['date'].split('-')[0]+'-'+data['date'].split('-')[1]+'-'+str(monthrange(int(data['date'].split('-')[0]), int(data['date'].split('-')[1]))[1])
		_logger.info("------ mobile ----- **** sdate: %s  edate: %s", sdate, edate)
		_logger.info("------ mobile ----- **** part: %d %s", data['partner_id'], m_date)
		pay_obj=self.env['sale.payment.info']
		acc_pay_obj=self.env['account.payment']
		so_ids = sale_obj.search([
#								   ('validity_date','=',current_date),
								  ('user_id','=',self.env.user.id)
								  ])
		pay_obj=self.env['sale.payment.info']
		for so in so_ids:
			invoice_ids = so.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
		payments = pay_obj._compute_partner_user_so_payment(False,sdate,edate,so_ids)	
		
		
		return payments
	
	def _compute_partner_sale_payment(self,partner_id,date_start,date_end,account_ids=False):
		_logger.info(u'payment-------\n')	
#		 sql_query = """SELECT ipr.invoice_id,sum(aml.credit) as amount,aml.date,so.id 
#						 FROM account_invoice_payment_rel ipr 
#							 left join 
#								 account_move_line aml on aml.payment_id=ipr.payment_id 
#							 left join 
#								 sale_order_line_invoice_rel slr on slr.invoice_line_id=ipr.invoice_id 
#							 left join 
#								 sale_order_line sol on slr.order_line_id=sol.id 
#							 left join 
#								 sale_order so on sol.order_id=so.id 
#						 WHERE aml.date>=%s AND aml.date<=%s  
#							 AND aml.partner_id = %s 
#				 """
#				 
#		 params = (date_start,date_end,partner_id,)
#		 if account_ids:
#			 sql_query += ' AND aml.account_id IN %s'
#			 params += (tuple(account_ids),)
# #		 else:
# #			 sql_query += ' AND aml.account_id IN (select id from account_account where internal_tye=\'receivable\')'
#		 sql_query += ' group by ipr.invoice_id,aml.date,so.id'
#		 print 'sql_query ',sql_query
#		 self.env.cr.execute(sql_query, params)
#		 res=self.env.cr.dictfetchall()
		partner_ids=[partner_id]
		addr = self.env['res.partner'].browse(partner_id).address_get(['delivery', 'invoice'])
		if addr.get('invoice',False):
			partner_ids.append(addr['invoice'])
#		print 'partner_ids123 ',partner_ids
		res=[]
		payment_obj = self.env['account.payment']
		payment_ids = payment_obj.search([('partner_id','in',partner_ids),
						('payment_date','>=',date_start),
						('payment_date','<=',date_end),
						('state','in',['reconciled','posted'])])
#		 print ('payment_ids ',payment_ids)
		amount=0
		for p in payment_ids:
			order_id=False
			for inv in p.invoice_ids:
				for l in inv.invoice_line_ids:
					for sol in l.sale_line_ids:
						order_id=sol.order_id.id
#						 print 'order_id ',order_id
#						 print 'm.amount ',m.amount
			#2 төлөлт хийсэн бол нийт дүнгээрээ 2 ирж байна
#						 res.append({'so_id':order_id,'amount':(m.debit_move_id.invoice_id.amount_total-m.debit_move_id.invoice_id.residual)})
			res.append({'so_id':order_id,'amount':(p.amount)})			
			amount+=p.amount
#		 aml_obj = self.env['account.move.line']
#		 aml_ids = aml_obj.search([('partner_id','in',partner_ids),
# #						 ('date','>=',date_start),
# #						 ('date','<=',date_end),
#						 ('credit','>',0),])
#		 print ('aml_ids ',aml_ids)
#		 res =[]
#		 for aml in aml_ids:
#			 print ('payment_id ',aml.payment_id.invoice_ids)
#			 print ('aml.matched_debit_ids ',aml.matched_debit_ids)
#			 if aml.matched_debit_ids :
# #				 for m in aml.matched_debit_ids:
#				 for m in aml.matched_debit_ids.filtered(lambda ma: ma.max_date >= date_start and ma.max_date <= date_end):
#					 if m.debit_move_id and m.debit_move_id.move_id:
#						 order_id=False
#						 for l in m.debit_move_id.move_id.invoice_line_ids:
#							 for sol in l.sale_line_ids:
#								 order_id=sol.order_id.id
# #						 print 'order_id ',order_id
# #						 print 'm.amount ',m.amount
#						 #2 төлөлт хийсэн бол нийт дүнгээрээ 2 ирж байна
# #						 res.append({'so_id':order_id,'amount':(m.debit_move_id.invoice_id.amount_total-m.debit_move_id.invoice_id.residual)})
#						 res.append({'so_id':order_id,'amount':(m.amount)})
						
		return res

	check_disc=[]
	
	def _compute_partner_user_so_payment(self,partner_id,date_start,date_end,sos,user_id=False):
		'''Гүйцэтгэл
		'''
		_logger.info(u'payment user-------_compute_partner_user_so_payment \n') 
		query=True
		func=True
		if func:
			func_res=self._compute_sale_payment_function(False,date_start,date_end,[user_id])
			res ={}
#			 print 'func_res ',func_res
			result=0
					
			for r in func_res:
#				 print 'rrr2 ',r
				amount_report=0
				discount=0
				if r['amount_report']:
					amount_report=r['amount_report']
				if r['discount']  and r['p_id'] not in self.check_disc and not r['from_bank']:
					if r['pay_amount']!=r['amount']:
						discount=r['discount']
						self.check_disc.append(r['p_id'])
					
				result+=amount_report - discount

			_logger.info("------ mobile -----result %s  ", str(result))
			return result
										   
		elif query:
			result=0   
			
			if user_id:
#				 sql_query = """
#								 select aml.id as aml_id, aml.debit as debit from 
#										 account_payment p left join 
#										 account_invoice_payment_rel ipr on ipr.payment_id=p.id left join 
#										 account_invoice ai on ai.id=ipr.invoice_id left join
#										 account_invoice_line ail on ai.id=ail.invoice_id left join		
#										 sale_order_line_invoice_rel slr on slr.invoice_line_id=ail.id left join
#										 sale_order_line sol on slr.order_line_id=sol.id		left join 
#										 sale_order so on sol.order_id=so.id	 left join 
#										 account_move_line aml on aml.payment_id=p.id left join	 
#										 account_journal aj on aml.journal_id=aj.id left join	  
#										 account_account a on aml.account_id=a.id
#									   where 
#											 payment_date>=%s
#											 and payment_date<=%s 
#											 and ai.user_id = %s
#											 and p.state in ('posted','reconciled')
#											 and a.internal_type='liquidity'
#									   group by aml.id			   
#				 """
				  # Илүү төлөлт хийсэн бол буруу бодох
#				 sql_query = """
#							 select sum(inv_amount) as inv_amount,sum(debit) as debit from (
#								  --давхар шүүлт
#								  select case when inv_count2=1 and debit>inv_amount 
#								  then debit else inv_amount end as inv_amount,debit from
#								  (
#							 ------
#								select sum(debit) debit,inv_id,count(inv_id),
#								 ----
#							   (select count(distinct invoice_id) from account_invoice_payment_rel where payment_id =p_id) as inv_count2,
#							   -----	
#								(select sum(apr.amount) from  
#									 account_invoice ai left join
#									 account_invoice_account_move_line_rel aiaml on aiaml.account_invoice_id=ai.id left join --payment_move_line_ids 
#									 account_partial_reconcile apr on aiaml.account_move_line_id=apr.credit_move_id--matched_debit_ids
#									 left join
#									 account_move am on ai.move_id=am.id left join
#									 account_move_line aml on aml.move_id=am.id and aml.id=apr.debit_move_id 
#									 where ai.id=inv_id and aml.id notnull) as inv_amount
#								from (
#								select aml.id as aml_id,aml.debit,ai.id as inv_id,p.id as p_id
#									 from 
#									 account_payment p left join 
#									 account_invoice_payment_rel ipr on ipr.payment_id=p.id left join 
#									 account_invoice ai on ai.id=ipr.invoice_id left join
#									 account_invoice_line ail on ai.id=ail.invoice_id left join		
#									 sale_order_line_invoice_rel slr on slr.invoice_line_id=ail.id left join
#									 sale_order_line sol on slr.order_line_id=sol.id		left join 
#									 sale_order so on sol.order_id=so.id	 left join 
#									 account_move_line aml on aml.payment_id=p.id left join	 
#									 account_journal aj on aml.journal_id=aj.id   left join
#									 account_account a on aml.account_id=a.id
#								   where 
#											 payment_date>=%s
#											 and payment_date<=%s 
#											 and ai.user_id = %s
#											 and p.state in ('posted','reconciled')
#											 and a.internal_type='liquidity'
#							   group by aml.id,ai.id,p.id) as foo group by inv_id,p_id order by inv_id desc
# 
#									 --давхар шүүлт
#									 ) as foo2
# 
#							   ) as baar
#				 """
#				 params = (date_start,date_end,user_id)
# #				 print 'sql_query ',sql_query
#				 self.env.cr.execute(sql_query, params)
#				 query_res=self.env.cr.dictfetchall()   
#				 for r in query_res:
# #					print 'rrr2 ',r
#					 if r['inv_amount']>r['debit']:
#						 result+=r['debit'] or 0
#					 else:
#						 result+=r['inv_amount'] or 0
					sql_query = """
								select sum(inv_amount) as inv_amount,sum(debit) as debit,name from (
								 --давхар шүүлт
								 select case when inv_count2=1 and debit>inv_amount 
								 then debit else inv_amount end as inv_amount,debit,name,partner_id from
								 (
							------
							   select sum(debit) debit,inv_id,count(inv_id),
								----
							  (select count(distinct invoice_id) from account_invoice_payment_rel where payment_id =p_id) as inv_count2,
							  -----	
								   (select sum(apr.amount) from  
										account_invoice ai left join
										account_invoice_account_move_line_rel aiaml on aiaml.account_invoice_id=ai.id left join --payment_move_line_ids 
										account_partial_reconcile apr on aiaml.account_move_line_id=apr.credit_move_id--matched_debit_ids
										left join
										account_move am on ai.move_id=am.id left join
										account_move_line aml on aml.move_id=am.id and aml.id=apr.debit_move_id 
										where ai.id=inv_id and aml.id notnull) as inv_amount,name,partner_id
								   from (
								   select aml.id as aml_id,aml.debit,ai.id as inv_id , 
										   aj.name as name,p.id as p_id,p.partner_id as partner_id
										from 
										account_payment p left join 
										account_invoice_payment_rel ipr on ipr.payment_id=p.id left join 
										account_invoice ai on ai.id=ipr.invoice_id left join
										account_invoice_line ail on ai.id=ail.invoice_id left join		
										sale_order_line_invoice_rel slr on slr.invoice_line_id=ail.id left join
										sale_order_line sol on slr.order_line_id=sol.id		left join 
										sale_order so on sol.order_id=so.id	 left join 
										account_move_line aml on aml.payment_id=p.id left join	 
										account_journal aj on aml.journal_id=aj.id   left join
										account_account a on aml.account_id=a.id
									  where 
												payment_date>=%s
												and payment_date<=%s 
												and ai.user_id = %s
												and p.state in ('posted','reconciled')
												--and p.partner_id in 
												and a.internal_type='liquidity'												
								  group by aml.id,ai.id, aj.name,p.id,p.partner_id) as foo group by inv_id,name,p_id,partner_id order by inv_id desc
									 ) as foo2
								  ) as baar group by name,partner_id
					"""
					params = (date_start,date_end,user_id)
#					 params = (date_start,date_end,user_id)
#					 print 'sql_query ',sql_query
					self.env.cr.execute(sql_query, params)
					query_res=self.env.cr.dictfetchall()   
					res ={}
					for r in query_res:
#						print 'rrr2 ',r
						if r['inv_amount']>r['debit']:
							result+=r['debit'] or 0
						else:
							result+=r['inv_amount'] or 0
	
			_logger.info("------ mobile -----result %s  ", str(result))
			return result
		else:
			invoice_ids=False
			result=0
			if sos:
				for so in sos:
					invoice_id = so.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
					if not invoice_ids:
						invoice_ids=invoice_id
					else:
						invoice_ids+=invoice_id
	 
			aml_obj = self.env['account.move.line']
			payment_obj = self.env['account.payment']
			payments_all={}
			so_amount=0
			if invoice_ids:
				for inv in invoice_ids:
					for pay in  inv.payment_move_line_ids.filtered(lambda r: 
																	   r.date >=date_start and
																	   r.date<=date_end):
						 
		#				 print 'payments_all 1 ',payments_all
						#Нэг төлөлтөөр олон нэхэмжлэхийн төлөлт хийсэн бол
						payment_currency_id = False
						if inv.type in ('out_invoice', 'in_refund'):
							amount = sum([p.amount for p in pay.matched_debit_ids if p.debit_move_id in inv.move_id.line_ids])
							amount_currency = sum(
								[p.amount_currency for p in pay.matched_debit_ids if p.debit_move_id in inv.move_id.line_ids])
							if pay.matched_debit_ids:
								payment_currency_id = all([p.currency_id == pay.matched_debit_ids[0].currency_id for p in
														   pay.matched_debit_ids]) and pay.matched_debit_ids[
														  0].currency_id or False
						elif inv.type in ('in_invoice', 'out_refund'):
							amount = sum(
								[p.amount for p in pay.matched_credit_ids if p.credit_move_id in inv.move_id.line_ids])
							amount_currency = sum([p.amount_currency for p in pay.matched_credit_ids if
												   p.credit_move_id in inv.move_id.line_ids])
							if pay.matched_credit_ids:
								payment_currency_id = all([p.currency_id == pay.matched_credit_ids[0].currency_id for p in
														   pay.matched_credit_ids]) and pay.matched_credit_ids[
														  0].currency_id or False
						# get the payment value in invoice currency
						if payment_currency_id and payment_currency_id == inv.currency_id:
							amount_to_show = amount_currency
						else:
							amount_to_show = pay.company_id.currency_id.with_context(date=inv.date).compute(amount,
																													inv.currency_id)
						if float_is_zero(amount_to_show, precision_rounding=inv.currency_id.rounding):
							continue	
						result +=amount_to_show
#						 if pay:
#							 so_amount+=inv.amount_total
#						 if not payments_all.get(pay.journal_id.name,False):
#								 payments_all[pay.journal_id.name]={
#	 #																 'amount':pay.credit,
#																	 'amount':amount_to_show,
#																	'move_ids':[pay.id],
#																	'partner_name':pay.partner_id.name,
#																	'type':pay.journal_id.type}
#						 else:
#							 if not pay.id in payments_all[pay.journal_id.name]['move_ids']:
#	 #							 payments_all[pay.journal_id.name]['amount']+=pay.credit
#								 payments_all[pay.journal_id.name]['amount']+=amount_to_show
#								 payments_all[pay.journal_id.name]['move_ids'].append(pay.id)
			 
#			 data_list = []
#			 _logger.info("------ mobile -----so_amount %s  ", str(so_amount))
#			 _logger.info("------ mobile -----payments_all %s  ", str(payments_all))
#			 for key in payments_all:
#				 data_list.append({'amount':payments_all[key]['amount'],
#								   'journal_name':key,
#								   'partner_name':payments_all[key]['partner_name'],
#								   'type':payments_all[key]['type'],
#								   'so_amount':so_amount
#								   })
			_logger.info("------ mobile -----result %s  ", str(result))
						 
			return result
		
	def _compute_so_payment(self,sos):
			invoice_ids=False
			result=0
			if sos:
				for so in sos:
					invoice_id = so.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
					if not invoice_ids:
						invoice_ids=invoice_id
					else:
						invoice_ids+=invoice_id
	 
			aml_obj = self.env['account.move.line']
			payment_obj = self.env['account.payment']
			payments_all={}
			so_amount=0
			if invoice_ids:
				for inv in invoice_ids:
					for pay in  inv.payment_move_line_ids.filtered(lambda r: 
																	   r.date >=date_start and
																	   r.date<=date_end):
						 
		#				 print 'payments_all 1 ',payments_all
						#Нэг төлөлтөөр олон нэхэмжлэхийн төлөлт хийсэн бол
						payment_currency_id = False
						if inv.type in ('out_invoice', 'in_refund'):
							amount = sum([p.amount for p in pay.matched_debit_ids if p.debit_move_id in inv.move_id.line_ids])
							amount_currency = sum(
								[p.amount_currency for p in pay.matched_debit_ids if p.debit_move_id in inv.move_id.line_ids])
							if pay.matched_debit_ids:
								payment_currency_id = all([p.currency_id == pay.matched_debit_ids[0].currency_id for p in
														   pay.matched_debit_ids]) and pay.matched_debit_ids[
														  0].currency_id or False
						elif inv.type in ('in_invoice', 'out_refund'):
							amount = sum(
								[p.amount for p in pay.matched_credit_ids if p.credit_move_id in inv.move_id.line_ids])
							amount_currency = sum([p.amount_currency for p in pay.matched_credit_ids if
												   p.credit_move_id in inv.move_id.line_ids])
							if pay.matched_credit_ids:
								payment_currency_id = all([p.currency_id == pay.matched_credit_ids[0].currency_id for p in
														   pay.matched_credit_ids]) and pay.matched_credit_ids[
														  0].currency_id or False
						# get the payment value in invoice currency
						if payment_currency_id and payment_currency_id == inv.currency_id:
							amount_to_show = amount_currency
						else:
							amount_to_show = pay.company_id.currency_id.with_context(date=inv.date).compute(amount,
																													inv.currency_id)
						if float_is_zero(amount_to_show, precision_rounding=inv.currency_id.rounding):
							continue	
						result +=amount_to_show
			_logger.info("------ mobile -----result %s  ", str(result))
						 
			return result				

	def _compute_partner_user_so_payment2(self,partner_id,sdate,edate,sos):
#		 data={'date':'2018-09-10','partner_id':self.partner_id.id}
		_logger.info("------ mobile -----sos %s  ", str(sos))
		invoice_ids=False
		if sos:
			for so in sos:
				invoice_id = so.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
				if not invoice_ids:
					invoice_ids=invoice_id
				else:
					invoice_ids+=invoice_id
#			 print 'invoice_ids22 ',invoice_ids.ids

		aml_obj = self.env['account.move.line']
		payment_obj = self.env['account.payment']
#		 payments = payment_obj.search([('invoice_ids','in',invoice_ids.ids)])
#		 aml_ids = aml_obj.search([
# #						 ('partner_id','=',partner_id),
#						 ('date','>=',date_start),
#						 ('date','<=',date_end),
#						 ('payment_id','in',payments.ids),
#						 ('payment_id','in',payments.ids),
#						 ('account_id.internal_type', '=', 'liquidity')						
#						 ])
#		 print 'aml_ids ',aml_ids
		payments_all=[]
		so_amount=0
		users=[]
		
		if self.env.user:
			user_id = self.env.user.id
			_logger.info("------ mobile -----user_id %s  ", str(user_id))
			
			query = """
					select rel.user_id from res_partner_route rpr 
									left join user_route_rel rel on rel.route_id=rpr.id 
								where driver_id ={0} group by user_id  
				""".format(user_id)
#						 print 'query11 ',query
			self.env.cr.execute(query)
			query_result = self.env.cr.dictfetchall()						
#						 print 'query_result ',query_result
			for r in query_result:
				users.append(r['user_id'])			 
		_logger.info("------ mobile -----users %s  ", str(users))
		if invoice_ids:
			for inv in invoice_ids:
	#			 inv.payment_move_line_ids:
				for pay in  inv.payment_move_line_ids.filtered(lambda r: 
																   r.date >=sdate and
																   r.date<=edate):
					
	#				 print 'payments_all 1 ',payments_all
					order_id=False
					for l in inv.invoice_line_ids:
						for sol in l.sale_line_ids:
							order_id=sol.order_id
	#						 print 'order_id ',order_id
					#2 төлөлт хийсэн бол нийт дүнгээрээ 2 ирж байна
	#						 res.append({'so_id':order_id,'amount':(m.debit_move_id.invoice_id.amount_total-m.debit_move_id.invoice_id.residual)})
	#				 res.append({'so_id':order_id,'amount':(m.amount)})
					if users:
						if order_id and order_id.user_id.id in users:  
							if pay:
								so_amount+=inv.amount_total
							payments_dic={'amount':pay.credit,
			#								'move_ids':[pay.id],
										   'partner_name':pay.partner_id.name,
										   'type':pay.journal_id.type,
										   'journal_name':pay.journal_id.short_name,
										   # 'journal_name':pay.journal_id.name,
										   'so_id':order_id.id,
										   'so_amount':inv.amount_total}
								
							payments_all.append(payments_dic)
							_logger.info("------ mobile -----payments_all111 %s  ", str(payments_all))

#				 if not payments_all.get(pay.journal_id.name,False):
#						 payments_all[pay.journal_id.name]={'amount':pay.credit,
#															'move_ids':[pay.id],
#															'partner_name':pay.partner_id.name,
#															'type':pay.journal_id.type}
#				 else:
#					 if not pay.id in payments_all[pay.journal_id.name]['move_ids']:
#						 payments_all[pay.journal_id.name]['amount']+=pay.credit
#						 payments_all[pay.journal_id.name]['move_ids'].append(pay.id)
	
#		 data_list = []
#		 _logger.info("------ mobile -----so_amount %s  ", str(so_amount))
#		 for key in payments_all:
#			 data_list.append({'amount':payments_all[key]['amount'],
#							   'journal_name':key,
#							   'partner_name':payments_all[key]['partner_name'],
#							   'type':payments_all[key]['type'],
#							   'so_amount':so_amount
#							   })
#		 _logger.info("------ mobile -----data_list %s  ", str(data_list))
		return payments_all

	def _compute_sale_payment_function(self,partners,date_start,date_end,user_ids=False,inv_partner=False,invoices=False,is_group=False,is_init=False):
		if user_ids:
			if is_init:
				
				if partners:
					where_inv=''
					sql_query = """
						select p.amount as pay_amount,apr.amount,aml.debit,aml.credit,aml.id,apr.id,ai.id ai_id,aj.name,p.is_more,p.discount,
								case when p.is_more then (select credit from account_move_line where id=apr.credit_move_id)--p.credit_move_id.credit
								else apr.amount end as amount_report,p.id as p_id,p.with_discount,p.from_bank
								from  
								account_invoice ai left join
								account_invoice_account_move_line_rel aiaml on aiaml.account_invoice_id=ai.id left join --payment_move_line_ids 
								account_move_line aml on aiaml.account_move_line_id=aml.id left join--and aml.id=apr.debit_move_id 
								account_partial_reconcile apr on aml.id=apr.credit_move_id--matched_debit_ids
										and apr.debit_move_id in (select id from account_move_line aml2 where move_id=ai.move_id)--inv.move_id.line_ids
										left join
								account_payment p on p.id=aml.payment_id left join
								account_journal aj on aml.journal_id=aj.id 
						
						--		left join
						--		account_move am on ai.move_id=am.id left join
						--		account_move_line aml on aml.move_id=am.id and aml.id=apr.debit_move_id 
								where 
								aml.date<%s
								and ai.user_id in %s
								and p.partner_id in %s
								and p.state in ('posted','reconciled')
								"""+where_inv+"\
								order by ai.id  "  
		#			if 12686 in partners:
		#				print 'sql_query ',sql_query
		#			 print 'user_ids',user_ids
		#			 print 'partners ',partners
					params = (date_start,tuple(user_ids),tuple(partners))
			#					 params = (date_start,date_end,user_id)
					self.env.cr.execute(sql_query, params)
					query_res=self.env.cr.dictfetchall() 
			else:
				if partners:
					where_inv=''
		#			 if invoices:
		#				 print 'invoices ',invoices
		#				 if len(invoices)==1:
		#					 where_inv=" AND ai.id ={0}".format(invoices[0])
		#				 elif len(invoices)>1:
		#					 where_inv=" AND ai.id in {0}".format(tuple(invoices))#Групп бол нэг мөрөнд гаргачвал болох байжэээ
		#			 print 'where_inv ',where_inv
					sql_query = """
						select p.amount as pay_amount,apr.amount,aml.debit,aml.credit,aml.id,apr.id,ai.id ai_id,aj.name,p.is_more,p.discount,
								case when p.is_more then (select credit from account_move_line where id=apr.credit_move_id)--p.credit_move_id.credit
								else apr.amount end as amount_report,p.id as p_id,p.with_discount,p.from_bank
								from  
								account_invoice ai left join
								account_invoice_account_move_line_rel aiaml on aiaml.account_invoice_id=ai.id left join --payment_move_line_ids 
								account_move_line aml on aiaml.account_move_line_id=aml.id left join--and aml.id=apr.debit_move_id 
								account_partial_reconcile apr on aml.id=apr.credit_move_id--matched_debit_ids
										and apr.debit_move_id in (select id from account_move_line aml2 where move_id=ai.move_id)--inv.move_id.line_ids
										left join
								account_payment p on p.id=aml.payment_id left join
								account_journal aj on aml.journal_id=aj.id 
						
						--		left join
						--		account_move am on ai.move_id=am.id left join
						--		account_move_line aml on aml.move_id=am.id and aml.id=apr.debit_move_id 
								where 
								aml.date>=%s
								and aml.date<=%s 
								and ai.user_id in %s
								and p.partner_id in %s
								and p.state in ('posted','reconciled')
								"""+where_inv+"\
								order by ai.id  "  
		#			if 12686 in partners:
		#				print 'sql_query ',sql_query
		#			 print 'user_ids',user_ids
		#			 print 'partners ',partners
					params = (date_start,date_end,tuple(user_ids),tuple(partners))
			#					 params = (date_start,date_end,user_id)
					self.env.cr.execute(sql_query, params)
					query_res=self.env.cr.dictfetchall() 
				else:
					sql_query = """
						select p.amount as pay_amount,apr.amount,aml.debit,aml.credit,aml.id,apr.id,ai.id ai_id,aj.name,p.is_more,p.discount,
								case when p.is_more then (select credit from account_move_line where id=apr.credit_move_id)--p.credit_move_id.credit
								else apr.amount end as amount_report,p.id as p_id,p.with_discount,p.from_bank
								from  
								account_invoice ai left join
								account_invoice_account_move_line_rel aiaml on aiaml.account_invoice_id=ai.id left join --payment_move_line_ids 
								account_move_line aml on aiaml.account_move_line_id=aml.id left join--and aml.id=apr.debit_move_id 
								account_partial_reconcile apr on aml.id=apr.credit_move_id--matched_debit_ids
										and apr.debit_move_id in (select id from account_move_line aml2 where move_id=ai.move_id)--inv.move_id.line_ids
										left join
								account_payment p on p.id=aml.payment_id left join
								account_journal aj on aml.journal_id=aj.id 
						
						--		left join
						--		account_move am on ai.move_id=am.id left join
						--		account_move_line aml on aml.move_id=am.id and aml.id=apr.debit_move_id 
								where 
								aml.date>=%s
								and aml.date<=%s 
								and ai.user_id in %s
								and p.state in ('posted','reconciled')
								order by ai.id		
					"""
					params = (date_start,date_end,tuple(user_ids))
			#					 params = (date_start,date_end,user_id)
		#			print 'sql_query11 ',sql_query
					self.env.cr.execute(sql_query, params)
					query_res=self.env.cr.dictfetchall() 
		else:
			if partners:
				where_inv=''
	#			 if invoices:
	#				 print 'invoices ',invoices
	#				 if len(invoices)==1:
	#					 where_inv=" AND ai.id ={0}".format(invoices[0])
	#				 elif len(invoices)>1:
	#					 where_inv=" AND ai.id in {0}".format(tuple(invoices))#Групп бол нэг мөрөнд гаргачвал болох байжэээ
	#			 print 'where_inv ',where_inv
				sql_query = """
					select p.amount as pay_amount,apr.amount,aml.debit,aml.credit,aml.id,apr.id,ai.id ai_id,aj.name,p.is_more,p.discount,
							case when p.is_more then (select credit from account_move_line where id=apr.credit_move_id)--p.credit_move_id.credit
							else apr.amount end as amount_report,p.id as p_id,p.with_discount,p.from_bank
							from  
							account_invoice ai left join
							account_invoice_account_move_line_rel aiaml on aiaml.account_invoice_id=ai.id left join --payment_move_line_ids 
							account_move_line aml on aiaml.account_move_line_id=aml.id left join--and aml.id=apr.debit_move_id 
							account_partial_reconcile apr on aml.id=apr.credit_move_id--matched_debit_ids
									and apr.debit_move_id in (select id from account_move_line aml2 where move_id=ai.move_id)--inv.move_id.line_ids
									left join
							account_payment p on p.id=aml.payment_id left join
							account_journal aj on aml.journal_id=aj.id 
					
					--		left join
					--		account_move am on ai.move_id=am.id left join
					--		account_move_line aml on aml.move_id=am.id and aml.id=apr.debit_move_id 
							where 
							aml.date>=%s
							and aml.date<=%s 
							and p.partner_id in %s
							and p.state in ('posted','reconciled')
							"""+where_inv+"\
							order by ai.id  "  
	#			if 12686 in partners:
	#				print 'sql_query ',sql_query
	#			 print 'user_ids',user_ids
	#			 print 'partners ',partners
				params = (date_start,date_end,tuple(partners))
		#					 params = (date_start,date_end,user_id)
				self.env.cr.execute(sql_query, params)
				query_res=self.env.cr.dictfetchall()						  
		return query_res	   
		   
	def _compute_sale_payment_by_method(self,partner_id,date_start,date_end,user_ids=False,inv_partner=False,is_group=False):
		'''ХНТ
		'''
		_logger.info(u'payment------- start \n')	
#		 print 'user_ids ',user_ids
	
		partners=[]
		for i in inv_partner:
			partners.append(i)
#		print 'partners--- ',partners
		partners=set(partners)
		query=True
		func=True
		if func:
			#групп бол нэг мөрөнд гаргавал болох группээр биш бол ашиглах
#			 sql_query = """
#						 select ai.id from account_invoice ai left join 
#									 account_invoice_line ail on ai.id=ail.invoice_id left join		
#									 sale_order_line_invoice_rel slr on slr.invoice_line_id=ail.id left join
#									 sale_order_line sol on slr.order_line_id=sol.id		left join 
#									 sale_order so on sol.order_id=so.id	
#						 where 
#						  ai.user_id in %s
#						 and so.partner_id = %s
#						 and ai.state in ('open','paid')
#						 group by ai.id
#			 """
#			 print 'sql_query1 ',sql_query
#			 params = (tuple(user_ids),partner_id)
#	 #					 params = (date_start,date_end,user_id)
#			 self.env.cr.execute(sql_query, params)
#			 query_res=self.env.cr.fetchall()		
			invoices=[]		   
#			 for i in query_res:
#				 invoices.append(i[0])
			func_res=self._compute_sale_payment_function(partners,date_start,date_end,user_ids,partner_id,invoices)
			res ={}
#			 if 12683 in partners:
			check_disc=[]
			for r in func_res:
				if res.has_key(r['name']):
					amount_report=0
					discount=0
					if r['amount_report']:
						amount_report=r['amount_report']
					if r['discount'] and r['p_id'] not in check_disc and not r['from_bank']:
						if r['pay_amount']!=r['amount']:
							discount=r['discount']
							check_disc.append(r['p_id'])
					# print 'amount_report ',amount_report
					# print 'discount ',discount
					res[r['name']]+=amount_report - discount
#					 res[r['name']]+=r['amount_report'] or 0 -r['discount'] or 0
				else:
					amount_report=0
					discount=0
					if r['amount_report']:
						amount_report=r['amount_report']
					if r['discount'] and r['p_id'] not in check_disc and not r['from_bank']:
						if r['pay_amount']!=r['amount']:#apr.amount p.amount
							discount=r['discount']
							check_disc.append(r['p_id'])
					# print 'amount_report22 ',amount_report
					# print 'discount ',discount
					res[r['name']]=amount_report - discount
		elif query:
#			 aml_obj = self.env['account.move.line']
#			 payment_obj = self.env['account.payment']
#			 args=[
#							 ('payment_date','>=',date_start),
#							 ('payment_date','<=',date_end),
#							 ('move_line_ids','!=',False),
#							 ('invoice_ids.user_id','in',user_ids),
#							 ('state','in',('posted','reconciled'))
#							 ]
			if list(partners):
					
#				 args.append(('partner_id','in',list(partners)))  
				if is_group:
					#2 өөр борлуулагчийн төлөлтйиг нэг төлөлтөөр хийвэ буруу болох тул салгаж хийх
#					 sql_query = """
#										 select aml.debit as debit,aj.name,aml.id as aml_id from 
#												 account_payment p left join 
#												 account_invoice_payment_rel ipr on ipr.payment_id=p.id left join 
#												 account_invoice ai on ai.id=ipr.invoice_id left join
# --												sale_order_line_invoice_rel slr on slr.invoice_line_id=ipr.invoice_id left join
# --												sale_order_line sol on slr.order_line_id=sol.id		left join 
# --												sale_order so on sol.order_id=so.id	 left join 
#												 account_move_line aml on aml.payment_id=p.id left join	 
#												 account_journal aj on aml.journal_id=aj.id left join	  
#												 account_account a on aml.account_id=a.id
#											   where 
#													 payment_date>=%s
#													 and payment_date<=%s 
#													 and ai.user_id in %s
#													 and p.state in ('posted','reconciled')
#													 and p.partner_id in %s
#													 and a.internal_type='liquidity'
#											   group by aj.name ,aml.id			   
#						 """
#					 params = (date_start,date_end,tuple(user_ids),tuple(partners))
#	 #				 sql_query += ' group by ipr.invoice_id,aml.date,so.id'
#	 #				print 'sql_query ',sql_query
#					 self.env.cr.execute(sql_query, params)
#					 query_res=self.env.cr.dictfetchall()					
#	 #				print 'query_res ',query_res								  
#					 res ={}
#	 #				print 'payment_ids ',payment_ids
#	 #				 so_obj = self.env['sale.order']
#					 for r in query_res:
# #					 print 'rrr ',r
#									 if res.has_key(r['name']):
#										 res[r['name']]+=r['debit']
#									 else:
#										 res[r['name']]=r['debit']
# #										 
										#Илүүтөлөлттэй бол буруу
												
					sql_query = """
								select sum(inv_amount) as inv_amount,sum(debit) as debit,name from (
								 --давхар шүүлт
								 select case when inv_count2=1 and debit>inv_amount 
								 then debit else inv_amount end as inv_amount,debit,name from
								 (
							------
							   select sum(debit) debit,inv_id,count(inv_id),
								----
							  (select count(distinct invoice_id) from account_invoice_payment_rel where payment_id =p_id) as inv_count2,
							  -----	
								   (select sum(apr.amount) from  
										account_invoice ai left join
										account_invoice_account_move_line_rel aiaml on aiaml.account_invoice_id=ai.id left join --payment_move_line_ids 
										account_partial_reconcile apr on aiaml.account_move_line_id=apr.credit_move_id--matched_debit_ids
										left join
										account_move am on ai.move_id=am.id left join
										account_move_line aml on aml.move_id=am.id and aml.id=apr.debit_move_id 
										where ai.id=inv_id and aml.id notnull) as inv_amount,name
								   from (
								   select aml.id as aml_id,aml.debit,ai.id as inv_id , aj.name as name,p.id as p_id
										from 
										account_payment p left join 
										account_invoice_payment_rel ipr on ipr.payment_id=p.id left join 
										account_invoice ai on ai.id=ipr.invoice_id left join
										account_invoice_line ail on ai.id=ail.invoice_id left join		
										sale_order_line_invoice_rel slr on slr.invoice_line_id=ail.id left join
										sale_order_line sol on slr.order_line_id=sol.id		left join 
										sale_order so on sol.order_id=so.id	 left join 
										account_move_line aml on aml.payment_id=p.id left join	 
										account_journal aj on aml.journal_id=aj.id   left join
										account_account a on aml.account_id=a.id
									  where 
												payment_date>=%s
												and payment_date<=%s 
												and ai.user_id in %s
												and p.state in ('posted','reconciled')
												and p.partner_id in %s
												and a.internal_type='liquidity'												
								  group by aml.id,ai.id, aj.name,p.id) as foo group by inv_id,name,p_id order by inv_id desc
									 ) as foo2
								  ) as baar group by name
					"""
					params = (date_start,date_end,tuple(user_ids),tuple(partners))
#					 params = (date_start,date_end,user_id)
					self.env.cr.execute(sql_query, params)
					query_res=self.env.cr.dictfetchall()   
					res ={}
					for r in query_res:
						if res.has_key(r['name']):
							if r['inv_amount']>r['debit']:
#								 result+=r['debit']
								res[r['name']]+=r['debit']
								 
							else:
#								 result+=r['inv_amount']										
								res[r['name']]+=r['inv_amount']
						else:
							if r['inv_amount']>r['debit']:
#								 result=r['debit']
								res[r['name']]=r['debit']
							else:
#								 result=r['inv_amount']										
								res[r['name']]=r['inv_amount']
							
				else:
					sql_query = """
										select aml.debit as debit,aj.name,aml.id as aml_id from 
												account_payment p left join 
												account_invoice_payment_rel ipr on ipr.payment_id=p.id left join 
												account_invoice ai on ai.id=ipr.invoice_id left join
												account_invoice_line ail on ai.id=ail.invoice_id left join		
												sale_order_line_invoice_rel slr on slr.invoice_line_id=ail.id left join
												sale_order_line sol on slr.order_line_id=sol.id		left join 
												sale_order so on sol.order_id=so.id	 left join 
												account_move_line aml on aml.payment_id=p.id left join	 
												account_journal aj on aml.journal_id=aj.id left join	  
												account_account a on aml.account_id=a.id
											  where 
													payment_date>=%s
													and payment_date<=%s 
													and ai.user_id in %s
													and p.state in ('posted','reconciled')
													and p.partner_id in %s
													and a.internal_type='liquidity'
													and so.partner_id=%s
											  group by aj.name ,aml.id			   
						"""
					params = (date_start,date_end,tuple(user_ids),tuple(partners),partner_id)
	#				 sql_query += ' group by ipr.invoice_id,aml.date,so.id'
#					 print 'sql_query ',sql_query
					self.env.cr.execute(sql_query, params)
					query_res=self.env.cr.dictfetchall()					
	#				print 'query_res ',query_res								  
					res ={}
	#				print 'payment_ids ',payment_ids
	#				 so_obj = self.env['sale.order']
					for r in query_res:
#						 print 'rrr2 ',r
						if res.has_key(r['name']):
							res[r['name']]+=r['debit']
						else:
							res[r['name']]=r['debit']					
#						 if order_id and order_id.partner_id.id==partner_id:	
# #						 print 'order_id.partner_id.id ',order_id.partner_id.id		
#							 for m in payment.move_line_ids:
#								 if m.debit>0 and m.account_id.internal_type in ('liquidity'):
#									 if res.has_key(m.journal_id.name):
#										 res[m.journal_id.name]+=m.debit
#									 else:
#										 res[m.journal_id.name]=m.debit			  
		elif inv_partner:
			aml_obj = self.env['account.move.line']
			payment_obj = self.env['account.payment']
			args=[
							('payment_date','>=',date_start),
							('payment_date','<=',date_end),
							('move_line_ids','!=',False),
							('invoice_ids.user_id','in',user_ids),
							('state','in',('posted','reconciled'))
							]
#			 if self.env['res.partner'].browse(partner_id).is_company:
#				 #Компани бол зөвхөн өөр дээрээ үүссэн нэхэмжлэх болон төлөлт
#				 args.append(('partner_id','=',partner_id))   
#				 payment_ids = payment_obj.search(args)
#				 res ={}
#	 #			 print 'payment_ids ',payment_ids
#				 for payment in payment_ids:
#					 for m in payment.move_line_ids:
#						 if m.debit>0 and m.account_id.internal_type in ('liquidity'):
#							 if res.has_key(m.journal_id.name):
#								 res[m.journal_id.name]+=m.debit
#							 else:
#								 res[m.journal_id.name]=m.debit				
#			 else:
			if list(partners):
				#хувь хүн бол толгой компани дээр нь нэхэмжлэх болон төлөлт нь үүссэн
#				 if partner_id:
#					 partner_ids=[partner_id]
#					 addr = self.env['res.partner'].browse(partner_id).address_get(['delivery', 'invoice'])
#					 if addr.get('invoice',False):
#						 partner_ids.append(addr['invoice'])
#					 args.append(('partner_id','in',partner_ids))  
					
				args.append(('partner_id','in',list(partners)))  
					
													 
				payment_ids = payment_obj.search(args)
				res ={}
#				print 'payment_ids ',payment_ids
				so_obj = self.env['sale.order']
				for payment in payment_ids:
					#гэхдээ зөвхөн толгой дээр үүсэн боловч өөртэй холбоотой SO уудын нэхэмжлэх болон төлөлт
					for inv in payment.invoice_ids:
#						 print 'inv ',inv
			#			 inv.payment_move_line_ids:
						order_id=False
						_logger.info("------ mobile ----- **** inv.id: %s", inv.id)
						_logger.info("------ mobile ----- **** inv.invoice_line_ids: %s", inv.invoice_line_ids)
						
						for l in inv.invoice_line_ids:
							for sol in l.sale_line_ids:
								order_id=sol.order_id
		#				 print 'order_id ',order_id
						if not order_id:
							refunds = so_obj.search([('name', 'like', inv.origin), ('company_id', '=', inv.company_id.id)])
							if refunds:
								order_id=refunds	
#						 print 'order_id ',order_id	  
					if is_group:
#						 if order_id and order_id.partner_id.id==partner_id:	
#						 print 'order_id.partner_id.id ',order_id.partner_id.id		
							for m in payment.move_line_ids:
								if m.debit>0 and m.account_id.internal_type in ('liquidity'):
									if res.has_key(m.journal_id.name):
										res[m.journal_id.name]+=m.debit
									else:
										res[m.journal_id.name]=m.debit			
					else:
						if order_id and order_id.partner_id.id==partner_id:	 #query дээр нэмэх Дэвжих хос трейд
#						 print 'order_id.partner_id.id ',order_id.partner_id.id		
							for m in payment.move_line_ids:
								if m.debit>0 and m.account_id.internal_type in ('liquidity'):
									if res.has_key(m.journal_id.name):
										res[m.journal_id.name]+=m.debit
									else:
										res[m.journal_id.name]=m.debit			
		elif user_ids:
			aml_obj = self.env['account.move.line']
			payment_obj = self.env['account.payment']
			args=[
							('payment_date','>=',date_start),
							('payment_date','<=',date_end),
							('move_line_ids','!=',False),
							('invoice_ids.user_id','in',user_ids),
							('state','in',('posted','reconciled'))
							]
			if self.env['res.partner'].browse(partner_id).is_company:
				#Компани бол зөвхөн өөр дээрээ үүссэн нэхэмжлэх болон төлөлт
				args.append(('partner_id','=',partner_id))   
				payment_ids = payment_obj.search(args)
				res ={}
	#			 print 'payment_ids ',payment_ids
				for payment in payment_ids:
					for m in payment.move_line_ids:
						if m.debit>0 and m.account_id.internal_type in ('liquidity'):
							if res.has_key(m.journal_id.name):
								res[m.journal_id.name]+=m.debit
							else:
								res[m.journal_id.name]=m.debit				
			else:
				#хувь хүн бол толгой компани дээр нь нэхэмжлэх болон төлөлт нь үүссэн
				if partner_id:
					partner_ids=[partner_id]
					addr = self.env['res.partner'].browse(partner_id).address_get(['delivery', 'invoice'])
					if addr.get('invoice',False):
						partner_ids.append(addr['invoice'])
					args.append(('partner_id','in',partner_ids))  
					
					
													 
				payment_ids = payment_obj.search(args)
				res ={}
	#			 print 'payment_ids ',payment_ids
				so_obj = self.env['sale.order']
				for payment in payment_ids:
					#гэхдээ зөвхөн толгой дээр үүсэн боловч өөртэй холбоотой SO уудын нэхэмжлэх болон төлөлт
					for inv in payment.invoice_ids:
#						 print 'inv ',inv
			#			 inv.payment_move_line_ids:
						order_id=False
						for l in inv.invoice_line_ids:
							for sol in l.sale_line_ids:
								order_id=sol.order_id
		#				 print 'order_id ',order_id
						if not order_id:
							refunds = so_obj.search([('name', 'like', inv.origin), ('company_id', '=', inv.company_id.id)])
							if refunds:
								order_id=refunds	
#						 print 'order_id ',order_id	  
					if order_id and order_id.partner_id.id==partner_id:	
#						 print 'order_id.partner_id.id ',order_id.partner_id.id		
						for m in payment.move_line_ids:
							if m.debit>0 and m.account_id.internal_type in ('liquidity'):
								if res.has_key(m.journal_id.name):
									res[m.journal_id.name]+=m.debit
								else:
									res[m.journal_id.name]=m.debit
							
		else:
			aml_obj = self.env['account.move.line']
			payment_obj = self.env['account.payment']
			args=[
							('payment_date','>=',date_start),
							('payment_date','<=',date_end),
							('move_line_ids','!=',False),
							]
			if partner_id:
				args.append(('partner_id','=',partner_id))   
			payment_ids = payment_obj.search(args)
			res ={}
			for payment in payment_ids:
				for m in payment.move_line_ids:
					if m.debit>0 and m.account_id.internal_type in ('liquidity'):
						if res.has_key(m.journal_id.name):
							res[m.journal_id.name]+=m.debit
						else:
							res[m.journal_id.name]=m.debit#					 if m.debit_move_id and m.debit_move_id.invoice_id:
#						 order_id=False
#						 for l in m.debit_move_id.invoice_id.invoice_line_ids:
#							 for sol in l.sale_line_ids:
#								 order_id=sol.order_id.id
#						 print 'order_id ',order_id
#						 res.append({'so_id':order_id,'amount':(m.debit_move_id.invoice_id.amount_total-m.debit_move_id.invoice_id.residual)})
		_logger.info(u'payment------- end \n')	
		return res		
	
	
	def _compute_sale_payment_by_all_partner(self,partner_list,date_start,date_end,user_ids=False,is_group=False):
		'''ХНТ ын бүх харилцагчаар
		'''
		_logger.info(u'_compute_sale_payment_by_all_partner------- start \n')	
#		 print 'user_ids ',user_ids
		for partner in partner_list:
			partners=[]
			for i in partner_list[partner]['inv_partner']:
				partners.append(i)
			partners=set(partners)
			if partner_list[partner]['inv_partner']:
				aml_obj = self.env['account.move.line']
				payment_obj = self.env['account.payment']
				args=[
								('payment_date','>=',date_start),
								('payment_date','<=',date_end),
								('move_line_ids','!=',False),
								('invoice_ids.user_id','in',user_ids),
								('state','in',('posted','reconciled'))
								]
				if list(partners):
					#хувь хүн бол толгой компани дээр нь нэхэмжлэх болон төлөлт нь үүссэн
					args.append(('partner_id','in',list(partners)))  
						
														 
					payment_ids = payment_obj.search(args)
					res ={}
	#				print 'payment_ids ',payment_ids
					so_obj = self.env['sale.order']
					for payment in payment_ids:
						#гэхдээ зөвхөн толгой дээр үүсэн боловч өөртэй холбоотой SO уудын нэхэмжлэх болон төлөлт
						for inv in payment.invoice_ids:
	#						 print 'inv ',inv
				#			 inv.payment_move_line_ids:
							order_id=False
							_logger.info("------ mobile ----- **** inv.id: %s", inv.id)
							_logger.info("------ mobile ----- **** inv.invoice_line_ids: %s", inv.invoice_line_ids)
							
							for l in inv.invoice_line_ids:
								for sol in l.sale_line_ids:
									order_id=sol.order_id
			#				 print 'order_id ',order_id
							if not order_id:
								refunds = so_obj.search([('name', 'like', inv.origin), ('company_id', '=', inv.company_id.id)])
								if refunds:
									order_id=refunds	
	#						 print 'order_id ',order_id	  
						if is_group:
	#						 if order_id and order_id.partner_id.id==partner_id:	
	#						 print 'order_id.partner_id.id ',order_id.partner_id.id		
								for m in payment.move_line_ids:
									if m.debit>0 and m.account_id.internal_type in ('liquidity'):
										if res.has_key(m.journal_id.name):
											res[m.journal_id.name]+=m.debit
										else:
											res[m.journal_id.name]=m.debit			
						else:
							if order_id and order_id.partner_id.id==partner_id:	
	#						 print 'order_id.partner_id.id ',order_id.partner_id.id		
								for m in payment.move_line_ids:
									if m.debit>0 and m.account_id.internal_type in ('liquidity'):
										if res.has_key(m.journal_id.name):
											res[m.journal_id.name]+=m.debit
										else:
											res[m.journal_id.name]=m.debit			
		_logger.info(u'payment------- end \n')	
		return res			

	
	def _compute_partner_initial(self,partner_id,date_start,user_ids=False,is_group=False,is_init_split=False):
		_logger.info(u'_compute_partner_initial-------\n')  
		if not user_ids:
			aml_obj = self.env['account.move.line']
			payment_obj = self.env['account.payment']
			args=[
							('date','<',date_start),
							('account_id.internal_type','in',['payable','receivable']),
							('move_id.state','=','posted')
							]
			if partner_id:
				args.append(('partner_id','=',partner_id))   
			aml_ids = aml_obj.search(args)
			res ={}
			initial=0
			for aml in aml_ids:
				initial+=aml.debit-aml.credit
			return initial   
		else:  
			if is_init_split:
				initial_dict={}
				account_obj = self.env['account.account']
				partner_obj = self.env['res.partner']
				
				partner_ids = [partner_id]
				account_ids = []
				skip=[169,170,172]
#				 if data['account_id']:
#		 #			 account_ids = [data['account_id'][0]]
#					 account_ids = account_obj.search([('id','=',data['account_id'][0])])
#				 elif data['account_type'] == 'payable':
#					 account_ids = account_obj.search([('user_type_id.type','=','payable')])
#				 elif data['account_type'] == 'receivable':
				account_ids = account_obj.search([('user_type_id.type','=','receivable'),('id','not in',skip)])

		
				date_where = ""
				date_where = " m.date < '%s' " % date_start
				state_where = ""
				state_where = " AND m.state = 'posted' " 
				partner_where = " AND l.partner_id is not null "
				if is_group and partner_id:
					part = self.env['res.partner'].browse(partner_id)
					parts=[partner_id]
					if part.parent_id:
						partner_ids.append(part.parent_id.id)
#				 elif partner_id:
#					 args.append(('partner_id','=',partner_id)) 
				if partner_ids :
					partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
				
				a = []
				cr = self.env.cr
				MoveLine = self.env['account.move.line']
				init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=date_start,
																state='posted',date_to=False, strict_range=True, initial_bal=True)._query_get()
				init_wheres = [""]
				
				if init_where_clause.strip():
					init_wheres.append(init_where_clause.strip())
				init_filters = " AND ".join(init_wheres)
				filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
		#		 print 'filters=======: ',filters
		#		 print 'init_where_params ',init_where_params
				
				for account in account_ids.ids:
					cr.execute("SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) "
							   "FROM account_move_line l "
							   "LEFT JOIN account_move m ON (m.id=l.move_id) "
							   "WHERE "
							   " state='posted' "+partner_where+" " 
							   " "+filters+" "
							   " AND l.account_id = " + str(account) + 
							   " GROUP BY l.account_id ",tuple(init_where_params))
		#			 AND l.state != 'draft' 
					fetched = cr.fetchone()
		#			 print "fetched::::::",fetched
					if fetched:
						q = "SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) \
								   FROM account_move_line l \
								   LEFT JOIN account_move m ON (m.id=l.move_id) \
								   LEFT JOIN account_period p ON (p.id=l.period_id) \
								   WHERE "+date_where+" "+state_where \
								   + partner_where+"  AND l.account_id = " + str(account) + " \
								   GROUP BY l.account_id "
						# print 'Query;	   ', q
		#				 AND p.fiscalyear_id =  " + str(data['fiscalyear_id']) + " AND l.state != 'draft' 
					sdebit, scredit, samount_currency = fetched or (0,0,0)
					account_str = account_obj.browse(account)
					acc=account_str.code + ' ' + account_str.name
					initial_amount = sdebit - scredit
#						 initial_amount_currency = samount_currency
					initial_dict[account]=initial_amount   
#				 print 'initial_dict ',initial_dict
			else:   
				#Удаж байна
				func=True
				if func:
					invoices=[]		   
					initial_dict={}
					cr = self.env.cr
					date_where = " date < '%s' " % date_start
		#			 for i in query_res:
		#				 invoices.append(i[0])
					if is_group and partner_id:
						part = self.env['res.partner'].browse(partner_id)
						parts=[partner_id]
						if part.parent_id:
							parts.append(part.parent_id.id)
		
					cr.execute("SELECT coalesce(sum(residual),0.0) "
							   "FROM account_invoice l "
							   "WHERE "
							   " state ='open' AND partner_id in ("+','.join(map(str,parts))+") AND "+date_where+" "
							   " AND type in ('out_invoice','out_refund') "  
							   " AND user_id in  ("+','.join(map(str,user_ids))+") ")
					
		#			 AND l.state != 'draft' 
					fetched = cr.fetchone()
		#				 AND p.fiscalyear_id =  " + str(data['fiscalyear_id']) + " AND l.state != 'draft' 
					initial_dict[date_start] = fetched[0] or 0	   
#					 func_res=self._compute_sale_payment_function(parts,date_start,False,user_ids,is_init=True)
#					 initial_dict ={}
#		 #			 if 12683 in partners:
#					 print 'func_res222222 ',func_res
#					 check_disc=[]
#					 for r in func_res:
#						 if initial_dict.has_key(r['name']):
#							 amount_report=0
#							 discount=0
#							 debit=0
#							 if r['amount_report']:
#								 amount_report=r['amount_report']
#								 debit=r['debit']
#							 if r['discount'] and r['p_id'] not in check_disc and not r['from_bank']:
#								 if r['pay_amount']!=r['amount']:
#									 discount=r['discount']
#									 check_disc.append(r['p_id'])
#							 print 'amount_report2 ',amount_report
#							 print 'discount ',discount
#							 initial_dict[r['name']]+=debit -(amount_report - discount)
#		 #					 res[r['name']]+=r['amount_report'] or 0 -r['discount'] or 0
#						 else:
#							 amount_report=0
#							 discount=0
#							 debit=0
#							 if r['amount_report']:
#								 amount_report=r['amount_report']
#								 debit=r['debit']
#							 if r['discount'] and r['p_id'] not in check_disc and not r['from_bank']:
#								 if r['pay_amount']!=r['amount']:#apr.amount p.amount
#									 discount=r['discount']
#									 check_disc.append(r['p_id'])
#							 print 'amount_report22 ',amount_report
#							 print 'discount ',discount
#							 initial_dict[r['name']]=debit -(amount_report - discount)
				else:
					initial_dict={}
					inv_obj = self.env['account.move']
					payment_obj = self.env['account.payment']
					cnt=0
					for user in user_ids:
						args=[
										('date_invoice','<',date_start),
			#							 ('account_id.internal_type','in',['payable','receivable']),
		#								 ('state','=','open'),
										('state','in',('paid','open')),
										('user_id','=',user)
										]
						if is_group and partner_id:
							part = self.env['res.partner'].browse(partner_id)
							parts=[partner_id]
							if part.parent_id:
								parts.append(part.parent_id.id)
							args.append(('partner_id','in',parts))   
						elif partner_id:
							args.append(('partner_id','=',partner_id)) 
						inv_ids = inv_obj.search(args)
						res ={}
						initial=0
						discount=0
						for inv in inv_ids:
		#					 if inv.type=='out_refund':
		#						 initial+=-inv.residual
		#					 else:
		#						 initial+=inv.residual
							if inv.type=='out_refund':
								initial+=-inv.amount_total
							else:
								initial+=inv.amount_total
		
						
							for pay in  inv.payment_move_line_ids.filtered(lambda r: 
																			   r.date <date_start
																			   ):
		#						 if inv.type=='out_refund':
		#							 if pay.debit>0:
		#								 initial+=pay.debit
		#						 else:
		#							 if pay.credit>0:
		#								 initial+=-pay.credit
						#Нэг төлөлтөөр олон нэхэмжлэхийн төлөлт хийсэн бол
								payment_currency_id = False
								if inv.type in ('out_invoice', 'in_refund'):
									amount = sum([p.amount for p in pay.matched_debit_ids if p.debit_move_id in inv.move_id.line_ids])
									amount_currency = sum(
										[p.amount_currency for p in pay.matched_debit_ids if p.debit_move_id in inv.move_id.line_ids])
									if pay.matched_debit_ids:
										payment_currency_id = all([p.currency_id == pay.matched_debit_ids[0].currency_id for p in
																   pay.matched_debit_ids]) and pay.matched_debit_ids[
																  0].currency_id or False
								elif inv.type in ('in_invoice', 'out_refund'):
									amount = sum(
										[p.amount for p in pay.matched_credit_ids if p.credit_move_id in inv.move_id.line_ids])
									amount_currency = sum([p.amount_currency for p in pay.matched_credit_ids if
														   p.credit_move_id in inv.move_id.line_ids])
									if pay.matched_credit_ids:
										payment_currency_id = all([p.currency_id == pay.matched_credit_ids[0].currency_id for p in
																   pay.matched_credit_ids]) and pay.matched_credit_ids[
																  0].currency_id or False
								# get the payment value in invoice currency
								if payment_currency_id and payment_currency_id == inv.currency_id:
									amount_to_show = amount_currency
								else:
									amount_to_show = pay.company_id.currency_id.with_context(date=inv.date).compute(amount,
																											  inv.currency_id)
								if float_is_zero(amount_to_show, precision_rounding=inv.currency_id.rounding):
									continue
								# print 'amount_to_show ',amount_to_show
								if inv.type=='out_refund':
		#							 if pay.debit>0:
									if amount_to_show>0:
										initial+=amount_to_show
								else:
									if amount_to_show>0:
										initial+=-amount_to_show
		#				 print 'initial ',initial
						if cnt==0:
							discount = payment_obj._compute_partner_payment_discount(partner_id,'2017-01-01',date_start)
						else:
							discount=0
						initial_dict[user]=initial#-discount
				
			return initial_dict	  
	 
	
	def _compute_sale_payment_by_user(self,user_id,date_start,date_end,account_ids=False):
		_logger.info(u'payment-------\n')	
#		 data={'date':'2018-09-10','partner_id':self.partner_id.id}
#		 sale_orders = []
#		 sale_obj = self.env['sale.order']
#		 pick_obj = self.env['stock.picking']
		sdate = date_start
		edate = date_end
		_logger.info("------ mobile ----- **** sdate: %s  edate: %s", sdate, edate)
		so_ids=[]
#		 so_ids = sale_obj.sudo().search([
# #								   ('validity_date','>=',sdate),
# #								   ('validity_date','<=',edate)
#									 ('user_id','=',user_id)
#								   ])
		pay_obj=self.env['sale.payment.info']
#		 for so in so_ids:
#			 invoice_ids = so.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
		payments = pay_obj._compute_partner_user_so_payment(False,sdate,edate,so_ids,user_id)	
		
		
		return payments
	
	
	def _compute_user_payments(self,date_start,date_end,user_id):
		_logger.info(u'payment user-------_compute_user_payments \n') 
		result=[]
		if user_id:
			sql_query = """
							select sum(debit) as debit,partner as partner_id  from (							  
							select aml.debit as debit,aj.name,aml.id as aml_id,aml.partner_id as partner from 
												account_payment p left join 
												account_invoice_payment_rel ipr on ipr.payment_id=p.id left join 
												account_invoice ai on ai.id=ipr.invoice_id left join
												account_move_line aml on aml.payment_id=p.id left join	 
												account_journal aj on aml.journal_id=aj.id left join	  
												account_account a on aml.account_id=a.id
											  where 
											payment_date>=%s
											and payment_date<=%s 
											and ai.user_id = %s
											and p.state in ('posted','reconciled')
											and a.internal_type='liquidity'
											  group by aj.name ,aml.id,aml.partner_id  ) as foo  group by partner order by sum(debit)
										  """
			params = (date_start,date_end,user_id)
#				 sql_query += ' group by ipr.invoice_id,aml.date,so.id'
#				print 'sql_query ',sql_query
			self.env.cr.execute(sql_query, params)
			query_res=self.env.cr.dictfetchall()					
			result=query_res
		_logger.info("------ mobile -----result %s  ", str(result))
		return result
			
	
	def get_payment_so_list_mw(self):
		data={'date':'2018-10-03','partner_id':self.partner_id.id}
		_logger.info("------ mobile -----get_payment_so_list %s  %s", str(data), type(data))
		sale_orders = []
		sale_obj = self.env['sale.order']
		sdate=data['date'].split('-')[0]+'-'+data['date'].split('-')[1]+'-01'
		edate= data['date'].split('-')[0]+'-'+data['date'].split('-')[1]+'-'+str(monthrange(int(data['date'].split('-')[0]), int(data['date'].split('-')[1]))[1])
		_logger.info("------ mobile -----get_payment_so_list sdate: %s  edate: %s", sdate, edate)
		_logger.info("------ mobile -----get_payment_so_list part: %s  edate: %s", str(data['partner_id']), str(self.env.user.id))
		so_ids = sale_obj.search([
								  ('partner_id','=',data['partner_id']),
								  ('validity_date','>=',sdate),
								  ('validity_date','<=',edate),
								  ('user_id','=',74)])#self.env.user.id
#		 self.env.user.id
		
		pay_obj=self.env['sale.payment.info']
		payments = pay_obj._compute_partner_sale_payment(data['partner_id'],sdate,edate)	
		for so in so_ids:
			lines=[]
			for sol in so.order_line:
				lines.append({
								'product_id':sol.product_id.id,
								'qty': sol.product_uom_qty,
								'price_unit': sol.price_unit,
								'product_name':sol.product_id.name
								})
						
			sale_orders.append({'so_id':so.id,
										   'so_name':so.name,
										   'so_date':so.validity_date,
										   'payment':0,
										   'amount_total':so.amount_total,
										   'lines':lines
										   })
							
		_logger.info("------ mobile -----len(sale_orders)  %s",len(sale_orders))
		for s in sale_orders:
			for p in payments:
				if p['so_id'] == s['so_id']:
					s['payment']=+p['amount']
		return sale_orders
	
	def create_payment_bank(self):
		data={'date':'2018-09-10','partner_id':self.partner_id.id,'so_id':self.so_id.id,'amount':self.pay_amount}
		
		_logger.info("------ mobile -----payment create datas %s  %s", str(data), type(data))
		statement_obj = self.env['account.bank.statement']
		bank_line_obj = self.env['account.bank.statement.line']
		sale_obj = self.env['sale.order']
		invoice_obj = self.env['account.move']
		if self.env.user.cash_journal_id:
			cash_journal_id = self.env.user.cash_journal_id.id
		
		statement_id= statement_obj.search([('date','=',data['date']),('journal_id','=',self.env.user.cash_journal_id.id)])
		if not statement_id:
			statement_id = statement_obj.sudo().create({'journal_id':self.env.user.cash_journal_id.id,
								 'date':data['date']})
		sale_order = sale_obj.browse(data['so_id'])
		invoices = set()
		partner_id=False
		for so in sale_order:
			partner_id=so.partner_id.id
			for sol in so.order_line:
				for ail in sol.invoice_lines:
					invoices.add(ail.invoice_id.id)
		invoice_br= invoice_obj.browse(list(invoices))
		amsl_vals=[]
		for inv in invoice_br:
			account_id= inv.account_id.id
			if inv.move_id:
			   for aml in inv.move_id.line_ids: 
				   if aml.account_id.id==account_id:
					   amsl_vals += [(0,0,{
									'inv_amount':data['amount'],
									'import_inv_id':inv.id
										})]				   
		try:
			bl=bank_line_obj.sudo().create({
										   'name': self.env.user.name+u' орлого',
										   'amount': data['amount'],
										   #				 'date':time.strftime("%Y-%m-%d"),
										   'date':data['date'],
										   'statement_id':statement_id.id,
										   'account_id':account_id,
										   'state':'draft',
										   'partner_id':partner_id,
										   'ref':self.env.user.name+u' орлого',
										   'import_line_ids':amsl_vals
										   })
			bl.button_validate_line()
			return {'payment_id':bl.id}
		except Exception as e:
			_logger.info(u"------ mobile -----absl ERROR %s ",str(e))
			return {'payment_id': False, 'error': str(e)}
		

	
	def create_payment(self):
		data={'date':'2018-09-10','partner_id':self.partner_id.id,'so_id':self.so_id.id,'pay_amount':self.pay_amount, 'journal_id':9}
		_logger.info("------ mobile -----payment create datas %s  %s", str(data), type(data))
		sale_obj = self.env['sale.order']
		journal_obj = self.env['account.journal']
		invoice_obj = self.env['account.move']
		if data.get('journal_id',False):
			cash_journal_id=journal_obj.browse(int(float(data['journal_id'])))
		elif self.env.user.cash_journal_id:
			cash_journal_id = self.env.user.cash_journal_id
		else:
			_logger.info(u"------ mobile -----absl ERROR journal not found ")
			return {'payment_id': False, 'error': 'journal not found'}		
			
		
		sale_order = sale_obj.browse(int(float(data['so_id'])))
		invoices = set()
		partner_id=False
		for so in sale_order:
			partner_id=so.partner_id.id
			for sol in so.order_line:
				for ail in sol.invoice_lines:
					invoices.add(ail.invoice_id.id)
		invoice_br= invoice_obj.browse(list(invoices))
		amsl_vals=[]
		payment_methods = (data['pay_amount']>0) and cash_journal_id.inbound_payment_method_ids or cash_journal_id.outbound_payment_method_ids
#		 payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
		p_vals={
				'payment_method_id': payment_methods and payment_methods[0].id or False,
				'partner_id': partner_id,
#				 'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
				'journal_id': cash_journal_id.id,
				'payment_date': data['date'],	
				'state': 'draft',
#				 'branch_id': self.branch_id.id,
#				 'communication': self.env.user.name+u' орлого' or '',
			   'name': self.env.user.name+u' орлого',
			   'amount': data['pay_amount'],

			}		
		for inv in invoice_br:
			account_id= inv.account_id.id
				#/////////////////////////////////////////////////////
#			 if invoice_defaults and len(invoice_defaults) == 1:
			p_vals['communication'] = inv.reference or inv.name or inv.number
			p_vals['currency_id'] = inv.currency_id.id
			p_vals['payment_type'] = inv.type in ('out_invoice', 'in_refund') and 'inbound' or 'outbound'
			p_vals['partner_type'] = MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type]
		if list(invoices):
			p_vals.update({
					'invoice_ids': [(6, 0, list(invoices))],
				})
				
				#/////////////////////////////////////////////////////					   
#		 try:
		payment = self.env['account.payment'].create(p_vals)
		payment.action_validate_invoice_payment()
		return {'payment_id':payment.id}
#		 except Exception as e:
#			 _logger.info(u"------ mobile -----absl ERROR %s ",str(e))
#			 return {'payment_id': False, 'error': str(e)}

	
	def create_payment2(self):
		data={'date':'2018-09-10','partner_id':self.so_id.partner_id.id,'so_id':self.so_id.id,'pay_amount':self.pay_amount}
		
		_logger.info("------ mobile -----payment create datas %s  %s", str(data), type(data))
		sale_obj = self.env['sale.order']
		invoice_obj = self.env['account.move']
		if self.env.user.cash_journal_id:
			cash_journal_id = self.env.user.cash_journal_id.id
		
		sale_order = sale_obj.browse(int(float(data['so_id'])))
		invoices = set()
		partner_id=False
		for so in sale_order:
			partner_id=so.partner_id.id
			for sol in so.order_line:
				for ail in sol.invoice_lines:
					invoices.add(ail.invoice_id.id)
		invoice_br= invoice_obj.browse(list(invoices))
		amsl_vals=[]
		payment_methods = (data['pay_amount']>0) and self.env.user.cash_journal_id.inbound_payment_method_ids or self.env.user.cash_journal_id.outbound_payment_method_ids
#		 payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
		p_vals={
				'payment_method_id': payment_methods and payment_methods[0].id or False,
				'partner_id': partner_id,
#				 'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
				'journal_id': 7,
				'payment_date': data['date'],	
				'state': 'draft',
#				 'branch_id': self.branch_id.id,
#				 'communication': self.env.user.name+u' орлого' or '',
			   'name': self.env.user.name+u' орлого',
			   'amount': data['pay_amount'],

			}		
		for inv in invoice_br:
			account_id= inv.account_id.id
				#/////////////////////////////////////////////////////
#			 if invoice_defaults and len(invoice_defaults) == 1:
			p_vals['communication'] = inv.reference or inv.name or inv.number
			p_vals['currency_id'] = inv.currency_id.id
			p_vals['payment_type'] = inv.type in ('out_invoice', 'in_refund') and 'inbound' or 'outbound'
			p_vals['partner_type'] = MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type]
		if list(invoices):
			p_vals.update({
					'invoice_ids': [(6, 0, list(invoices))],
				})
				
				#/////////////////////////////////////////////////////					   
#		 try:
		payment = self.env['account.payment'].create(p_vals)
		payment.action_validate_invoice_payment()
		return {'payment_id':payment.id}
#		 except Exception as e:
#			 _logger.info(u"------ mobile -----absl ERROR %s ",str(e))
#			 return {'payment_id': False, 'error': str(e)}
				

	
	def _partner_cash_payment_discount(self,partner_id,date_start,date_end):
		_logger.info(u'payment user-------_partner_cash_payment_discount \n')	
		discount=0
		if partner_id:
			aml_obj = self.env['account.move.line']
			payment_obj = self.env['account.payment']
			args=[
							('payment_date','>=',date_start),
							('payment_date','<=',date_end),
							('move_line_ids','!=',False),
#							 ('invoice_ids.user_id','in',user_ids),
							('state','in',('posted','reconciled')),
							('partner_id','=',partner_id)
							]
#			 if self.env['res.partner'].browse(partner_id).is_company:
#				 #Компани бол зөвхөн өөр дээрээ үүссэн нэхэмжлэх болон төлөлт
#				 args.append(('partner_id','=',partner_id))   
#				 payment_ids = payment_obj.search(args)
#				 res ={}
	#			 print 'payment_ids ',payment_ids
			for payment in payment_ids:
				if payment.discount>0:
					discount+=payment.discount
		return data_list
				
				
				
