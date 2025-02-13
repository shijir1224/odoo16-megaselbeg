# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
from datetime import datetime, timedelta

from odoo import tools
from odoo import api, fields, models
from odoo.tools.misc import get_lang


class BankReport(models.TransientModel):
	_name = "bank.report"
	_description = "bank report"

	company_id = fields.Many2one('res.company', string='Компани', change_default=True,
		required=True, readonly=True, default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
	sector_ids = fields.Many2many('hr.department', string='Сектор')
	salary_id= fields.Many2one('salary.order', 'Цалин')
	year= fields.Char(method=True, store=True, type='char', string='Жил', size=8,required=True)
	month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
			('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
			('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар',required=True)
	type = fields.Selection([
			('advance','Урьдчилгаа цалин'),
			('final','Сүүл цалин'),
		], string='Төрөл', required=True,index=True, change_default=True, default='final',)
	bank_id = fields.Many2one('res.bank', u'Банк')
	is_not_account = fields.Boolean('Дансгүй ажилчид татах')

	
	def export_report(self):
		ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		sheet = workbook.add_worksheet(u'Salary bank report')

		file_name = 'Банкинд илгээх тайлан'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(10)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#6495ED')

		theaderkhas = workbook.add_format({'bold': 1})
		theaderkhas.set_font_size(10)
		theaderkhas.set_text_wrap()
		theaderkhas.set_font('Times new roman')
		theaderkhas.set_align('center')
		theaderkhas.set_align('vcenter')
		theaderkhas.set_border(style=1)
		theaderkhas.set_bg_color('#D3D3D3')

		theader1 = workbook.add_format({'bold': 1})
		theader1.set_font_size(10)
		theader1.set_font('Times new roman')
		theader1.set_align('left')
		theader1.set_align('vcenter')

		theader1khas = workbook.add_format({})
		theader1khas.set_font_size(10)
		theader1khas.set_font('Times new roman')
		theader1khas.set_align('left')
		theader1khas.set_align('vcenter')

		theaderu = workbook.add_format({'bold': 1})
		theaderu.set_font_size(10)
		theaderu.set_font('Times new roman')
		theaderu.set_align('right')
		theaderu.set_align('vcenter')

		theader4 = workbook.add_format({'bold': 1})
		theader4.set_font_size(10)
		theader4.set_font('Times new roman')
		theader4.set_align('center')
		theader4.set_align('vcenter')

		theader2 = workbook.add_format({'bold': 1})
		theader2.set_font_size(11)
		theader2.set_font('Times new roman')
		theader2.set_align('center')
		theader2.set_align('vcenter')

		theader3 = workbook.add_format({'bold': 1})
		theader3.set_font_size(11)
		theader3.set_font('Times new roman')
		theader3.set_align('left')
		theader3.set_align('vcenter')

		theader3khas = workbook.add_format({'bold': 1})
		theader3khas.set_font_size(11)
		theader3khas.set_font('Times new roman')
		theader3khas.set_align('center')
		theader3khas.set_align('vcenter')

		header = workbook.add_format({'bold': 1,'num_format': '###,###,###'})
		header.set_font_size(9)
		header.set_font('Times new roman')
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_bg_color('#A8C3F4')

		fooder = workbook.add_format({'bold': 1,'num_format': '###,###,###'})
		fooder.set_font_size(9)
		fooder.set_font('Times new roman')
		fooder.set_align('right')
		fooder.set_border(style=1)
		fooder.set_bg_color('#A8C3F4')

		fooderkhas = workbook.add_format({'bold': 1,'num_format': '###,###,###'})
		fooderkhas.set_font_size(9)
		fooderkhas.set_font('Times new roman')
		fooderkhas.set_align('right')
		fooderkhas.set_border(style=1)
		fooderkhas.set_bg_color('#E5E4E2')

		contest_left = workbook.add_format({'num_format': '###,###,###'})
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		contest_left1 = workbook.add_format({'num_format': '###,###,###.##'})
		contest_left1.set_text_wrap()
		contest_left1.set_font_size(9)
		contest_left1.set_font('Times new roman')
		contest_left1.set_align('right')
		contest_left1.set_border(style=1)

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)
		contest_center.set_num_format('#,##0.00')
		if self.bank_id.bic =='KHAS':
			if self.month=='90':
				month='10'
			elif self.month=='91':
				month='11'
			elif self.month=='92':
				month='12'
			else:
				month=self.month
					# GET warehouse loc ids
			rowx=0
			save_row=7
			sheet.merge_range(rowx+0,0,rowx+0,4, u'ЦАЛИН АВАХ АЖИЛТНУУДЫН НЭРС', theader3khas),
			sheet.merge_range(rowx+2,0,rowx+2,1, u'Байгууллагын нэр:', theader1khas),
			sheet.merge_range(rowx+2,2,rowx+2,3, self.company_id.name, theader1khas),
			sheet.merge_range(rowx+3,0,rowx+3,1, u'Байгууллагын хаяг:', theader1khas),
			sheet.merge_range(rowx+5,0,rowx+5,1, u'Огноо:', theader1khas),
			sheet.write(rowx+5,2, time.strftime('%Y-%m-%d'), theader1khas),
			sheet.merge_range(rowx+7,0,rowx+7,1, u'Гүйлгээний утга:', theader1khas),
			sheet.merge_range(rowx+7,2,rowx+7,4, 'Картаар тавих'+' '+self.year+' '+month+' '+'сарын цалинг шилжүүлэв' , theader1khas),
			month=0
			

			rowx=9

			sheet.write(rowx+1, 0, u'Д/д', theaderkhas),
			sheet.write(rowx+1, 1, u'Ажилтан', theaderkhas),
			sheet.write(rowx+1, 2, u'Дансны дугаар', theaderkhas),
			sheet.write(rowx+1, 3, u'Валют', theaderkhas),
			sheet.write(rowx+1, 4, u'Гарт олгох', theaderkhas),
				
			rowx+=1
			
			sheet.set_column('A:A', 5)
			sheet.set_column('B:B', 25)
			sheet.set_column('C:C', 15)
			sheet.set_column('D:D', 15)
			sheet.set_column('E:E', 15)
			sheet.set_column('F:F', 15)

			# domain = [('sector_id','in',self.sector_ids.ids)]
			
			# sec_ids = self.env['hr.department'].sudo().search([domain])
			sect_ids = []
			for sec in self.sector_ids:
				sect_ids.append(sec.id)
			sec_ids = str(sect_ids)
			sec_ids = sec_ids.replace("[", "(")
			sec_ids = sec_ids.replace("]", ")")
			lang = self.env.user.lang or get_lang(self.env).code
			
			if self.is_not_account==True:
				if self.sector_ids:
					query="""SELECT 
						COALESCE(he.name->> '%s', he.name->>'en_US') as he_name,
						--he.name,
						he.last_name,
						he.passport_id,
						line.amount_net,
						he.id,
						he.account_number,
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='NETU'),
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='RNET')
						FROM salary_order so
						LEFT JOIN salary_order_line line ON line.order_id=so.id
						LEFT JOIN hr_employee he ON he.id=line.employee_id
						WHERE so.year='%s' and so.month='%s' and so.type='%s' and so.company_id=%s and so.sector_id in %s  and he.bank_id is null and he.id is not null
						ORDER BY he.name"""%(lang,self.year,self.month, self.type,self.company_id.id, sec_ids)
					self.env.cr.execute(query)
					records = self.env.cr.fetchall()
				else:
					query="""SELECT 
						COALESCE(he.name->> '%s', he.name->>'en_US') as he_name,
						--he.name,
						he.last_name,
						he.passport_id,
						line.amount_net,
						he.id,
						he.account_number,
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='NETU'),
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='RNET')
						FROM salary_order so
						LEFT JOIN salary_order_line line ON line.order_id=so.id
						LEFT JOIN hr_employee he ON he.id=line.employee_id
						WHERE so.year='%s' and so.month='%s' and so.type='%s' and so.company_id=%s and he.bank_id is null and he.id is not null
						ORDER BY he.name"""%(lang,self.year,self.month,self.type, self.company_id.id)
					self.env.cr.execute(query)
					records = self.env.cr.fetchall()
			else:
				if self.sector_ids:
					query="""SELECT
						COALESCE(he.name->> '%s', he.name->>'en_US') as he_name,
 
						--he.name,
						he.last_name,
						he.passport_id,
						line.amount_net,
						he.id,
						he.account_number,
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='NETU'),
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='RNET')
						FROM salary_order so
						LEFT JOIN salary_order_line line ON line.order_id=so.id
						LEFT JOIN hr_employee he ON he.id=line.employee_id
						WHERE so.year='%s' and so.month='%s' and he.bank_id=%s and so.type='%s' and so.company_id=%s and so.sector_id in %s
						ORDER BY he.name"""%(lang,self.year,self.month,self.bank_id.id,self.type, self.company_id.id, sec_ids)
					self.env.cr.execute(query)
					records = self.env.cr.fetchall()
				else:
					query="""SELECT 
						COALESCE(he.name->> '%s', he.name->>'en_US') as he_name,

						--he.name,
						he.last_name,
						he.passport_id,
						line.amount_net,
						he.id,
						he.account_number,
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='NETU'),
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='RNET')
						FROM salary_order so
						LEFT JOIN salary_order_line line ON line.order_id=so.id
						LEFT JOIN hr_employee he ON he.id=line.employee_id
						WHERE so.year='%s' and so.month='%s' and he.bank_id=%s and so.type='%s' and so.company_id=%s
						ORDER BY he.name"""%(lang,self.year,self.month,self.bank_id.id,self.type, self.company_id.id)
					self.env.cr.execute(query)
					records = self.env.cr.fetchall()
			rowx+=1
			n=1
			for record in records:	  
				if self.is_not_account==True:
					sheet.write(rowx, 0,n,contest_left)
					sheet.write(rowx, 1,record['he_name']+' '+record[1],contest_left)
					sheet.write(rowx, 2,record[5],contest_left)
					sheet.write(rowx, 3,"MNT",contest_left)
					if self.type=='advance':
						if not record[6]:
							continue
						sheet.write(rowx, 4,record[6],contest_center)
					else:
						if not record[7]:
							continue
						sheet.write(rowx, 4,record[7] ,contest_center)
					# sheet.write(rowx, 4,record[5],contest_center)
					# sheet.write(rowx, 5,'',contest_left1)
				else:
					sheet.write(rowx, 0,n,contest_left)
					sheet.write(rowx, 1,record[0]+' '+record[1],contest_left)
					sheet.write(rowx, 2,record[5],contest_left)
					sheet.write(rowx, 3,"MNT",contest_left)
					if self.type=='advance':
						if not record[6]:
							continue
						sheet.write(rowx, 4,record[6],contest_center)
					else:
						if not record[7]:
							continue						
						sheet.write(rowx, 4,record[7],contest_center)
				rowx+=1
				n+=1
			sheet.merge_range(rowx,0,rowx,3, u"Нийт", fooderkhas)
			sheet.write_formula(rowx, 4, '{=SUM('+self._symbol(save_row-1, 4) +':'+ self._symbol(rowx-1, 4)+')}', fooderkhas)

		else:
			# GET warehouse loc ids
			rowx=0
			save_row=7
			sheet.merge_range(rowx+0,0,rowx+0,3, u'Байгууллагын нэр:'+ ' ' + self.company_id.name, theader3),
			sheet.merge_range(rowx+4,0,rowx+4,2, time.strftime('%Y-%m-%d'), theader1),
			sheet.merge_range(rowx+4,3,rowx+4,5, self.bank_id.name, theaderu),
			month=0
			if self.month=='90':
				month='10'
			elif self.month=='91':
				month='11'
			elif self.month=='92':
				month='12'
			else:
				month=self.month

			if self.type=='final':
				sheet.merge_range(rowx+2,0,rowx+2,5, self.year +u'  ОНЫ  '+ month+u' -Р САРЫН СҮҮЛ ЦАЛИН', theader2),
			elif self.type=='advance':
				sheet.merge_range(rowx+2,0,rowx+2,5, self.year +u'  ОНЫ  '+ month+u' -Р САРЫН УРЬДЧИЛГАА ЦАЛИН', theader2),
			rowx=4

			sheet.write(rowx+1, 0, u'№', theader),
			sheet.write(rowx+1, 1, u'Овог', theader),
			sheet.write(rowx+1, 2, u'Нэр', theader),
			sheet.write(rowx+1, 3, u'Регистр', theader),
			sheet.write(rowx+1, 4, u'Дансны дугаар', theader),
			sheet.write(rowx+1, 5, u'Цалингийн дүн', theader),
				
			rowx+=1
			
			sheet.set_column('A:A', 5)
			sheet.set_column('B:B', 15)
			sheet.set_column('C:C', 15)
			sheet.set_column('D:D', 15)
			sheet.set_column('E:E', 15)
			sheet.set_column('F:F', 15)

			# domain = [('sector_id','in',self.sector_ids.ids)]
			
			# sec_ids = self.env['hr.department'].sudo().search([domain])
			sect_ids = []
			for sec in self.sector_ids:
				sect_ids.append(sec.id)
			sec_ids = str(sect_ids)
			sec_ids = sec_ids.replace("[", "(")
			sec_ids = sec_ids.replace("]", ")")
			lang = self.env.user.lang or get_lang(self.env).code

			if self.is_not_account==True:
				if self.sector_ids:
					query="""SELECT 
						COALESCE(he.name->> '%s', he.name->>'en_US') as he_name,

						--he.name,
						he.last_name,
						he.passport_id,
						line.amount_net,
						he.id,
						he.account_number,
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='NETU'),
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='RNET')
						FROM salary_order so
						LEFT JOIN salary_order_line line ON line.order_id=so.id
						LEFT JOIN hr_employee he ON he.id=line.employee_id
						WHERE so.year='%s' and so.month='%s' and so.type='%s' and so.company_id=%s and so.sector_id in %s  and he.bank_id is null and he.id is not null
						ORDER BY he.name"""%(lang,self.year,self.month, self.type,self.company_id.id, sec_ids)
					self.env.cr.execute(query)
					records = self.env.cr.fetchall()
				else:
					query="""SELECT 
						COALESCE(he.name->> '%s', he.name->>'en_US') as he_name,

						--he.name,
						he.last_name,
						he.passport_id,
						line.amount_net,
						he.id,
						he.account_number,
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='NETU'),
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='RNET')
						FROM salary_order so
						LEFT JOIN salary_order_line line ON line.order_id=so.id
						LEFT JOIN hr_employee he ON he.id=line.employee_id
						WHERE so.year='%s' and so.month='%s' and so.type='%s' and so.company_id=%s and he.bank_id is null and he.id is not null
						ORDER BY he.name"""%(lang,self.year,self.month,self.type, self.company_id.id)
					self.env.cr.execute(query)
					records = self.env.cr.fetchall()
			else:
				if self.sector_ids:
					query="""SELECT 
						COALESCE(he.name->> '%s', he.name->>'en_US') as he_name,

						--he.name,
						he.last_name,
						he.passport_id,
						line.amount_net,
						he.id,
						he.account_number,
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='NETU'),
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='RNET')
						FROM salary_order so
						LEFT JOIN salary_order_line line ON line.order_id=so.id
						LEFT JOIN hr_employee he ON he.id=line.employee_id
						WHERE so.year='%s' and so.month='%s' and he.bank_id=%s and so.type='%s' and so.company_id=%s and so.sector_id in %s
						ORDER BY he.name"""%(lang, self.year,self.month,self.bank_id.id,self.type, self.company_id.id, sec_ids)
					self.env.cr.execute(query)
					records = self.env.cr.fetchall()
				else:
					query="""SELECT 
						COALESCE(he.name->> '%s', he.name->>'en_US') as he_name,

						--he.name,
						he.last_name,
						he.passport_id,
						line.amount_net,
						he.id,
						he.account_number,
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='NETU'),
						(select coalesce(sum(amount),null) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='RNET')
						FROM salary_order so
						LEFT JOIN salary_order_line line ON line.order_id=so.id
						LEFT JOIN hr_employee he ON he.id=line.employee_id
						WHERE so.year='%s' and so.month='%s' and he.bank_id=%s and so.type='%s' and so.company_id=%s
						ORDER BY he.name"""%(lang,self.year,self.month,self.bank_id.id,self.type, self.company_id.id)
					self.env.cr.execute(query)
					records = self.env.cr.fetchall()
			rowx+=1
			n=1
			for record in records:
				if self.is_not_account==True:
					
					sheet.write(rowx, 0,n,contest_left)
					sheet.write(rowx, 1,record[1],contest_left)
					sheet.write(rowx, 2,record[0],contest_left)
					sheet.write(rowx, 3,record[2],contest_left)
					sheet.write(rowx, 4,record[5],contest_center)
					if self.type=='advance':
						if not record[6]:
							continue
						sheet.write(rowx, 5,record[6],contest_left1)
					else:
						if not record[7]:
							continue
						sheet.write(rowx, 5,record[7],contest_left1)
					# sheet.write(rowx, 5,'',contest_left1)
				else:
									
					sheet.write(rowx, 0,n,contest_left)
					sheet.write(rowx, 1,record[1],contest_left)
					sheet.write(rowx, 2,record[0],contest_left)
					sheet.write(rowx, 3,record[2],contest_left)
					sheet.write(rowx, 4,record[5],contest_center)
					if self.type=='advance':
						if not record[6]:
							continue
						sheet.write(rowx, 5,record[6],contest_left1)
					else:
						if not record[7]:
							continue
						sheet.write(rowx, 5,record[7],contest_left1)

				rowx+=1
				n+=1
			sheet.merge_range(rowx,0,rowx,4, u"Нийт", header)
			sheet.write_formula(rowx, 5, '{=SUM('+self._symbol(save_row-1, 5) +':'+ self._symbol(rowx-1, 5)+')}', fooder)

		
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



