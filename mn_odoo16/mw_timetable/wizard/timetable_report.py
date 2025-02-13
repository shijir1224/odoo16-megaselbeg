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


class TimetableBalanceReport(models.TransientModel):
	_name = "timetable.balance.report"
	_description = "Timetable Balance Report"

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

		file_name = 'Цагийн нэгдсэн тайлан'

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
	

		theader11 = workbook.add_format({'bold': 1})
		theader11.set_font_size(9)
		theader11.set_text_wrap()
		theader11.set_font('Times new roman')
		theader11.set_align('center')
		theader11.set_align('vcenter')
		theader11.set_border(style=1)
		theader11.set_bg_color('#FFD27F')
		theader11.set_num_format('#,##0.00')

		footer = workbook.add_format({'bold': 1})
		footer.set_text_wrap()
		footer.set_font_size(9)
		footer.set_font('Times new roman')
		footer.set_align('right')
		footer.set_align('vcenter')
		footer.set_border(style=1)
		footer.set_bg_color('#EFEFFF')
		footer.set_num_format('#,##0.00')

		contest_right = workbook.add_format()
		contest_right.set_text_wrap()
		contest_right.set_font_size(9)
		contest_right.set_font('Times new roman')
		contest_right.set_align('right')
		contest_right.set_align('vcenter')
		contest_right.set_border(style=1)

		contest_leftoff = workbook.add_format()
		contest_leftoff.set_text_wrap()
		contest_leftoff.set_font_size(9)
		contest_leftoff.set_font('Times new roman')
		contest_leftoff.set_align('left')
		contest_leftoff.set_align('vcenter')
		contest_leftoff.set_border(style=1)
		contest_leftoff.set_bg_color('#ffc024')


		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)
		contest_left.set_bg_color('#8db4e2')
		contest_left.set_num_format('#,##0.00')


		contest_left1 = workbook.add_format()
		contest_left1.set_text_wrap()
		contest_left1.set_font_size(9)
		contest_left1.set_font('Times new roman')
		contest_left1.set_align('left')
		contest_left1.set_align('vcenter')
		contest_left1.set_border(style=1)
		contest_left1.set_bg_color('#0370c0')
		contest_left1.set_num_format('#,##0.00')

		contest_leftug = workbook.add_format()
		contest_leftug.set_text_wrap()
		contest_leftug.set_font_size(9)
		contest_leftug.set_font('Times new roman')
		contest_leftug.set_align('left')
		contest_leftug.set_align('vcenter')
		contest_leftug.set_border(style=1)
		contest_leftug.set_num_format('#,##0.00')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)
		contest_center.set_num_format('#,##0.00')

		theader190 = workbook.add_format({'bold': 1})
		theader190.set_font_size(8)
		theader190.set_font('Times new roman')
		theader190.set_align('center')
		theader190.set_align('vcenter')
		theader190.set_border(style=1)
		theader190.set_bg_color('#fff4d7')
		theader190.set_rotation(90)

		theader90 = workbook.add_format({'bold': 1})
		theader90.set_font_size(8)
		theader90.set_text_wrap()
		theader90.set_font('Times new roman')
		theader90.set_align('center')
		theader90.set_align('vcenter')
		theader90.set_border(style=1)
		theader90.set_bg_color('#c7dff1')
		theader90.set_rotation(90)

		theaderu90 = workbook.add_format({'bold': 1})
		theaderu90.set_font_size(8)
		theaderu90.set_font('Times new roman')
		theaderu90.set_align('center')
		theaderu90.set_align('vcenter')
		theaderu90.set_border(style=1)
		theaderu90.set_bg_color('#e2e8f3')
		theaderu90.set_rotation(90)

		theadery90 = workbook.add_format({'bold': 1})
		theadery90.set_font_size(8)
		theadery90.set_font('Times new roman')
		theadery90.set_align('center')
		theadery90.set_align('vcenter')
		theadery90.set_border(style=1)
		theadery90.set_bg_color('#fefd32')
		theadery90.set_rotation(90)

		theaderno90 = workbook.add_format({'bold': 1})
		theaderno90.set_font_size(8)
		theaderno90.set_font('Times new roman')
		theaderno90.set_align('center')
		theaderno90.set_align('vcenter')
		theaderno90.set_border(style=1)
		theaderno90.set_bg_color('#e8f2e2')
		theaderno90.set_rotation(90)

		theader1p = workbook.add_format({'bold': 1})
		theader1p.set_font_size(10)
		theader1p.set_font('Times new roman')
		theader1p.set_align('left')
		theader1p.set_align('vcenter')
		theader1p.set_border(style=1)
		theader1p.set_bg_color('#fff4d7')

		theader1hh = workbook.add_format({'bold': 1})
		theader1hh.set_font_size(10)
		theader1hh.set_font('Times new roman')
		theader1hh.set_align('left')
		theader1hh.set_align('vcenter')
		theader1hh.set_border(style=1)

		sheet.set_column('A:A', 5)
		sheet.set_column('B:B', 10)
		sheet.set_column('C:C', 10)
		sheet.set_column('D:D', 10)
		sheet.set_column('E:E', 10)
		sheet.set_column('F:G', 20)
		sheet.set_column('G:G', 7)
		sheet.set_column('AK:DA', 7)
		sheet.set_column('AN:BQ', 15)
		sheet.set_column('H:CC', 5)
		rowx = 4

		sheet.write(rowx, 0, u'№', theader),
		sheet.write(rowx, 1, u'Ажилтны код', theader),
		sheet.write(rowx, 2, u'Овог', theader),
		sheet.write(rowx, 3, u'Нэр', theader),
		sheet.write(rowx, 4, u'Регистр', theader),
		sheet.write(rowx, 5, u'Хэлтэс алба', theader),
		# sheet.write(rowx, 6, u'Албан тушаал', theader),

		#1.2 query дээрх нөхцөл шалгах
		# Цагийн төлөвлөгөө зурах хэсэхг
		rowx += 1
		n=1
		query = """SELECT 
			line.employee_id as emp,
			hd.name as hd_name,
			hj.name as hj_name,
			hr.name as name,
			hr.last_name as last_name,
			hr.identification_id as ident_id,
			hr.passport_id as passport_id,
			hr.employee_type as employee_type
			FROM hr_timetable_line line
			left join hr_timetable_line_line tl ON  line.id=tl.parent_id
			left join hr_timetable ht ON ht.id=line.parent_id
			left join hr_employee hr ON hr.id=line.employee_id
			left join hr_job hj ON hj.id=line.job_id
			left join hr_department hd ON hd.id=line.department_id
			left join hr_work_location wl ON wl.id=ht.work_location_id
			WHERE tl.date>='%s' and tl.date<='%s' %s
			GROUP BY hd.name,hr.name,line.employee_id,hj.name,hr.last_name,hr.identification_id,hr.employee_type,hr.passport_id
			ORDER BY hr.name
		""" % (self.start_date, self.end_date,self.set_conditions())
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		for record in records:
			sheet.write(rowx, 0, n, contest_leftoff)
			sheet.write(rowx, 1, record['ident_id'], contest_leftoff)
			sheet.write(rowx, 2, record['last_name'], contest_leftoff)
			sheet.write(rowx, 3, record['name'], contest_leftoff)
			sheet.write(rowx,4, record['passport_id'], contest_leftoff)
			sheet.write(rowx, 5, record['hd_name'], contest_leftoff)
			# sheet.write(rowx, 6, record['hj_name'], contest_leftoff)

			query1 = """SELECT 
				line.date as date,
				line.is_work_schedule as is_work_schedule,
				line.worked_hour as worked_hour,
				line.overtime_hour as overtime_hour,
				line.sickness_hour as sickness_hour,
				line.night_hour as night_hour,
				parent.employee_id as employee_id,
				hs.flag as flag,
				line.id as id
				FROM hr_timetable_line_line line
				LEFT JOIN hr_timetable_line parent on parent.id=line.parent_id
				LEFT JOIN hr_shift_time hs on hs.id=line.shift_attribute_id
				where line.date>='%s' and line.date<='%s' and parent.employee_id=%s
				ORDER BY line.date""" % (self.start_date, self.end_date, record['emp'])
			self.env.cr.execute(query1)
			records1 = self.env.cr.dictfetchall()
			col = 6
			for rec in records1:
				overtime_hour=0
				if rec['is_work_schedule'] == 'day':
					if rec['overtime_hour']:
						overtime_hour = rec['overtime_hour']
					sheet.write(rowx, col,rec['worked_hour'] + overtime_hour, contest_left)
				elif rec['is_work_schedule'] == 'night':
					if rec['overtime_hour']:
						overtime_hour = rec['overtime_hour']
					sheet.write(rowx, col, rec['night_hour'] + overtime_hour, contest_left1)
				else:
					sheet.write(rowx, col,rec['flag'], contest_leftug)
				col += 1
				
				ccc=col
				records2 = self.env['hour.balance.dynamic.line.line'].search([('employee_id','=',rec['employee_id'])])
				for rec2 in records2:
					if rec2.parent_id.date_from == self.start_date and rec2.parent_id.date_to == self.end_date:
						sheet.write(rowx,ccc,rec2['hour'],theader),
						ccc+=1
			rowx += 1
			n += 1
		query = """SELECT
			date 
			FROM hr_timetable_line_line
			where date>='%s' and date<='%s'
			GROUP BY date
			ORDER BY date""" % (self.start_date, self.end_date)
		self.env.cr.execute(query)
		records3 = self.env.cr.fetchall()
		planet = None
		rowx += 1
		n = 1
		col = 6
		coll=0
		for record3 in records3:
			start_date = datetime.strptime(str(record3[0]), DATE_FORMAT)
			if start_date.weekday() == 0:
				planet = 'Mon'
			elif start_date.weekday() == 1:
				planet = 'Tue'
			elif start_date.weekday() == 2:
				planet = 'Wed'
			elif start_date.weekday() == 3:
				planet = 'Thu'
			elif start_date.weekday() == 4:
				planet = 'Fri'
			elif start_date.weekday() == 5:
				planet = 'Sat'
			elif start_date.weekday() == 6:
				planet = 'Sun'
			sheet.merge_range(2, col, 3, col, planet, theader),
			sheet.write(4, col, start_date.day,theader),
			col += 1
			coll = col
			
		line_line = self.env['hour.balance.dynamic.configuration'].search([])
		for ll in line_line:
			sheet.merge_range(2,coll,4,coll, ll.name, theader),
			coll+=1
		
			
	
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
