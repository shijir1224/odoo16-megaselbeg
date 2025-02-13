
import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
from datetime import datetime, timedelta

from odoo import tools
from odoo import api, fields, models



class ppeEndDateTtctReport(models.Model):

	_name = 'ppe.end.date.report'
	_description = 'ppe End Date Report'
	
	start_date = fields.Date('Эхлэх огноо')
	end_date = fields.Date('Дуусах огноо')
	
	def export_report(self):
		ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		sheet = workbook.add_worksheet(u'Report')

		file_name = 'PPE олголт'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(8)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#0a5eaf')
		theader.set_font_color('white')

		theaderl = workbook.add_format({'bold': 1})
		theaderl.set_font_size(10)
		theaderl.set_text_wrap()
		theaderl.set_font('Times new roman')
		theaderl.set_align('center')
		theaderl.set_align('vcenter')
		theaderl.set_font_color('0a5eaf')

		theader1 = workbook.add_format({})
		theader1.set_font_size(10)
		theader1.set_text_wrap()
		theader1.set_font('Times new roman')
		theader1.set_align('center')
		theader1.set_align('vcenter')

		contest_left = workbook.add_format({'num_format': '###,###,###'})
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		contest_left1 = workbook.add_format()
		contest_left1.set_text_wrap()
		contest_left1.set_font_size(9)
		contest_left1.set_font('Times new roman')
		contest_left1.set_align('right')
		contest_left1.set_num_format('#,0.0')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)
		contest_center.set_num_format('#,0.0')

		# GET warehouse loc ids
		rowx=0
		save_row=0
		sheet.merge_range(rowx+1,0,rowx+1,12, u'PPE дуусах хугацааны тайлан', theaderl),

		rowx=2

		sheet.write(rowx+1, 0, u'#', theader),
		sheet.write(rowx+1, 1, u'Ажилтан/Staff name', theader),
		sheet.write(rowx+1, 2, u'Албан тушаал/Position', theader),
		sheet.write(rowx+1, 3, u'Хэлтэс/Department', theader),
		sheet.write(rowx+1, 4, u'Компани/Company', theader),
		sheet.write(rowx+1, 5, u'Ажилтны төлөв/Staff status', theader),
		sheet.write(rowx+1, 6, u'Нэг бүрийн хамгаалах хэрэгсэл/The name of PPE', theader),
		sheet.write(rowx+1, 7, u'Олгосон огноо/Provided date', theader),
		sheet.write(rowx+1, 8, u'Тоо хэмжээ/Provided quantity', theader),
		sheet.write(rowx+1, 9, u'Норм/Norm', theader),
		sheet.write(rowx+1, 10, u'Нормын хугацаа дуусах огноо/End date', theader),
		sheet.write(rowx+1, 11, u'Тайлбар/Comment', theader),
		sheet.write(rowx+1, 12, u'Холбоотой шаардах/Requisition', theader),

		rowx+=1
		
		sheet.set_column('A:A', 5)
		sheet.set_column('B:F', 15)
		sheet.set_column('G:G', 40)
		sheet.set_column('C:C', 40)
		sheet.set_column('E:E', 30)
		sheet.set_column('H:M', 15)
		query="""SELECT 
			ppe.employee_id as employee_id,
			ppel.id as ppel_id
			FROM ppe_registration ppe
			LEFT JOIN ppe_registration_line ppel ON ppe.id=ppel.parent_id
			WHERE  ppel.end_date >= '%s' and  ppel.end_date <= '%s'
			ORDER BY  ppe.employee_id
			"""%(self.start_date,self.end_date)
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		rowx+=1
		n=1
		for record in records:	
			ppel_id = self.env['ppe.registration.line'].search([('id','=',record['ppel_id'])])
			hr_id = self.env['hr.employee'].search([('id','=',record['employee_id'])])
			sheet.write(rowx, 0,n,contest_left)
			sheet.write(rowx, 1,hr_id.name,contest_left)
			sheet.write(rowx, 2,hr_id.job_id.name,contest_left)
			sheet.write(rowx, 3,hr_id.department_id.name,contest_left)
			sheet.write(rowx, 4,hr_id.company_id.name,contest_left)
			sheet.write(rowx, 5,hr_id.employee_type,contest_left)
			sheet.write(rowx, 6,ppel_id.product_id.name,contest_center)
			sheet.write(rowx, 7,str(ppel_id.date),contest_center)
			sheet.write(rowx, 8,ppel_id.qty,contest_center)
			sheet.write(rowx, 9,ppel_id.norm,contest_center)
			sheet.write(rowx, 10,str(ppel_id.end_date),contest_center)
			sheet.write(rowx, 11,ppel_id.description,contest_center)
			sheet.write(rowx, 12,ppel_id.product_expense_id.name,contest_center)
			# sheet.write(rowx, 3,ppel_id.qty,contest_center)
			rowx+=1
			n+=1

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