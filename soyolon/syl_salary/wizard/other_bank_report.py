# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
from datetime import datetime, timedelta
from odoo.tools import get_lang

from odoo import tools
from odoo import api, fields, models

class OtherBankReport(models.TransientModel):
	_name = "other.bank.report"
	_description = "other bank report "

	company_id = fields.Many2one('res.company', string='Компани', change_default=True,
		required=True, readonly=True, default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
	# long_salary_id= fields.Many2one('long.year.salary', 'Удааэ жил')
	date = fields.Date('Тайлан татах огноо')
	bank_id = fields.Many2one('res.bank', u'Банк')


	# is_long_year= fields.Boolean('Удаан жилийн нэмэгдэл эсэх')

	
	def export_report(self):
		ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		sheet = workbook.add_worksheet(u'Salary bank report')

		file_name = 'Банкинд илгээх тайлан'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

	

		theaderkhas = workbook.add_format({'bold': 1})
		theaderkhas.set_font_size(10)
		theaderkhas.set_text_wrap()
		theaderkhas.set_font('Times new roman')
		theaderkhas.set_align('center')
		theaderkhas.set_align('vcenter')
		theaderkhas.set_border(style=1)


		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(10)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#6495ED')


		

		theader1khas = workbook.add_format({'bold': 1})
		theader1khas.set_font_size(10)
		theader1khas.set_font('Times new roman')
		theader1khas.set_align('left')
		theader1khas.set_align('vcenter')

	
		

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

		contest_left1 = workbook.add_format({'num_format': '###,###,###'})
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
			
		rowx=0
		save_row=3
		sheet.merge_range(rowx+0,0,rowx+0,3, u'Байгууллагын нэр:'+ ' ' + self.company_id.name, theader1khas),
		sheet.merge_range(rowx+1,4,rowx+1,5, self.bank_id.name, theader1khas),
	


		rowx=4

		sheet.write(rowx, 0, u'№', theader),
		sheet.write(rowx, 1, u'Овог', theader),
		sheet.write(rowx, 2, u'Нэр', theader),
		sheet.write(rowx, 3, u'Регистр', theader),
		sheet.write(rowx, 4, u'Дансны дугаар', theader),
		sheet.write(rowx, 5, u'Цалингийн дүн', theader),

		
		sheet.set_column('A:A', 5)
		sheet.set_column('B:B', 25)
		sheet.set_column('C:C', 15)
		sheet.set_column('D:D', 15)
		sheet.set_column('E:E', 15)
		sheet.set_column('F:F', 15)
		rowx+=1
		lang = self.env.user.lang or get_lang(self.env).code
		query="""SELECT 
					COALESCE(he.name->> '%s', he.name->>'en_US'),
					he.last_name,
					he.passport_id,
					he.id,
					he.account_number,
					line.amount_net_round
					FROM long_year_salary so
					LEFT JOIN long_year_salary_line line ON line.parent_id=so.id
					LEFT JOIN hr_employee he ON he.id=line.employee_id
					WHERE so.date='%s'  and he.bank_id=%s  and line.amount_net_round>0
					ORDER BY he.name"""%(lang, self.date, self.bank_id.id)
		self.env.cr.execute(query)
		records = self.env.cr.fetchall()
		
		n=1
		for record in records:
			sheet.write(rowx, 0,n,contest_left)
			sheet.write(rowx, 1,record[1],contest_left)
			sheet.write(rowx, 2,record[0],contest_left)
			sheet.write(rowx, 3,record[2],contest_left)
			sheet.write(rowx, 4,record[4],contest_center)
			sheet.write(rowx, 5,record[5],contest_center)
			rowx+=1
			n+=1
		sheet.merge_range(rowx,0,rowx,4, u"Нийт", fooderkhas)
		sheet.write_formula(rowx, 5, '{=SUM('+self._symbol(save_row-1, 5) +':'+ self._symbol(rowx-1, 5)+')}', fooderkhas)

		
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
