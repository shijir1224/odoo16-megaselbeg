# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
from datetime import datetime, timedelta
from odoo.addons.mw_base.excel import Report, Sheet, Element, Cell, formula_round

from odoo import tools
from odoo import api, fields, models
from odoo.tools.misc import get_lang

class SalaryReportFinal(models.TransientModel):
	_name = "salary.final.report"
	_description = "salary final report"

	salary_id= fields.Many2one('salary.order', 'Цалин')
	year= fields.Char(method=True, store=True, type='char', string='Жил', size=8,)
	month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
			('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
			('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар',)
	sector_ids = fields.Many2many('hr.department', string='Сектор')
	type = fields.Selection([
			('advance','Урьдчилгаа цалин'),
			('final','Сүүл цалин'),
		], string='Төрөл', required=True,index=True, change_default=True, default='final',)
	company_id = fields.Many2one('res.company', string='Компани', change_default=True,
		required=True, readonly=True, default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
	sector_id = fields.Many2one('hr.department', string='Сектор', domain=[('type', '=', 'sector')])
	is_dep = fields.Boolean('Ажилтны хэсгээр татах')
	date_from =fields.Date('Эхлэх огноо')
	date_to =fields.Date('Дуусах огноо')
	# type = fields.Selection([('working','Үндсэн'),('experiment','Туршилт'),('timer','Цагийн'),('all','Бүгл')],'Төрөл')
	
	def export_report(self):
		ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		body = Element()

		sheet = workbook.add_worksheet(u'Salary final report')
		worksheet_other = workbook.add_worksheet(u'Other info')

		file_name = 'Salary'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(10)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c4d79b')
		theader.set_num_format('#,##0')

		h2 = workbook.add_format()
		h2.set_font_size(11)
		h2.set_font('Times new roman')
		h2.set_align('center')
		h2.set_align('vcenter')

		theader1 = workbook.add_format({'bold': 1})
		theader1.set_font_size(10)
		theader1.set_font('Times new roman')
		theader1.set_align('center')
		theader1.set_align('vcenter')

		theader2 = workbook.add_format({'bold': 1})
		theader2.set_font_size(9)
		theader2.set_font('Times new roman')
		theader2.set_align('right')
		theader2.set_align('vcenter')

		theader3 = workbook.add_format({'bold': 1})
		theader3.set_font_size(9)
		theader3.set_font('Times new roman')
		theader3.set_align('left')
		theader3.set_align('vcenter')

		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_font('Times new roman')
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_bg_color('#F7FCE7')
		header.set_num_format('#,##0')

		header_wrap = workbook.add_format({'bold': 1})
		header_wrap.set_text_wrap()
		header_wrap.set_font_size(9)
		header_wrap.set_align('center')
		header_wrap.set_align('vcenter')
		header_wrap.set_border(style=1)
		header_wrap.set_bg_color('#6495ED')

		footer = workbook.add_format({'bold': 1})
		footer.set_text_wrap()
		footer.set_font_size(9)
		footer.set_align('right')
		footer.set_align('vcenter')
		footer.set_border(style=1)
		footer.set_bg_color('#F7FCE7')
		footer.set_num_format('#,##0')

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		contest_left0 = workbook.add_format()
		contest_left0.set_font_size(9)
		contest_left0.set_align('left')
		contest_left0.set_align('vcenter')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)

		center = workbook.add_format({'num_format': '###,###,###.##'})
		center.set_text_wrap()
		center.set_font('Times new roman')
		center.set_font_size(9)	 
		center.set_align('right')
		center.set_border(style=1)
		

		categ_name = workbook.add_format({'bold': 1})
		categ_name.set_font_size(9)
		categ_name.set_align('left')
		categ_name.set_align('vcenter')
		categ_name.set_border(style=1)
		categ_name.set_bg_color('#B9CFF7')

		categ_right = workbook.add_format({'bold': 1})
		categ_right.set_font_size(9)
		categ_right.set_align('right')
		categ_right.set_align('vcenter')
		categ_right.set_border(style=1)
		categ_right.set_bg_color('#B9CFF7')
		categ_right.set_num_format('#,##0.00')

		content_left = workbook.add_format({'num_format': '###,###,###.##'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(9)
		content_left.set_border(style=1)
		content_left.set_align('left')

		months=0
		if self.salary_id.month==90:
			months=10
		elif self.salary_id.month==91:
			months=11
		elif self.salary_id.month==92:
			months=12
		else:
			months=self.salary_id.month
		month=0
		if self.date_from.month==10:
			month='90'
		elif self.date_from.month==11:
			month='91'
		elif self.date_from.month==12:
			month='92'
		else:
			month=self.date_from.month
		rowx=5
		colx=10
		sheet.merge_range(rowx, 0,rowx+2,0, u'Д/д', theader),
		sheet.merge_range(rowx,1,rowx+2,1, u'Код', theader),
		sheet.merge_range(rowx,2,rowx+2,2, u'Овог', theader),
		sheet.merge_range(rowx,3,rowx+2,3, u'Нэр', theader),
		sheet.merge_range(rowx,4,rowx+2,4, u'Албан тушаал', theader),
		sheet.merge_range(rowx,5,rowx+2,5, u'Даатгуулагчийн төрөл', theader),
		sheet.merge_range(rowx,6,rowx+2,6, u'Регистрийн дугаар', theader),
		sheet.merge_range(rowx,7,rowx+2,7, u'Татвар төлөгчийн дугаар', theader),		
		sheet.merge_range(rowx,8,rowx+2,8, u'Жил', theader),		
		sheet.merge_range(rowx,9,rowx+2,9, u'Сар', theader),		

		sheet.merge_range(rowx-10,0,rowx-10,3, u'Компанийн нэр:'+ ' ' + self.company_id.name, theader3),
		# sheet.merge_range(rowx-6,0,rowx-6,15, self.salary_id.name, theader1),
		sheet.merge_range(rowx-4,11,rowx-4,13, u'Тайлан хэвлэсэн огноо:', theader2),
		sheet.merge_range(rowx-4,14,rowx-4,15, time.strftime('%Y-%m-%d'), theader3),

		sect_ids = []
		for sec in self.sector_ids:
			sect_ids.append(sec.id)
		sec_ids = str(sect_ids)
		sec_ids = sec_ids.replace("[", "(")
		sec_ids = sec_ids.replace("]", ")")
		if self.is_dep==True:
			if self.sector_ids:
				query_header="""SELECT 
					cat.name as name,
					cat.id as cat_id
					FROM salary_order so
					LEFT JOIN salary_order_line line ON line.order_id=so.id
					LEFT JOIN salary_order_line_line ll ON ll.order_line_id1=line.id
					LEFT JOIN hr_allounce_deduction_category cat ON cat.id=ll.category_id
					WHERE so.year='%s' and so.month='%s' and so.company_id='%s' and so.type='%s' and so.sector_id in %s and cat.name is not null
					group by so.year, so.month, so.company_id, cat.name, cat.number, cat.id
					ORDER BY cat.number"""%(self.date_to.year, month, self.company_id.id,self.type, sec_ids)
				self.env.cr.execute(query_header)
				rec_query_header = self.env.cr.dictfetchall()
			else:
				query_header="""SELECT 
					cat.name as name,
					cat.id as cat_id
					FROM salary_order so
					LEFT JOIN salary_order_line line ON line.order_id=so.id
					LEFT JOIN salary_order_line_line ll ON ll.order_line_id1=line.id
					LEFT JOIN hr_allounce_deduction_category cat ON cat.id=ll.category_id
					WHERE so.year='%s' and so.month='%s' and so.company_id='%s' and so.type='%s' and cat.name is not null
					group by so.year, so.month, so.company_id, cat.name, cat.number, cat.id
					ORDER BY cat.number"""%(self.date_to.year, month, self.company_id.id,self.type)
				self.env.cr.execute(query_header)
				rec_query_header = self.env.cr.dictfetchall()
			col=10
			for head in rec_query_header:
				sheet.merge_range(rowx,col,rowx+2,col, head['name'], theader),
				col+=1

			sheet.freeze_panes(9, 9)
			save_row=11
			n=1
			rowx+=3
			
			sheet.set_column('A:A', 5)
			sheet.set_column('B:B', 7)
			sheet.set_column('C:C', 15)
			sheet.set_column('D:D', 15)
			sheet.set_column('E:E', 25)
			sheet.set_column('G:H', 11)
			if self.sector_ids:
				query="""SELECT 
					rb.id,
					rb.name
					FROM salary_order so
					LEFT JOIN salary_order_line line ON line.order_id=so.id
					LEFT JOIN hr_employee hr ON hr.id=line.employee_id
					LEFT JOIN hr_department rb ON rb.id=hr.department_id
					WHERE so.date_invoice>='%s' and so.date_invoice<='%s' and so.company_id='%s' and so.type='%s'  and so.sector_id in %s
					group by rb.id, rb.name"""%(self.date_from, self.date_to, self.company_id.id,self.type, sec_ids)
				self.env.cr.execute(query)
				recs = self.env.cr.fetchall()
			else:
				query="""SELECT 
					rb.id,
					rb.name
					FROM salary_order so
					LEFT JOIN salary_order_line line ON line.order_id=so.id
					LEFT JOIN hr_employee hr ON hr.id=line.employee_id
					LEFT JOIN hr_department rb ON rb.id=hr.department_id
					WHERE so.date_invoice>='%s' and so.date_invoice<='%s' and so.company_id='%s' and so.type='%s'
					group by rb.id, rb.name"""%(self.date_from, self.date_to, self.company_id.id,self.type)
				self.env.cr.execute(query)
				recs = self.env.cr.fetchall()
			ss_club = False
			temp_dict = {}
			lang = self.env.user.lang or get_lang(self.env).code
			month_ex=0
			for rec in recs:
				if rec[0]:
					department = self.env['hr.department'].browse(rec[0])
					if department.parent_id:
						sheet.merge_range(rowx,0,rowx,7, str(department.parent_id.name)+'/'+str(department.name), header),
					else:
						sheet.merge_range(rowx,0,rowx,7, str(department.name), header),
					# sheet.merge_range(rowx,8,rowx,col, '', header),
					# sheet.merge_range(rowx,5,rowx,30, '', header),
					rowx+=1
					if self.sector_ids:
						query="""SELECT  
							COALESCE(he.name->> '%s', he.name->>'en_US') as he_name,
							--he.name as he_name,
							hd.name as hd_name,
							he.last_name as last_name ,
							he.identification_id as identification_id,
							hj.id as hj_id,
							he.id as he_id,
							--so.date_invoice as so_date,
							so.year as year,
							so.month as month,
							he.ttd_number as ttd_number,
							he.passport_id as register,
							it.code as code,
							line.id as sol_id
							FROM salary_order so
							LEFT JOIN salary_order_line line ON line.order_id=so.id
							LEFT JOIN hr_employee he ON he.id=line.employee_id
							LEFT JOIN hr_department hd ON he.department_id=hd.id
							LEFT JOIN hr_job hj ON hj.id=he.job_id
							LEFT JOIN hr_contract hc ON hc.employee_id=he.id
							LEFT JOIN insured_type it ON line.insured_type_id=it.id
							WHERE so.date_invoice>='%s' and so.date_invoice<='%s' and so.company_id='%s' and hd.id=%s  and so.type='%s' and so.sector_id in %s and line.employee_id is not null
							GROUP BY he.name, hd.name, he.last_name, he.identification_id, hj.id, he.id,so.year, so.month, he.ttd_number, he.passport_id, it.code, line.id 
							ORDER BY he.name, so.year, so.month
							"""%(lang,self.date_from, self.date_to, self.company_id.id,rec[0],self.type, sec_ids)
						self.env.cr.execute(query)
					else:
						query="""SELECT  
							COALESCE(he.name->> '%s', he.name->>'en_US') as he_name,
							--he.name as he_name,
							hd.name as hd_name,
							he.last_name as last_name ,
							he.identification_id as identification_id,
							hj.id as hj_id,
							he.id as he_id,
							--so.date_invoice as so_date,
							so.year as year,
							so.month as month,
							he.ttd_number as ttd_number,
							he.passport_id as register,
							it.code as code,
							line.id as sol_id
							FROM salary_order so
							LEFT JOIN salary_order_line line ON line.order_id=so.id
							LEFT JOIN hr_employee he ON he.id=line.employee_id
							LEFT JOIN hr_department hd ON he.department_id=hd.id
							LEFT JOIN hr_job hj ON hj.id=he.job_id
							LEFT JOIN hr_contract hc ON hc.employee_id=he.id
							LEFT JOIN insured_type it ON line.insured_type_id=it.id
							WHERE so.date_invoice>='%s' and so.date_invoice<='%s' and so.company_id='%s' and hd.id=%s  and so.type='%s' and line.employee_id is not null
							GROUP BY he.name, hd.name, he.last_name, he.identification_id, hj.id, he.id,  so.year, so.month, he.ttd_number, he.passport_id, it.code, line.id 
							ORDER BY he.name, so.year, so.month
							"""%(lang,self.date_from, self.date_to, self.company_id.id,rec[0],self.type)
						self.env.cr.execute(query)
				
					records = self.env.cr.dictfetchall()
					
					for record in records:
						if record['month']=='90':
							month_ex='10'
						elif record['month']=='91':
							month_ex='11'
						elif record['month']=='92':
							month_ex='12'
						else:
							month_ex=record['month']
						if not ss_club:
							# save_row = rowx+1
							ss_club=True
						job_id = self.env['hr.job'].search([('id','=',record['hj_id'])],limit=1)
						sheet.write(rowx, 0, n,content_left)
						sheet.write(rowx, 1, record['identification_id'],content_left)
						sheet.write(rowx, 2, record['last_name'],content_left)
						sheet.write(rowx, 3, record['he_name'],content_left)
						# sheet.write(rowx, 4,record['hd_name'],content_left)
						sheet.write(rowx, 4, job_id.name,content_left)
						sheet.write(rowx, 5, record['code'],center)
						sheet.write(rowx, 6, record['register'],content_left)
						sheet.write(rowx, 7, record['ttd_number'],content_left)
						sheet.write(rowx, 8, record['year'],content_left)
						sheet.write(rowx, 9, month_ex,content_left)
						colx=10
						for head in rec_query_header:
							query_line="""SELECT 
									sum(ll.amount) as amount
									FROM salary_order so
									LEFT JOIN salary_order_line line ON line.order_id=so.id
									LEFT JOIN salary_order_line_line ll ON ll.order_line_id1=line.id
									LEFT JOIN hr_employee hr ON hr.id=line.employee_id
									LEFT JOIN hr_allounce_deduction_category cat ON cat.id=ll.category_id
									WHERE ll.order_line_id1=%s and cat.id=%s
									GROUP BY cat.id
									ORDER BY cat.number"""%(record['sol_id'],head['cat_id'])
							self.env.cr.execute(query_line)
							recs_line = self.env.cr.dictfetchall()
							if recs_line:
								for line in recs_line:
									sheet.write(rowx, colx,line['amount'],center)
									colx+=1
							else:
								sheet.write(rowx, colx,'0',center)
								colx+=1
						rowx+=1
						n+=1
					ss_club = False
			col=10
			sheet.merge_range(rowx, 0, rowx, 10, u'НИЙТ', footer)
			l=11
		
			while l <= colx-1:
				sheet.write_formula(rowx, l, '{=SUM('+self._symbol(save_row-1, l) +':'+ self._symbol(rowx-1, l)+')}', footer)
				l+=1
			# col=10
			# for head in rec_query_header:
			# 	sheet.merge_range(rowx,0,rowx,7, u"Нийт", header)
			# 	sheet.write_formula(rowx, col, '{=SUM('+self._symbol(save_row-1, col) +':'+ self._symbol(rowx-1, col)+')}', footer)
			# 	col+=1
		else:
			if self.sector_ids:
				query_header="""SELECT 
					cat.name as name,
					cat.id as cat_id
					FROM salary_order so
					LEFT JOIN salary_order_line line ON line.order_id=so.id
					LEFT JOIN salary_order_line_line ll ON ll.order_line_id1=line.id
					LEFT JOIN hr_allounce_deduction_category cat ON cat.id=ll.category_id
					WHERE so.year='%s' and so.month='%s' and so.company_id='%s' and so.type='%s' and so.sector_id in %s and cat.name is not null
					group by so.year, so.month, so.company_id, cat.name, cat.number, cat.id
					ORDER BY cat.number"""%(self.date_from.year,month, self.company_id.id,self.type, sec_ids)
				self.env.cr.execute(query_header)
				rec_query_header = self.env.cr.dictfetchall()
			else:
				query_header="""SELECT 
					cat.name as name,
					cat.id as cat_id
					FROM salary_order so
					LEFT JOIN salary_order_line line ON line.order_id=so.id
					LEFT JOIN salary_order_line_line ll ON ll.order_line_id1=line.id
					LEFT JOIN hr_allounce_deduction_category cat ON cat.id=ll.category_id
					WHERE so.year='%s' and so.month='%s' and so.company_id='%s' and so.type='%s' and cat.name is not null
					group by so.year, so.month, so.company_id, cat.name, cat.number, cat.id
					ORDER BY cat.number"""%(self.date_from.year, month, self.company_id.id,self.type)
				self.env.cr.execute(query_header)
				rec_query_header = self.env.cr.dictfetchall()
			col=10
			for head in rec_query_header:
				sheet.merge_range(rowx,col,rowx+2,col, head['name'], theader),
				col+=1

			sheet.freeze_panes(8, 8)
			save_row=10
			n=1
			rowx+=3
			
			sheet.set_column('A:A', 5)
			sheet.set_column('B:B', 7)
			sheet.set_column('C:C', 15)
			sheet.set_column('D:D', 15)
			sheet.set_column('E:E', 25)
			sheet.set_column('G:H', 11)
			if self.sector_ids:
				query="""SELECT 
					rb.id,
					rb.name
					FROM salary_order so
					LEFT JOIN salary_order_line line ON line.order_id=so.id
					LEFT JOIN hr_employee hr ON hr.id=line.employee_id
					LEFT JOIN hr_department rb ON rb.id=so.sector_id
					WHERE so.date_invoice>='%s' and so.date_invoice<='%s' and so.company_id='%s' and so.type='%s'  and so.sector_id in %s
					group by rb.id, rb.name"""%(self.date_from, self.date_to, self.company_id.id,self.type, sec_ids)
				self.env.cr.execute(query)
				recs = self.env.cr.fetchall()
			else:
				query="""SELECT 
					rb.id,
					rb.name
					FROM salary_order so
					LEFT JOIN salary_order_line line ON line.order_id=so.id
					LEFT JOIN hr_employee hr ON hr.id=line.employee_id
					LEFT JOIN hr_department rb ON rb.id=hr.department_id
					WHERE so.date_invoice>='%s' and so.date_invoice<='%s' and so.company_id='%s' and so.type='%s'
					group by rb.id, rb.name"""%(self.date_from, self.date_to, self.company_id.id,self.type)
				self.env.cr.execute(query)
				recs = self.env.cr.fetchall()
			ss_club = False
			temp_dict = {}
			lang = self.env.user.lang or get_lang(self.env).code
			for rec in recs:
				if rec[0]:
					department = self.env['hr.department'].browse(rec[0])
					if department.parent_id:
						sheet.merge_range(rowx,0,rowx,7, str(department.parent_id.name)+'/'+str(department.name), header),
					else:
						sheet.merge_range(rowx,0,rowx,7, str(department.name), header),
					# sheet.merge_range(rowx,8,rowx,col, '', header),
					# sheet.merge_range(rowx,5,rowx,30, '', header),
					rowx+=1
					if self.sector_ids:
						query="""SELECT 
							COALESCE(he.name->> '%s', he.name->>'en_US') as he_name,
							hd.name as hd_name,
							he.last_name as last_name ,
							he.identification_id as identification_id,
							hj.id as hj_id,
							he.id as he_id,
							--so.date_invoice as so_date,
							so.year as year,
							so.month as month,
							he.ttd_number as ttd_number,
							he.passport_id as register,
							it.code as code,
							line.id as sol_id
							FROM salary_order so
							LEFT JOIN salary_order_line line ON line.order_id=so.id
							LEFT JOIN hr_employee he ON he.id=line.employee_id
							LEFT JOIN hr_department hd ON so.sector_id=hd.id
							LEFT JOIN hr_job hj ON hj.id=he.job_id
							LEFT JOIN hr_contract hc ON hc.employee_id=he.id
							LEFT JOIN insured_type it ON line.insured_type_id=it.id
							WHERE so.date_invoice>='%s' and so.date_invoice<='%s' and so.company_id='%s' and hd.id=%s  and so.type='%s' and so.sector_id in %s and line.employee_id is not null
							GROUP BY he.name, hd.name, he.last_name, he.identification_id, hj.id, he.id, so.year, so.month, he.ttd_number, he.passport_id, it.code, line.id 
							ORDER BY he.name, so.year, so.month
							"""%(lang, self.date_from, self.date_to, self.company_id.id,rec[0],self.type, sec_ids)
						self.env.cr.execute(query)
					else:
						query="""SELECT 
							COALESCE(he.name->> '%s', he.name->>'en_US') as he_name,
							hd.name as hd_name,
							he.last_name as last_name ,
							he.identification_id as identification_id,
							hj.id as hj_id,
							he.id as he_id,
							--so.date_invoice as so_date,
							so.year as year,
							so.month as month,
							he.ttd_number as ttd_number,
							he.passport_id as register,
							it.code as code,
							line.id as sol_id
							FROM salary_order so
							LEFT JOIN salary_order_line line ON line.order_id=so.id
							LEFT JOIN hr_employee he ON he.id=line.employee_id
							LEFT JOIN hr_department hd ON he.department_id=hd.id
							LEFT JOIN hr_job hj ON hj.id=he.job_id
							LEFT JOIN hr_contract hc ON hc.employee_id=he.id
							LEFT JOIN insured_type it ON line.insured_type_id=it.id
							WHERE so.date_invoice>='%s' and so.date_invoice<='%s' and so.company_id='%s' and hd.id=%s  and so.type='%s' and line.employee_id is not null
							GROUP BY he.name, hd.name, he.last_name, he.identification_id, hj.id, he.id, so.year, so.month, he.ttd_number, he.passport_id, it.code, line.id 
							ORDER BY he.name, so.year, so.month
							"""%(lang, self.date_from, self.date_to, self.company_id.id,rec[0],self.type)
						self.env.cr.execute(query)
				
					records = self.env.cr.dictfetchall()
					for record in records:
						if record['month']=='90':
							month_ex='10'
						elif record['month']=='91':
							month_ex='11'
						elif record['month']=='92':
							month_ex='12'
						else:
							month_ex=record['month']
						if not ss_club:
							# save_row = rowx+1
							ss_club=True
						job_id = self.env['hr.job'].search([('id','=',record['hj_id'])],limit=1)
						sheet.write(rowx, 0, n,content_left)
						sheet.write(rowx, 1, record['identification_id'],content_left)
						sheet.write(rowx, 2, record['last_name'],content_left)
						sheet.write(rowx, 3, record['he_name'], content_left)
						# sheet.write(rowx, 4,record['hd_name'],content_left)
						sheet.write(rowx, 4, job_id.name,content_left)
						sheet.write(rowx, 5, record['code'],center)
						sheet.write(rowx, 6, record['register'],content_left)
						sheet.write(rowx, 7, record['ttd_number'],content_left)
						sheet.write(rowx, 8, record['year'],content_left)
						sheet.write(rowx, 9, month_ex,content_left)
						colx=10
						for head in rec_query_header:
							query_line="""SELECT 
									sum(ll.amount) as amount
									FROM salary_order so
									LEFT JOIN salary_order_line line ON line.order_id=so.id
									LEFT JOIN salary_order_line_line ll ON ll.order_line_id1=line.id
									LEFT JOIN hr_employee hr ON hr.id=line.employee_id
									LEFT JOIN hr_allounce_deduction_category cat ON cat.id=ll.category_id
									WHERE ll.order_line_id1=%s and cat.id=%s
									GROUP BY cat.id
									ORDER BY cat.number"""%(record['sol_id'],head['cat_id'])
							self.env.cr.execute(query_line)
							recs_line = self.env.cr.dictfetchall()
							if recs_line:
								for line in recs_line:
									sheet.write(rowx, colx,line['amount'],center)
									colx+=1
							else:
								sheet.write(rowx, colx,'0',center)
								colx+=1
						rowx+=1
						n+=1
					ss_club = False
			col=10
			sheet.merge_range(rowx, 0, rowx, 10, u'НИЙТ', footer)
			l=11
		
			while l <= colx-1:
				sheet.write_formula(rowx, l, '{=SUM('+self._symbol(save_row-1, l) +':'+ self._symbol(rowx-1, l)+')}', footer)
				l+=1
			# for head in rec_query_header:
			# 	sheet.merge_range(rowx,0,rowx,7, u"Нийт", header)
			# 	sheet.write_formula(rowx, col, '{=SUM('+self._symbol(save_row-1, col) +':'+ self._symbol(rowx-1, col)+')}', footer)
			# 	col+=1
		# sheet.write(rowx, 2, u'Бэлтгэсэн:', h2)
		# sheet.merge_range(rowx, 3, rowx, 5, u'Нягтлан бодогч:........................//'%(self.salary_id.preparatory.last_name[:1],self.salary_id.preparatory.name), h2)

		# sheet.write(rowx+1, 2, u'Хянасан:', h2)
		# sheet.merge_range(rowx+1, 3, rowx+1, 5, u':......................//'%(self.salary_id.compute_controller.job_id.name,self.salary_id.compute_controller.last_name[:1],self.salary_id.compute_controller.name), h2)
		
		# sheet.write(rowx+2, 2, u'Баталсан:', h2)
		# sheet.merge_range(rowx+2, 3, rowx+2, 5, u'Гүйцэтгэх захирал:...................//'%(self.salary_id.done_director.last_name[:1],self.salary_id.done_director.name), h2)
		
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


	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)
	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol

