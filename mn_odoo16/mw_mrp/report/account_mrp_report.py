# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models

class account_mrp_view_report(models.Model):
	_name = "account.mrp.view.report"
	_description = "Account MRP report"
	_auto = False
	_order = 'account_id'
 
	account_id = fields.Many2one('account.account', u'Данс', readonly=True)
	date = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
 # partner_id = fields.Many2one('res.partner', u'Харилцагч', readonly=True)
	debit_all = fields.Float(u'Дебит бүгд', readonly=True)
	credit_all = fields.Float(u'Кредит бүгд', readonly=True)

	mrp_debit = fields.Float(u'Дебит MO', readonly=True)
	mrp_credit = fields.Float(u'Кредит MO', readonly=True)

	close_debit = fields.Float(u'Дебит хаалт', readonly=True)
	close_credit = fields.Float(u'Кредит хаалт', readonly=True)

	other_debit = fields.Float(u'Дебит Бусад', readonly=True)
	other_credit = fields.Float(u'Кредит Бусад', readonly=True)

	move_id = fields.Many2one('account.move', u'Гүйлгээ', readonly=True)
	branch_id = fields.Many2one('res.branch', u'Салбар', readonly=True)

 # analytic_account_id = fields.Many2one('account.analytic.account', u'Шинжилгээний данс',readonly=True)
 # code_group_id = fields.Many2one('account.code.type', u'Дансны бүлэг',readonly=True)
 
	def init(self):
		tools.drop_view_if_exists(self.env.cr, 'account_mrp_view_report')
		self.env.cr.execute("""CREATE or REPLACE VIEW account_mrp_view_report as 
				select move_id as id, sum(debit_all) as debit_all,   
sum(credit_all) as credit_all, 
sum(close_debit) as close_debit,
sum(close_credit) as close_credit,
sum(mrp_debit) as mrp_debit,
sum(mrp_credit) as mrp_credit,
sum(other_debit) as other_debit,
sum(other_credit) as other_credit,
account_id,date,branch_id,move_id
 from (     
select l1.move_id,a.code,sum(l1.debit) as debit_all,sum(l1.credit) as credit_all,l1.date,l1.account_id,l1.branch_id,
        case when l1.move_id in (select move_id from mrp_prod_account_move_st_rel where move_id notnull group by move_id union all select move_id from mrp_prod_account_move_st_close_rel where move_id notnull ) 
        then sum(l1.debit)  else 0 end as mrp_debit,
        case when l1.move_id in (select move_id from mrp_prod_account_move_st_rel where move_id notnull group by move_id union all select move_id from mrp_prod_account_move_st_close_rel where move_id notnull ) 
        then sum(l1.credit)  else 0 end as mrp_credit,
        case when l1.move_id in (select move_id from mrp_standart_cost_calc_line where move_id notnull group by move_id) 
        then sum(l1.debit)  else 0 end as close_debit,
        case when l1.move_id in (select move_id from mrp_standart_cost_calc_line where move_id notnull group by move_id) 
        then sum(l1.credit)  else 0 end as close_credit,
        case when l1.move_id not in (select move_id from mrp_prod_account_move_st_rel where move_id notnull group by move_id union all select move_id from mrp_prod_account_move_st_close_rel where move_id notnull union all select move_id from mrp_standart_cost_calc_line where move_id notnull group by move_id) 
        then sum(l1.debit)  else 0 end as other_debit,
        case when l1.move_id not in (select move_id from mrp_prod_account_move_st_rel where move_id notnull group by move_id union all select move_id from mrp_prod_account_move_st_close_rel where move_id notnull union all select move_id from mrp_standart_cost_calc_line where move_id notnull group by move_id) 
        then sum(l1.credit)  else 0 end as other_credit
        from account_account a left join account_move_line l1 on l1.account_id=a.id  
        where a.id in (select credit_account_id from mrp_product_standart_cost_line where credit_account_id notnull) 
        --and a.company_id=1 and l1.date between '2024-03-01' and '2024-03-31' and l1.company_id=1 
        and l1.branch_id=36         group by l1.move_id ,a.code ,l1.date,l1.account_id,l1.branch_id
        ) as foo group by move_id,account_id,date,branch_id
			""")
		
		
# 		select sum(debit_all) as debit_all,   
# sum(credit_all) as credit_all, 
# sum(close_debit) as close_debit,
# sum(mrp_debit) as mrp_debit,
# sum(mrp_credit) as mrp_credit,
# sum(other_debit) as other_debit,
# sum(other_credit) as other_credit,
# code                              
#  from (                  
# select a.code,sum(l1.debit) as debit_all,sum(l1.credit) as credit_all,
#         case when l1.move_id in (select move_id from mrp_prod_account_move_st_rel where move_id notnull group by move_id union all select move_id from mrp_prod_account_move_st_close_rel where move_id notnull ) 
#         then sum(l1.debit)  else 0 end as mrp_debit,                                                                                                                                                              
#         case when l1.move_id in (select move_id from mrp_prod_account_move_st_rel where move_id notnull group by move_id union all select move_id from mrp_prod_account_move_st_close_rel where move_id notnull ) 
#         then sum(l1.credit)  else 0 end as mrp_credit,                                                                                                                                                            
#         case when l1.move_id in (select move_id from mrp_standart_cost_calc_line where move_id notnull group by move_id) 
#         then sum(l1.debit)  else 0 end as close_debit,
#         case when l1.move_id in (select move_id from mrp_standart_cost_calc_line where move_id notnull group by move_id) 
#         then sum(l1.credit)  else 0 end as close_credit,
#         case when l1.move_id not in (select move_id from mrp_prod_account_move_st_rel where move_id notnull group by move_id union all select move_id from mrp_prod_account_move_st_close_rel where move_id notnull union all select move_id from mrp_standart_cost_calc_line where move_id notnull group by move_id)                                                                                                                                                                           then sum(l1.debit)  else 0 end as other_debit,
#         case when l1.move_id not in (select move_id from mrp_prod_account_move_st_rel where move_id notnull group by move_id union all select move_id from mrp_prod_account_move_st_close_rel where move_id notnull union all select move_id from mrp_standart_cost_calc_line where move_id notnull group by move_id)                                                                                                                                                                           then sum(l1.credit)  else 0 end as other_credit
#         from account_account a left join account_move_line l1 on l1.account_id=a.id  
#         where a.id in (select credit_account_id from mrp_product_standart_cost_line where credit_account_id notnull) 
#         and a.company_id=1 and l1.date between '2024-03-01' and '2024-03-31' and l1.company_id=1 and a.id in (30122, 30118)
#         and l1.branch_id=36         group by l1.move_id ,a.code 
#         ) as foo group by code;   
