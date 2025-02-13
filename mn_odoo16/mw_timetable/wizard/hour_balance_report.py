# -*- coding: utf-8 -*-
import time
import xlsxwriter
from io import BytesIO
import base64
try:
	# Python 2 support
	from base64 import encodestring
except ImportError:
	# Python 3.9.0+ support
	from base64 import encodebytes as encodestring
from datetime import datetime, timedelta
from odoo import tools
from odoo import api, fields, models


DATE_FORMAT = "%Y-%m-%d"


class HourBalanceReport(models.TransientModel):
	_name = "hour.balance.report"
	_description = "Hour Balance Report"

	start_date = fields.Date(u'Эхлэх огноо')
	end_date = fields.Date(u'Дуусах огноо')
	department_id = fields.Many2one('hr.department', 'Хэлтэс')
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')

	def set_conditions(self):
		conditions = ""
		if  self.department_id and self.work_location_id:
			conditions = "and wl.id= %s" % self.work_location_id.id
			conditions +=  " and hd.id = %s " % self.department_id.id
		elif self.department_id:
			conditions = " and hd.id = %s " % self.department_id.id
		elif self.work_location_id:
			conditions = " and wl.id = %s " % self.work_location_id.id
		return conditions

	def export_report(self):
		ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		sheet = workbook.add_worksheet(u'Roster report')

		file_name = 'Цагийн баланс нэгдсэн тайлан'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(9)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#d9e1f2')

		theaderh = workbook.add_format({'bold': 1})
		theaderh.set_font_size(9)
		theaderh.set_text_wrap()
		theaderh.set_font('Times new roman')
		theaderh.set_align('center')
		theaderh.set_align('vcenter')
		theaderh.set_border(style=1)
		theaderh.set_bg_color('#FFD27F')

		footer = workbook.add_format({'bold': 1})
		footer.set_text_wrap()
		footer.set_font_size(9)
		footer.set_font('Times new roman')
		footer.set_align('right')
		footer.set_align('vcenter')
		footer.set_border(style=1)
		footer.set_bg_color('#EFEFFF')
		footer.set_num_format('#,##0.00')

		contest_leftoff = workbook.add_format()
		contest_leftoff.set_text_wrap()
		contest_leftoff.set_font_size(9)
		contest_leftoff.set_font('Times new roman')
		contest_leftoff.set_align('left')
		contest_leftoff.set_align('vcenter')
		contest_leftoff.set_border(style=1)

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)
		contest_center.set_num_format('#,##0.00')

		sheet.set_column('A:A', 5)
		sheet.set_column('B:B', 6)
		sheet.set_column('C:AG', 15)
		# GET warehouse loc ids

		rowx = 4

		sheet.write(rowx, 0, u'№', theader),
		sheet.write(rowx, 1, u'Ажилтны код', theader),
		sheet.write(rowx, 2, u'Овог', theader),
		sheet.write(rowx, 3, u'Нэр', theader),
		sheet.write(rowx, 4, u'Ажилтны төлөв', theader),
		sheet.write(rowx, 5, u'Хэлтэс алба', theader),
		sheet.write(rowx, 6, u'Албан тушаал', theader),
		sheet.write(rowx, 7, u'АЗ өдөр', theader),
		sheet.write(rowx, 8, u'АЗ цаг', theader),

		#1.2 query дээрх нөхцөл шалгах
		# Цагийн төлөвлөгөө зурах хэсэхг
		rowx += 1
		n=1
		
		query1 = """SELECT
			sum(hbl.day_to_work_month) as day_to_work_month,
			sum(hbl.hour_to_work_month) as hour_to_work_month,
			hr.id as hr_id
			FROM hour_balance_dynamic_line hbl
			LEFT JOIN hour_balance_dynamic hb ON hb.id=hbl.parent_id
			LEFT JOIN hr_employee hr ON hr.id = hbl.employee_id
			LEFT JOIN hr_department hd ON hd.id = hb.department_id
			LEFT JOIN hr_work_location wl ON wl.id = hb.work_location_id
			WHERE hb.date_from>='%s' and hb.date_to<='%s' and hb.state ='done' and hb.type='final' %s 
			GROUP BY hr.id""" %(self.start_date,self.end_date,self.set_conditions())
		self.env.cr.execute(query1)
		records1 = self.env.cr.dictfetchall()
		
		confs = self.env['hour.balance.dynamic.configuration'].search([('is_salary','!=',True)])
		col=9
		rowx= 4
		for c in confs:
			sheet.write(rowx,col, c.name, theader),
			col+=1
		n=1
		rowx+=1
		print('\n\n-records1--',records1)
		for rec in records1:
			line_emp = self.env['hr.employee'].search([('id','=',rec['hr_id'])],limit=1)
			sheet.write(rowx, 0, n, contest_leftoff)
			sheet.write(rowx, 1, line_emp.identification_id, contest_leftoff)
			sheet.write(rowx, 2, line_emp.last_name, contest_leftoff)
			sheet.write(rowx, 3, line_emp.name, contest_leftoff)
			sheet.write(rowx, 4, dict(line_emp._fields['employee_type'].selection).get(line_emp.employee_type), contest_leftoff)
			sheet.write(rowx, 5, line_emp.department_id.name, contest_leftoff)
			sheet.write(rowx, 6, line_emp.job_id.name, contest_leftoff)
			sheet.write(rowx, 7, rec['day_to_work_month'], contest_leftoff)
			sheet.write(rowx, 8, rec['hour_to_work_month'], contest_leftoff)
			
			query = """SELECT
				sum(hbll.hour) as hour,
				hbll.is_salary as is_salary,
				hc.id as hc_id
				FROM hour_balance_dynamic_line_line hbll
				LEFT JOIN hour_balance_dynamic_configuration hc ON hc.id=hbll.conf_id
				WHERE hbll.employee_id = %s and hbll.date_from >='%s' and hbll.date_to<='%s' and hbll.is_salary != True
				GROUP BY hc.id,hbll.is_salary,hbll.number
				ORDER BY hbll.number  """ %(rec['hr_id'],self.start_date,self.end_date)
			self.env.cr.execute(query)
			records = self.env.cr.dictfetchall()
			print('\n\n-records--',records,rec['hr_id'])
			colx=9
			for ll in records:
				# print('\n\n===',ll['hour'],ll['hc_id'])
				sheet.write(rowx,colx,ll['hour'], contest_leftoff),
				colx+=1
			rowx+=1
			n+=1
		
		
		workbook.close()
		out = encodestring(output.getvalue())
		excel_id = self.env['report.excel.output'].create(
			{'data': out, 'name': file_name+'.xlsx'})
		return {
			'name': 'Export Result',
			'view_mode': 'form',
			'res_model': 'report.excel.output',
			'view_id': False,
			'type': 'ir.actions.act_url',
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
