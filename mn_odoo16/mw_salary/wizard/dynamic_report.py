# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
from datetime import datetime, timedelta

from odoo import tools
from odoo import api, fields, models

class DynamicReport(models.TransientModel):
	_name = "dynamic.report"
	_description = "dynamic report"

	@api.model
	def _get_categs(self):
	    return self.env['hr.allounce.deduction.category'].sudo().search([('is_advance', '!=', True)]).ids

	salary_id= fields.Many2one('salary.order', 'Цалин')
	category_ids = fields.Many2many('hr.allounce.deduction.category',string='Нэмэгдэл суутгалууд', default=_get_categs)
	color = fields.Char(u'Өнгө', required=True, default='#c4d79b')

	def export_report(self):
		ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		sheet = workbook.add_worksheet(u'Salary report')

		file_name = 'Salary report'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(10)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color(self.color)

		theader1 = workbook.add_format({'bold': 1})
		theader1.set_font_size(10)
		theader1.set_font('Times new roman')
		theader1.set_align('left')
		theader1.set_align('vcenter')

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

		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_font('Times new roman')
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_bg_color(self.color)

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

		# GET warehouse loc ids
		rowx=0
		save_row=7
		sheet.merge_range(rowx+0,0,rowx+0,3, u'Байгууллагын нэр:'+ ' ' + self.salary_id.company_id.name, theader3),
		sheet.merge_range(rowx+4,0,rowx+4,2, time.strftime('%Y-%m-%d'), theader1),
		# sheet.merge_range(rowx+4,3,rowx+4,5, self.salary_id.company_id.name, theaderu),
		if self.salary_id.type=='final':
			sheet.merge_range(rowx+2,0,rowx+2,5, self.salary_id.year +u'  ОНЫ  '+ self.salary_id.month+u' -Р САРЫН СҮҮЛ ЦАЛИН', theader2),
		elif self.salary_id.type=='advance':
			sheet.merge_range(rowx+2,0,rowx+2,5, self.salary_id.year +u'  ОНЫ  '+ self.salary_id.month+u' -Р САРЫН УРЬДЧИЛГАА ЦАЛИН', theader2),
		rowx=4
		colx=6
		for item in self.category_ids:
			sheet.write(rowx+1, colx, item.name, theader),
			colx+=1

		sheet.write(rowx+1, 0, u'№', theader),
		sheet.write(rowx+1, 1, u'Код', theader),
		sheet.write(rowx+1, 2, u'Овог', theader),
		sheet.write(rowx+1, 3, u'Нэр', theader),
		sheet.write(rowx+1, 4, u'Дансны дугаар', theader),
		sheet.write(rowx+1, 5, u'Үндсэн цалингийн дүн', theader),

		sheet.set_column('A:A', 5)
		sheet.set_column('B:B', 10)
		sheet.set_column('C:C', 15)
		sheet.set_column('D:D', 15)
		sheet.set_column('E:E', 15)
		sheet.set_column('F:AZ', 10)

		query="""SELECT 
			he.name as hr_name,
			he.last_name as last_name,
			he.identification_id as identification_id,
			line.basic as basic,
			he.id as hr_id
			FROM salary_order so
			LEFT JOIN salary_order_line line ON line.order_id=so.id
			LEFT JOIN hr_employee he ON he.id=line.employee_id
			WHERE so.id=%s"""%(self.salary_id.id)
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		rowx+=2
		n=1
		
		for record in records:
			sheet.write(rowx, 0,n,contest_left)
			sheet.write(rowx, 1,record['identification_id'],contest_left)
			sheet.write(rowx, 2,record['last_name'],contest_left)
			sheet.write(rowx, 3,record['hr_name'],contest_left)
			# sheet.write(rowx, 4,record['bank_account_number'],contest_center)
			sheet.write(rowx, 5,record['basic'],contest_left1)
			clx=6
			for cat in self.category_ids:
				query1="""SELECT
	                ll.amount as amount
	                FROM salary_order so
	                LEFT JOIN salary_order_line line ON line.order_id=so.id
	                LEFT JOIN salary_order_line_line ll ON ll.order_line_id1=line.id
	                LEFT JOIN hour_balance_line bal ON bal.order_balance_line_id=line.id
	                LEFT JOIN hr_employee he ON he.id=line.employee_id
	                LEFT JOIN hr_department rb ON rb.id=bal.department_id
	                LEFT JOIN hr_job hj ON hj.id=bal.job_id
	                WHERE so.id=%s and ll.category_id=%s and he.id=%s"""%(self.salary_id.id,cat.id,record['hr_id'])
				self.env.cr.execute(query1)
				recs = self.env.cr.fetchall()
				if recs:
					sheet.write(rowx, clx, recs[0][0], contest_left1),
					clx+=1

			rowx+=1
			n+=1

		sheet.merge_range(rowx,0,rowx,4, u"Нийт", header)
		l=5
		while l <= clx-1:
			sheet.write_formula(rowx, l, '{=SUM('+self._symbol(save_row-1, l) +':'+ self._symbol(rowx-1, l)+')}', header)
			l+=1


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





