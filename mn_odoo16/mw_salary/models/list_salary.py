# -*- coding: utf-8 -*-
##############################################################################
#
#	ManageWall, Enterprise Management Solution	
#	Copyright (C) 2007-2014 ManageWall Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#

#	Email : puujee9005@gmail.com
#	Phone : 976 + 95900955
#
##############################################################################
from odoo.tools.translate import _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import logged, profile
import time, odoo.netsvc, odoo.tools, re
import logging
from odoo.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID, api
_logger = logging.getLogger(__name__)
import itertools
import collections
from odoo import models, fields, api, _
from xlsxwriter.utility import xl_rowcol_to_cell
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import UserError, ValidationError
from odoo.addons.auth_signup.models.res_partner import SignupError, now
import odoo
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import timedelta

import xlrd
from odoo.osv import osv

DATE_FORMAT = "%Y-%m-%d"

class ListWage(models.Model):
	_name = "list.wage"
	_description = "list wage"

	def unlink(self):
		for obj in self:
			if obj.state != 'draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(ListWage, self).unlink()

	name = fields.Char('Name', size=150)
	year= fields.Char(method=True, store=True, type='char', string='Year', size=8)
	month=fields.Selection([('1','January'), ('2','February'), ('3','March'), ('4','April'),
		('5','May'), ('6','June'), ('7','July'), ('8','August'), ('9','September'),
		('90','October'), ('91','November'), ('92','December')], 'Month', required=True)
	emp_balance_ids= fields.One2many('list.wage.line', 'parent_id', 'Employee List')
	data = fields.Binary('Exsel file')
	hr_company_id = fields.Many2one('hr.company', 'Байршил')
	date = fields.Date('Огноо')
	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
	s_date = fields.Date('Эхлэх огноо')
	e_date = fields.Date('Дуусах огноо')
	move_id = fields.Many2one('account.move', string='Санхүү бичилт')
	journal_id = fields.Many2one('account.journal', string='Журнал')
	invoice_partner_id = fields.Many2one('res.partner','Нэхэмжлэх харилцагч')
	invoice_date = fields.Date('Нэхэмжлэх огноо')
	is_maternity = fields.Boolean('Жирэмсний тэтгэмж эсэх')
	state= fields.Selection([('draft','Draft'),
				('done',u'done')], 'Status',readonly=True, default = 'draft', tracking=True, copy=False)

	def done_action(self):
		for line in self.emp_balance_ids:
			line.write({'state': 'done'})
		return self.write({'state': 'done'})

	def draft_action(self):
		for line in self.emp_balance_ids:
			line.write({'state': 'draft'})
		return self.write({'state': 'draft'})

	def print_list_report(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'list'

		# CELL styles тодорхойлж байна
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(9)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#99CCFF')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(9)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#99CCFF')

		content_left = workbook.add_format({'num_format': '###,###,###'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(9)
		content_left.set_border(style=1)
		content_left.set_align('left')

		content_left_no = workbook.add_format({'num_format': '###,###,###'})
		content_left_no.set_text_wrap()
		content_left_no.set_font('Times new roman')
		content_left_no.set_font_size(11)
		content_left_no.set_align('left')
		
		content_right = workbook.add_format({'num_format': '###,###,###'})
		content_right.set_text_wrap()
		content_right.set_font('Times new roman')
		content_right.set_font_size(9)
		content_right.set_border(style=1)
		content_right.set_align('right')

		content_right1 = workbook.add_format({'num_format': '###,###,###.##'})
		content_right1.set_text_wrap()
		content_right1.set_font('Times new roman')
		content_right1.set_font_size(9)
		content_right1.set_border(style=1)
		content_right1.set_align('right')

		center_bold = workbook.add_format({'num_format': '###,###,###','bold': 1})
		center_bold.set_text_wrap()
		center_bold.set_font('Times new roman')
		center_bold.set_font_size(9)
		center_bold.set_align('right')
		center_bold.set_border(style=1)
		center_bold.set_bg_color('#99CCFF')

		sheet = workbook.add_worksheet(u'Цалин')
		
		sheet.merge_range(0, 0, 0, 3, self.company_id.name, h1)
		sheet.merge_range(2, 0, 2, 20, self.month + u'-Р САРЫН ХӨДӨЛМӨРИЙН ЧАДВАР ТҮР АЛДСАНЫ ТЭТГЭМЖ ОЛГОСОН ЖАГСААЛТ', h1)
		# sheet.write(5, 19, u'Огноо:', h1)
		# sheet.write(5, 20, str(self.invoice_date), h1)

		rowx=6
		sheet.merge_range(rowx, 0,rowx+2,0, u'№', theader),
		sheet.merge_range(rowx,1,rowx+2,1, u'Овог', theader),
		sheet.merge_range(rowx,2,rowx+2,2, u'Нэр', theader),
		sheet.merge_range(rowx,3,rowx+2,3, u'Ажилтны код', theader),
		sheet.merge_range(rowx,4,rowx+2,4, u'НДД дугаар', theader),
		sheet.merge_range(rowx,5,rowx,7, u'Эмнэлгийн хуудасны', theader),
		sheet.merge_range(rowx+1,5,rowx+2,5, u'Дугаар', theader),
		sheet.merge_range(rowx+1,6,rowx+2,6, u'Эхэлсэн огноо', theader),
		sheet.merge_range(rowx+1,7,rowx+2,7, u'Дууссан огноо', theader),
		sheet.merge_range(rowx,8,rowx+2,8, u'Ажилласан жил', theader),
		sheet.merge_range(rowx,9,rowx+2,9, u'3 сарын нийлбэр цалин', theader),
		sheet.merge_range(rowx,10,rowx+2,10, u'3 сарын нийлбэр хоног', theader),
		sheet.merge_range(rowx,11,rowx,13, u'Тэтгэмж бодох', theader),
		sheet.merge_range(rowx+1,11,rowx+2,11, u'Нэг өдрийн хөлс', theader),
		sheet.merge_range(rowx+1,12,rowx+2,12, u'Хувь', theader),
		sheet.merge_range(rowx+1,13,rowx+2,13, u'Нэг өдөрт ногдох', theader),
		sheet.merge_range(rowx,14,rowx,16, u'Хоног', theader),
		sheet.merge_range(rowx+1,14,rowx+2,14, u'Бүгд', theader),
		sheet.merge_range(rowx+1,15,rowx+2,15, u'Ажил олгогчоос', theader),
		sheet.merge_range(rowx+1,16,rowx+2,16, u'НД-аас', theader),
		sheet.merge_range(rowx,17,rowx,19, u'Олгох тэтгэмж', theader),
		sheet.merge_range(rowx+1,17,rowx+2,17, u'Бүгд', theader),
		sheet.merge_range(rowx+1,18,rowx+2,18, u'Ажил олгогчоос', theader),
		sheet.merge_range(rowx+1,19,rowx+2,19, u'НД-аас', theader),
		# sheet.merge_range(rowx,20,rowx+2,20, u'Дансны дугаар', theader),

		rowx+=3
		sheet.set_column('A:A', 5)
		sheet.set_column('B:B', 15)
		sheet.set_column('C:C', 15)
		sheet.set_column('E:E', 10)
		sheet.set_column('U:U', 10)
		n=1
		for data in self.emp_balance_ids:

			sheet.write(rowx, 0, n,content_left)
			sheet.write(rowx, 1,data.employee_id.last_name,content_left)
			sheet.write(rowx, 2,data.employee_id.name,content_left)
			sheet.write(rowx, 3,data.employee_id.identification_id,content_left)
			sheet.write(rowx, 4,data.ssnid,content_left) 
			sheet.write(rowx, 5,data.hospital_number,content_right)
			sheet.write(rowx, 6,str(data.start_date),content_right)
			sheet.write(rowx, 7,str(data.end_date),content_right)
			sheet.write(rowx, 8,str(data.total_year),content_right1)
			sheet.write(rowx, 9,data.tree_month_amount_wage,content_right) 
			sheet.write(rowx, 10,data.tree_month_amount_day,content_right)
			sheet.write(rowx, 11,data.one_day_wage,content_right)
			sheet.write(rowx, 12,data.procent,content_right)
			sheet.write(rowx, 13,data.one_day,content_right)
			sheet.write(rowx, 14,data.all_day,content_right)
			if data.company_day:
				sheet.write(rowx, 15,data.company_day,content_right)
			else:
				sheet.write(rowx, 15,'0',content_right)
			if data.nd_day:
				sheet.write(rowx, 16,data.nd_day,content_right)
			else:
				sheet.write(rowx, 16,'0',content_right)
			if data.all_wage:
				sheet.write(rowx, 17,data.all_wage,content_right)
			else:
				sheet.write(rowx, 17,'0',content_right)
			if data.company_wage:
				sheet.write(rowx, 18,data.company_wage,content_right)
			else:
				sheet.write(rowx, 18,'0',content_right)
			if data.nd_wage:
				sheet.write(rowx, 19,data.nd_wage,content_right)
			else:
				sheet.write(rowx, 19,'0',content_right)
			# sheet.write(rowx, 20,data.employee_id.bank_account_number,content_right)
			rowx+=1
			n+=1
		sheet.merge_range(rowx, 0, rowx, 7, u'Нийлбэр', theader)
		sheet.write_formula(rowx, 8, "{=SUM(I%d:I%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 9, "{=SUM(J%d:J%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 10, "{=SUM(K%d:K%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 11, "{=SUM(L%d:L%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 12, "{=SUM(M%d:M%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 13, "{=SUM(N%d:N%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 14, "{=SUM(O%d:O%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 15, "{=SUM(P%d:P%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 16, "{=SUM(Q%d:Q%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 17, "{=SUM(R%d:R%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 18, "{=SUM(S%d:S%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 19, "{=SUM(T%d:T%d)}" % (10, rowx), center_bold)
		sheet.write(rowx, 20, '', center_bold)

		rowx+=3
		sheet.merge_range(rowx, 1, rowx, 6, u'Ерөнхий нягтлан бодогч:.......................//', content_left_no)
		sheet.merge_range(rowx+1, 1, rowx+1, 6, u'Нягтлан бодогч:.......................//', content_left_no)

		sheet.merge_range(rowx-1, 9, rowx-1, 19, u'Шалгаж хүлээж авсан нийгмийн даатгалын хэлтэс(газар)-ын', content_left_no)
		sheet.merge_range(rowx, 9, rowx, 19, u'байцаагч.........................Оны.....-р сарын ..... өдөр', content_left_no)
		sheet.merge_range(rowx+1, 9, rowx+1, 19, u'....Оны.....-р сарын ..... өдөр', content_left_no)

		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
		return {
			'name': 'Export Result',
			'view_mode': 'form',
			'res_model': 'report.excel.output',
			'view_id': False,
			'type' : 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			'target': 'new',
			'nodestroy': True,
		}


	def action_move_create(self):
		move_pool = self.env['account.move']
		dep_id = self.env['hr.department']
		user_bool = self.env['res.users']
		partner_bool = self.env['res.partner']
		timenow = time.strftime('%Y-%m-%d')
		
		for slip in self:
			order_line = []
			debit_sum = 0.0
			credit_sum = 0.0
			if slip.move_id:
				raise UserError(_("System in create journal"))
			else:
				move = {
					'date': slip.invoice_date,
					'ref': slip.name,
					'journal_id': slip.journal_id.id,
				}
				# MI
			if self.company_id.id==4:
				self.env.cr.execute('''SELECT
					he.id as hr_id,
					sum(line.company_wage) as company_wage,
					sum(line.all_wage) as all_wage,
					sum(line.nd_wage) as nd_wage
					from list_wage lw 
					left join list_wage_line line ON lw.id=line.parent_id 
					left join hr_employee he ON he.id=line.employee_id
					where lw.id='''+str(slip.id)+''' 
					GROUP BY he.id
					''')
					
				origin=''
				records = self.env.cr.fetchall()
				inv_ids=[]
				company_wage =0
				nd_wage =0
				for rec in records:
					emp_pool = self.env['hr.employee'].search([('id','=',rec[0])],limit=1)
					company_wage += rec[1]
					nd_wage += rec[3]

					credit_line = (0, 0, {
					'name': emp_pool.name,
					'date': slip.invoice_date,
					'partner_id': emp_pool.partner_id.id,
					# 'branch_id': rec[17],
					'analytic_account_id': None,
					'account_id': 4605,
					'journal_id': slip.journal_id.id,
					# 'analytic_account_id' : rec[3],
					# 'period_id': 8395,
					'debit': 0,
					'credit': rec[2],
					})
					order_line.append(credit_line)
					credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']
					
				debit_line = (0, 0, {
				'name': 'ХЧТАТ',
				'date': slip.invoice_date,
				# 'analytic_account_id': rec[3],
				'partner_id': slip.invoice_partner_id.id,
				'account_id': 4552,
				'journal_id': slip.journal_id.id,
				# 'period_id': 8395,
				'debit': nd_wage,
				'credit': 0
				})
				order_line.append(debit_line)
				debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

				self.env.cr.execute('''SELECT
					hd.id as hd_id,
					sum(line.company_wage) as company_wage,
					sum(line.all_wage) as all_wage,
					sum(line.nd_wage) as nd_wage
					from list_wage lw 
					left join list_wage_line line ON lw.id=line.parent_id 
					left join hr_employee he ON he.id=line.employee_id
					left join hr_department hd ON hd.id=he.department_id
					where lw.id='''+str(slip.id)+''' 
					GROUP BY hd.id
					''')
				recs = self.env.cr.fetchall()
				for recd in recs:
					
					dep_pool = self.env['hr.department'].search([('id','=',recd[0])],limit=1)
					
					debit_line = (0, 0, {
					'name': 'ХЧТАТ зардал',
					'date': slip.invoice_date,
					'analytic_account_id': dep_pool.analytic_account_id.id,
					# 'branch_id': rec[5],
					'account_id': dep_pool.account_shi_expense_id.id,
					'journal_id': slip.journal_id.id,
					# 'period_id': 8395,
					'debit': recd[1],
					'credit': 0
					})
					order_line.append(debit_line)
					debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
				# MOTORS
			if self.company_id.id==6:
				self.env.cr.execute('''SELECT
					he.id as hr_id,
					sum(line.company_wage) as company_wage,
					sum(line.all_wage) as all_wage,
					sum(line.nd_wage) as nd_wage
					from list_wage lw 
					left join list_wage_line line ON lw.id=line.parent_id 
					left join hr_employee he ON he.id=line.employee_id
					where lw.id='''+str(slip.id)+''' 
					GROUP BY he.id
					''')
					
				origin=''
				records = self.env.cr.fetchall()
				inv_ids=[]
				company_wage =0
				nd_wage =0
				for rec in records:
					emp_pool = self.env['hr.employee'].search([('id','=',rec[0])],limit=1)
					company_wage += rec[1]
					nd_wage += rec[3]

					credit_line = (0, 0, {
					'name': emp_pool.name,
					'date': slip.invoice_date,
					'partner_id': emp_pool.partner_id.id,
					# 'branch_id': rec[17],
					'analytic_account_id': None,
					'account_id': 13426,
					'journal_id': slip.journal_id.id,
					# 'analytic_account_id' : rec[3],
					# 'period_id': 8395,
					'debit': 0,
					'credit': rec[2],
					})
					order_line.append(credit_line)
					credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']
					
				debit_line = (0, 0, {
				'name': 'ХЧТАТ',
				'date': slip.invoice_date,
				# 'analytic_account_id': rec[3],
				'partner_id': slip.invoice_partner_id.id,
				'account_id': 13360,
				'journal_id': slip.journal_id.id,
				# 'period_id': 8395,
				'debit': nd_wage,
				'credit': 0
				})
				order_line.append(debit_line)
				debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

				self.env.cr.execute('''SELECT
					hd.id as hd_id,
					sum(line.company_wage) as company_wage,
					sum(line.all_wage) as all_wage,
					sum(line.nd_wage) as nd_wage
					from list_wage lw 
					left join list_wage_line line ON lw.id=line.parent_id 
					left join hr_employee he ON he.id=line.employee_id
					left join hr_department hd ON hd.id=he.department_id
					where lw.id='''+str(slip.id)+''' 
					GROUP BY hd.id
					''')
				recs = self.env.cr.fetchall()
				for recd in recs:
					
					dep_pool = self.env['hr.department'].search([('id','=',recd[0])],limit=1)
					
					debit_line = (0, 0, {
					'name': 'ХЧТАТ зардал',
					'date': slip.invoice_date,
					'analytic_account_id': dep_pool.analytic_account_id.id,
					# 'branch_id': rec[5],
					'account_id': dep_pool.account_shi_expense_id.id,
					'journal_id': slip.journal_id.id,
					# 'period_id': 8395,
					'debit': recd[1],
					'credit': 0
					})
					order_line.append(debit_line)
					debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
			if debit_sum > (credit_sum*-1):
				debit = debit_sum - (credit_sum*-1)
				debit_line = (0, 0, {
				'name': 'Penny difference',
				'date': slip.invoice_date,
				# 'partner_id': rec[4],
				'account_id': 4645,
				'journal_id': slip.journal_id.id,
				# 'period_id': 8395,
				'debit': 0,
				'credit': debit,
				})
				order_line.append(debit_line)
				debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
			if debit_sum < (credit_sum*-1):
				credit = (credit_sum*-1) - debit_sum 
				credit_line = (0, 0, {
				'name': 'Penny difference',
				'date': slip.invoice_date,
				# 'partner_id': 1365,
				'account_id': 4645,
				'journal_id': slip.journal_id.id,
				# 'analytic_account_id' : rec[3],
				# 'period_id': 8395,
				'debit': credit,
				'credit': 0,
				})
				order_line.append(credit_line)
				credit_sum += credit_line[2]['debit'] - credit_line[2]['credit']

			move.update({'line_ids': order_line})
			move_id = move_pool.create(move)
			self.write({'move_id': move_id.id,})
			move_pool._post()
		return True

	def com_bank_acc(self,ids):
		line=self.browse(ids)
		name=''
		if line.company_id.partner_id.bank_ids:
			for acc in line.company_id.partner_id.bank_ids:
				name += acc.acc_number+' , '
		return name

	def com_bank(self,ids):
		line=self.browse(ids)
		name=''
		if line.company_id.partner_id.bank_ids:
			for acc in line.company_id.partner_id.bank_ids:
				if acc.bank_id:
					name += acc.bank_id.name+' , '
		return name

	def action_to_print(self):
		model_id = self.env['ir.model'].sudo().search([('model','=','list.wage')], limit=1)
		template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','hchtat_invoice')], limit=1)
		if template:
			res = template.sudo().print_template(self.id)
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

	def get_company_logo(self, ids):
		report_id = self.browse(ids)
		print ('report_id.move_id.company_id ',report_id.move_id.company_id)
		if report_id.move_id.company_id and not report_id.move_id.company_id.logo_web:
			raise UserError(_(u'Компаний мэдээлэл дээр логогоо сонгоно уу!'))

		image_buf = report_id.move_id.company_id.logo_web.decode('utf-8')
		image_str = '';
		if len(image_buf)>10:
			image_str = '<img alt="Embedded Image" width="550" src="data:image/png;base64,%s" />'%(image_buf)
		return image_str

	def get_move_product_line(self, ids):
		datas = []
		report_id = self.browse(ids)

		i = 1
		lines = []
		lines = report_id.emp_balance_ids
		sum1 = 0
		sum2 = 0
		sum3 = 0
		nbr = 1
		for line in lines:
			name = line.employee_id.name
			qty = 1
			price_unit = line.nd_wage
			price_subtotal = line.nd_wage
			sum2 += qty
			sum3 += price_subtotal

			temp = [
			u'<p style="text-align: center;">'+str(nbr)+u'</p>',
			u'<p style="text-align: left;">'+(name)+u'</p>',
			"{0:,.0f}".format(qty) or '',
			"{0:,.0f}".format(price_unit) or '',
			"{0:,.0f}".format(price_subtotal) or '',
			]
			nbr += 1
			datas.append(temp)
			i += 1
		
		if not datas:
			return False

		temp = [
			u'',
			u'',
			u'',
			u'<p style="text-align: center;">Дүн</p>',
			"{0:,.0f}".format(sum3) or '',
			]
		datas.append(temp)
		temp = [
			u'',
			u'',
			u'',
			u'<p style="text-align: center;">НӨАТ</p>',
			"{0:,.0f}".format(0) or '',
			]
		datas.append(temp)

		temp = [
			u'',
			u'',
			u'',
			u'<p style="text-align: center;">Дүн</p>',
			"{0:,.0f}".format(sum3) or '',
			]
		datas.append(temp)
		return datas

	def get_move_line(self, ids):
		report_id = self.browse(ids)
		headers = [
		u'№',
		u'Гүйлгээний утга',
		u'Тоо хэмжээ',
		u'Нэгж үнэ',
		u'Нийт үнэ',
		]

		datas = self.get_move_product_line(ids)
		if not datas:
			return ''
		res = {'header': headers, 'data':datas}
		return res

class ListWageLine(models.Model):
	_name = "list.wage.line"
	_description = "list wage line"

	def view_form(self):
		self.ensure_one()
		action = {
			'name':'Мөрүүд',
			'type':'ir.actions.act_window',
			'view_mode':'form',
			'res_model':'list.wage.line',
			'target':'new',
		}
		view = self.env.ref('mw_salary.view_list_wage_line_form')
		view_id = view and view.id or False
		action['view_id'] = view_id
		action['res_id'] = self.id
		return action

	parent_id = fields.Many2one('list.wage','Parent', ondelete='cascade')
	employee_id = fields.Many2one('hr.employee','Ажилтан')
	ssnid= fields.Char(u'НДД дугаар')
	hospital_number= fields.Char(u'Эмнэлгийн хуудсын дугаар')
	start_date=fields.Date(u'Эхэлсэн огноо')
	end_date=fields.Date(u'Дууссан огноо')
	total_year=fields.Float(u'Нийт НДШ төлсөн жил')
	tree_month_amount_wage=fields.Float(u'3 сарын нийлбэр цалин', digits=(0, 0))
	tree_month_amount_day=fields.Float(u'3 cарын нийлбэр хоног')
	procent=fields.Float(u'Тэтгэмж бодох хувь', digits=(0, 0))
	job_id= fields.Many2one('hr.job','Job')
	department_id= fields.Many2one('hr.department', "Department")
	all_day=fields.Integer(u'Бүх өдөр',digits=(0, 0), tracking=True)
	company_day = fields.Float(u'Ажил олгогчоос', digits=(0, 0), tracking=True)
	one_day_wage = fields.Float(u'Нэг өдрийн хөлс', digits=(0, 0), tracking=True)
	one_day = fields.Float(u'Нэг өдөрт ногдох', digits=(0, 0), tracking=True)
	nd_day = fields.Float(u'НД-аас', digits=(0, 0), store=True, compute='_compute_nd_wage')
	all_wage = fields.Float(u'Бүх олговол', digits=(0, 0), store=True, compute='_compute_nd_wage')
	company_wage = fields.Float(u'Ажил олгогчоос', digits=(0, 0), store=True, compute='_compute_nd_wage')
	nd_wage = fields.Float(u'НД-аас', digits=(0, 0), store=True, compute='_compute_nd_wage')
	employee_wage_id = fields.One2many('list.wage.detail','parent_id','Lines')
	salary_start_date = fields.Date('Цалингийн эхлэх огноо')
	salary_end_date = fields.Date('Цалингийн дуусах огноо')
	state= fields.Selection([('draft','Draft'),
				 ('done',u'done')], 'Status',readonly=True, default = 'draft', tracking=True, copy=False)


	@api.depends('all_day','one_day','company_day','nd_day')
	def _compute_nd_wage(self):
		for obj in self:
			obj.nd_day = obj.all_day - obj.company_day
			obj.all_wage = obj.all_day*obj.one_day
			obj.company_wage = obj.company_day*obj.one_day
			obj.nd_wage = obj.nd_day*obj.one_day

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		self.department_id = self.employee_id.department_id
		self.job_id = self.employee_id.job_id
		self.total_year = self.employee_id.sum_uls_year

		month = 0
		if self.parent_id.month=='1':
			month = '01'
		elif self.parent_id.month=='2':
			month = '02'
		elif self.parent_id.month=='3':
			month = '03'
		elif self.parent_id.month=='4':
			month = '04'
		elif self.parent_id.month=='5':
			month = '05'
		elif self.parent_id.month=='6':
			month = '06'
		elif self.parent_id.month=='7':
			month = '07'
		elif self.parent_id.month=='8':
			month = '08'
		elif self.parent_id.month=='9':
			month = '09'
		elif self.parent_id.month=='90':
			month = '10'
		elif self.parent_id.month=='91':
			month = '11'
		elif self.parent_id.month=='92':
			month = '12'

		ssd = str(self.parent_id.year)+'-'+str(month)+'-'+'01'
		date_s = datetime.strptime(str(ssd), DATE_FORMAT)
		date_s_salary = (date_s + relativedelta(months=-3, day=1, days=0)).strftime('%Y-%m-%d')
		date_e = (date_s + relativedelta(months=0, day=1, days=-1)).strftime('%Y-%m-%d')
		self.salary_start_date = date_s_salary
		self.salary_end_date = date_e

		if self.parent_id.is_maternity==True:
			self.procent=100
		else:
			if self.employee_id.sum_uls_year<5:
				self.procent=50
			elif self.employee_id.sum_uls_year>=5 and self.employee_id.sum_uls_year<10:
				self.procent=55
			elif self.employee_id.sum_uls_year>=10 and self.employee_id.sum_uls_year<=15:
				self.procent=60
			else:
				self.procent=75

	def button_computation(self):
		detail_pool =  self.env['list.wage.detail']
		all_wage = 0
		nd_wage = {}
		company_wage = 0

		if self.employee_wage_id:
			self.employee_wage_id.unlink()

		query="""SELECT 
			(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='TOOTS') as too,
			line.employee_id as emp_id,
			so.year as year,
			so.month as month,
			(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='WH') as hour
			FROM salary_order so
			LEFT JOIN salary_order_line line ON line.order_id=so.id
			WHERE line.employee_id=%s and so.date_invoice>='%s' and so.date_invoice<='%s' and so.type='final'"""%(self.employee_id.id,self.salary_start_date,self.salary_end_date)
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		for emp in records:
			month = 0
			if emp['month']=='1':
				month = '01'
			elif emp['month']=='2':
				month = '02'
			elif emp['month']=='3':
				month = '03'
			elif emp['month']=='4':
				month = '04'
			elif emp['month']=='5':
				month = '05'
			elif emp['month']=='6':
				month = '06'
			elif emp['month']=='7':
				month = '07'
			elif emp['month']=='8':
				month = '08'
			elif emp['month']=='9':
				month = '09'
			elif emp['month']=='90':
				month = '10'
			elif emp['month']=='91':
				month = '11'
			elif emp['month']=='92':
				month = '12'
			lsd = str(emp['year'])+'-'+str(month)+'-'+'01'
			date_s = datetime.strptime(str(lsd), DATE_FORMAT)

			date_e = (date_s + relativedelta(months=+1, day=1, days=-1)).strftime('%Y-%m-%d')

			if emp['too']>6600000:
				detail_id = detail_pool.create({
					'employee_id':emp['emp_id'],
					'amount_tootsson':6600000,
					'worked_day':emp['hour'],
					'year':emp['year'],
					'month':emp['month'],
					'parent_id':self.id,
					'line_start_date':date_s,
					'line_end_date':date_e
				})
			else:
				detail_id = detail_pool.create({
					'employee_id':emp['emp_id'],
					'amount_tootsson':emp['too'],
					'worked_day':emp['hour'],
					'year':emp['year'],
					'month':emp['month'],
					'parent_id':self.id,
					'line_start_date':date_s,
					'line_end_date':date_e
				})
		www = 0 
		hhh = 0
		for ll in self.employee_wage_id:
			if ll.amount_tootsson>6600000:
				www += 6600000
			else:
				www += ll.amount_tootsson
			self.tree_month_amount_wage = www

			l_s_date=datetime.strptime(str(ll.line_start_date), DATE_FORMAT)
			l_e_date=datetime.strptime(str(ll.line_end_date), DATE_FORMAT)
			ltimedel = l_e_date - l_s_date
			ldiff_day = ltimedel.days + 1
			l_holidays_id = self.env['hr.public.holiday'].search([('days_date','>=',ll.line_start_date),('days_date','<=',ll.line_end_date)])
			l_days = {'mon':0,'tue':1,'wed':2,'thu':3,'fri':4,'sat':5,'sun':6}
			l_delta_day = timedelta(days=1)
			ldt = l_s_date
			l_sat_count=0
			l_sun_count=0

			while ldt <= l_e_date:
				if ldt.weekday() == l_days['sat']:
					l_sat_count+=1
				if ldt.weekday() == l_days['sun']:
					l_sun_count+=1
				ldt += l_delta_day
			l_holidays=l_sat_count+l_sun_count+len(l_holidays_id)
			# ll.worked_day=ldiff_day - l_holidays
			ll.worked_day=21

			# if ll.worked_day>0:
			# 	hhh += ll.worked_day
			# else:
			# 	hhh += ll.amount_tootsson
			self.tree_month_amount_day = 63

		if self.tree_month_amount_wage>0:
			self.one_day_wage=self.tree_month_amount_wage/self.tree_month_amount_day
		if self.one_day_wage>0:
			self.one_day= self.one_day_wage * self.procent / 100

		hour_id = self.env['list.wage.line'].sudo().search([('parent_id','=',self.parent_id.id),('employee_id','=',self.employee_id.id)])
		company_day=0

		s_date=datetime.strptime(str(self.start_date), DATE_FORMAT)
		e_date=datetime.strptime(str(self.end_date), DATE_FORMAT)
		timedel = e_date - s_date
		diff_day = timedel.days + 1
		holidays_id = self.env['hr.public.holiday'].search([('days_date','>=',self.start_date),('days_date','<=',self.end_date)])
		days = {'mon':0,'tue':1,'wed':2,'thu':3,'fri':4,'sat':5,'sun':6}
		delta_day = timedelta(days=1)
		dt = s_date
		sat_count=0
		sun_count=0

		while dt <= e_date:
			if dt.weekday() == days['sat']:
				sat_count+=1
			if dt.weekday() == days['sun']:
				sun_count+=1
			dt += delta_day
		holidays=sat_count+sun_count+len(holidays_id)
		self.all_day=diff_day - holidays

class ListWageDetail(models.Model):
	_name = "list.wage.detail"
	_description = "list wage detail"

	employee_id = fields.Many2one('hr.employee','Ажилтан')
	year = fields.Char('Жил')
	month=fields.Selection([('1','January'), ('2','February'), ('3','March'), ('4','April'),
			('5','May'), ('6','June'), ('7','July'), ('8','August'), ('9','September'),
			('90','October'), ('91','November'), ('92','December')], u'Сар')
	amount_tootsson = fields.Float('Тооцсон цалин')
	worked_day = fields.Float('Ажилласан хоног')
	line_start_date = fields.Date('Эхлэх огноо')
	line_end_date = fields.Date('Дуусах огноо')
	parent_id = fields.Many2one('list.wage.line','Parent')