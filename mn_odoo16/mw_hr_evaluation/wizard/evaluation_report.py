# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
from datetime import datetime, timedelta

from odoo import tools
from odoo import api, fields, models

class EvaluationReport(models.TransientModel):
	_name = "evaluation.report"
	_description = "Evaluation report"

	company_id= fields.Many2one('res.company', "Компани", default=lambda self: self.env.user.company_id, readonly=True, required=True)
	date = fields.Date('Огноо', required=True)
	year = fields.Char('Жил')
	month = fields.Char('Сар', ondelete=False)

	@api.onchange('date')
	def _onchange_date(self):
		if self.date:
			self.year = self.date.year
			self.month = self.date.month

	def export_report(self):
		ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		sheet = workbook.add_worksheet(u'Evaluation report')

		file_name = 'Үнэлгээний тайлан'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(8)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#98FB98')

		contest_left = workbook.add_format({'num_format': '#,##0.00'})
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)
		contest_left.set_num_format('#,##0.00')

		contest_left1 = workbook.add_format({'num_format': '#,##0.00'})
		contest_left1.set_text_wrap()
		contest_left1.set_font_size(9)
		contest_left1.set_font('Times new roman')
		contest_left1.set_align('right')
		contest_left1.set_border(style=1)
		contest_left1.set_num_format('#,##0.00')

		theader3 = workbook.add_format({'bold': 1})
		theader3.set_font_size(11)
		theader3.set_font('Times new roman')
		theader3.set_align('left')
		theader3.set_align('vcenter')

		contest_center_date = workbook.add_format()
		contest_center_date.set_text_wrap()
		contest_center_date.set_font_size(9)
		contest_center_date.set_font('Times new roman')
		contest_center_date.set_align('center')
		contest_center_date.set_align('vcenter')
		contest_center_date.set_border(style=1)
		contest_center_date.set_num_format('dd/mm/yy')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)
		contest_center.set_num_format('#,##0')

		contest_center_t = workbook.add_format()
		contest_center_t.set_text_wrap()
		contest_center_t.set_font_size(9)
		contest_center_t.set_font('Times new roman')
		contest_center_t.set_align('center')
		contest_center_t.set_align('vcenter')
		contest_center_t.set_border(style=1)


		# GET warehouse loc ids
		rowx=0
		save_row=7
		sheet.merge_range(0,2,0,3, u'"Улаанбаатар Гурил" ХХК-н ажилтнуудын %s.%s сарын KPI үнэлгээ'%(self.year,self.month), theader3),
		sheet.merge_range(2,2,2,5, u'Үнэлгээний тайлан', theader3),
		rowx=6

		sheet.write(rowx+1, 0, u'№', theader),
		sheet.write(rowx+1, 1, u'Жил', theader),
		sheet.write(rowx+1, 2, u'Сар', theader),
		sheet.write(rowx+1, 3, u'Овог', theader),
		sheet.write(rowx+1, 4, u'Нэр', theader),
		sheet.write(rowx+1, 5, u'Ажилтны код', theader),
		sheet.write(rowx+1, 6, u'Хэлтэс', theader),
		sheet.write(rowx+1, 7, u'Албан тушаал', theader),
		sheet.write(rowx+1, 8, u'Үзүүлэлт', theader),
		sheet.write(rowx+1, 9, u'Авах оноо', theader),
		sheet.write(rowx+1, 10, u'Авсан оноо', theader),
		sheet.write(rowx+1, 11, u'Тайлбар', theader),
		sheet.write(rowx+1, 12, u'Нийт авах оноо', theader),
		sheet.write(rowx+1, 13, u'Нийт авсан оноо', theader),
			
		rowx+=1
		
		sheet.set_column('A:A', 5)
		sheet.set_column('B:C', 7)
		sheet.set_column('D:D', 10)
		sheet.set_column('E:E', 15)
		sheet.set_column('G:H', 25)
		sheet.set_column('I:I', 30)
		sheet.set_column('L:L', 30)

		query="""SELECT 
			hr.name as hr_name,
			hr.last_name as last_name,
			hr.identification_id as ident_id,
			hd.name as hd_name,
			hj.name as hj_name,
			el.score as score,
			el.sum_amount as sum_amount,
			el.year as year,
			el.month as month,
			el.id as el_id
			FROM hr_evaluation he 
			LEFT JOIN hr_evaluation_line el ON el.parent_id=he.id 
			LEFT JOIN hr_employee hr ON hr.id=el.employee_id 
			LEFT JOIN hr_department hd ON hd.id=hr.department_id 
			LEFT JOIN hr_job hj ON hj.id=hr.job_id
			WHERE hr.company_id=%s and he.year='%s' and he.month='%s'"""%(self.company_id.id,self.year,self.month)
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		rowx+=1
		rx=6
		k=0
		n=1
		emp = ''
		for record in records:
			l=0
			line_pool = self.env['hr.evaluation.line.line'].search([('line_parent_id','=',record['el_id'])])
			
			if line_pool:
				for line in line_pool:
					if line.description:
						emp = line.description

					sheet.write(rowx, 8,line.conf_id.name,contest_left)
					sheet.write(rowx, 9,line.score,contest_center)
					sheet.write(rowx, 10,line.get_score,contest_center)
					sheet.write(rowx, 11,emp,contest_center)
					rowx+=1
					k+=1
					l+=1
			else:
				sheet.write(rowx, 8,'',contest_center)
				sheet.write(rowx, 9,'',contest_center)
				sheet.write(rowx, 10,'',contest_center)
				sheet.write(rowx, 11,'',contest_center)
				rowx+=1
			if k<=1:
				sheet.write(rx, 0,n,contest_left)
				sheet.write(rx, 1,record['year'],contest_left)
				sheet.write(rx, 2,record['month'],contest_left)
				sheet.write(rx, 3,record['last_name'],contest_left)
				sheet.write(rx, 4,record['hr_name'],contest_left)
				sheet.write(rx, 5,record['ident_id'],contest_left)
				sheet.write(rx, 6,record['hd_name'],contest_left)
				sheet.write(rx, 7,record['hj_name'],contest_left)
				sheet.write(rx, 12,record['score'],contest_center)
				sheet.write(rx, 13,record['sum_amount'],contest_left1)
				n+=1
			else:
				sheet.merge_range(rx, 0,rx+k-1, 0,n,contest_left)
				sheet.merge_range(rx, 1,rx+k-1, 1,record['year'],contest_left)
				sheet.merge_range(rx, 2,rx+k-1, 2,record['month'],contest_left)
				sheet.merge_range(rx, 3,rx+k-1, 3,record['last_name'],contest_left)
				sheet.merge_range(rx, 4,rx+k-1, 4,record['hr_name'],contest_left)
				sheet.merge_range(rx, 5,rx+k-1, 5,record['ident_id'],contest_left)
				sheet.merge_range(rx, 6,rx+k-1, 6,record['hd_name'],contest_left)
				sheet.merge_range(rx, 7,rx+k-1, 7,record['hj_name'],contest_left)
				sheet.merge_range(rx, 12,rx+k-1, 12,record['score'],contest_left)
				sheet.merge_range(rx, 13,rx+k-1, 13,record['sum_amount'],contest_left)
				n+=1
			if l>0:
				rx+=l
			else:
				rx+=1
			k=0

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
