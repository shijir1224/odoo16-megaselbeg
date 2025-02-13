import xlrd
import odoo
from xlsxwriter.utility import xl_rowcol_to_cell
import xlsxwriter
from io import BytesIO
from odoo import api, fields, models
import base64
try:
	# Python 2 support
	from base64 import encodestring
except ImportError:
	# Python 3.9.0+ support
	from base64 import encodebytes as encodestring
from odoo import  models, _
from odoo.osv import osv
import xlrd
from tempfile import NamedTemporaryFile
import odoo.netsvc, os
from odoo.exceptions import UserError
import time


class HrTimetableDailyReport(models.Model):
	_name = "hr.timetable.daily.report"
	_description="Hr Timetable Daily Report"


	date_from = fields.Date("Огноо", default=time.strftime("%Y-%m-01"))
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)



	def print_report(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'Өдөр тутмын ажиллаж буй ажилтнуудын тоо'

		# CELL styles тодорхойлж байна
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		left_h1 = workbook.add_format({'bold': 1})
		left_h1.set_font_size(10)
		left_h1.set_font('Times new roman')
		left_h1.set_align('left')

		h2 = workbook.add_format()
		h2.set_font_size(11)
		h2.set_font('Times new roman')
		h2.set_align('left')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(10)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#dfa12b')

		content_right = workbook.add_format()
		content_right.set_text_wrap()
		content_right.set_font('Times new roman')
		content_right.set_font_size(9)
		content_right.set_border(style=1)
		content_right.set_align('right')

		content_left = workbook.add_format({})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(9)
		content_left.set_border(style=1)
		content_left.set_align('left')
		
		
		center = workbook.add_format({})
		center.set_text_wrap()
		center.set_font('Times new roman')
		center.set_font_size(9)	 
		center.set_align('center')
		center.set_border(style=1)

		fooder = workbook.add_format({'num_format': '#,##0.0','bold': 1})
		fooder.set_font_size(10)
		fooder.set_text_wrap()
		fooder.set_font('Times new roman')
		fooder.set_align('center')
		fooder.set_align('vcenter')
		fooder.set_border(style=1)
		fooder.set_bg_color('#dfa12b')
		sheet = workbook.add_worksheet(u'Төлөвлөгөө')


		sheet.merge_range(3, 0, 3, 8, u'%s ӨДРИЙН АЖИЛТНУУДЫН ТООН МЭДЭЭ'%(self.date_from), h1)

		rowx=6
		sheet.merge_range(rowx, 0,rowx+2,0, u'Д/д', theader),
		sheet.merge_range(rowx,1,rowx+2,1, u'Хэсэг', theader),
		sheet.merge_range(rowx,2,rowx+2,2, u'Бүртгэлтэй байгаа ажилтны тоо', theader),
		sheet.merge_range(rowx,3,rowx+2,3, u'Ажиллаж байгаа ажилтны тоо', theader),
		sheet.merge_range(rowx,4,rowx+2,4, u'Амарч байгаа ажилтны тоо', theader),
		sheet.merge_range(rowx,5,rowx+2,5, u'Чөлөөтэй болон өвчтэй байгаа ажилтны тоо', theader),
		sheet.merge_range(rowx,6,rowx+2,6, u'Жирэмсний амралттай  ажилтны тоо', theader),
		
		sheet.merge_range(rowx, 8,rowx+2,8, u'Д/д', theader),
		sheet.merge_range(rowx,9,rowx+2,9, u'Хэсэг', theader),
		sheet.merge_range(rowx,10,rowx+2,10, u'Ажиллаж байгаа ажилтны тоо', theader),
		sheet.merge_range(rowx,11,rowx+2,11, u'Өдөр', theader),
		sheet.merge_range(rowx,12,rowx+2,12, u'Шөнө', theader),
		sheet.merge_range(rowx,13,rowx+2,13, u'Эрэгтэй', theader),
		sheet.merge_range(rowx,14,rowx+2,14, u'Эмэгтэй', theader),
		
		sheet.set_column('A:A', 4)
		sheet.set_column('B:B', 10)
		sheet.set_column('C:D', 12)
		sheet.set_column('I:I', 4)
		sheet.set_column('J:J', 10)
		
		rowx+=3
		query = """SELECT 
			count(l.id) as emp_count,
			hd.id as hd_id,
			hd.name as hd_name
			FROM hr_timetable_line_line ll
			LEFT JOIN hr_timetable_line l on l.id = ll.parent_id
			LEFT JOIN hr_department hd on hd.id = l.department_id
			WHERE ll.date='%s'
			GROUP BY hd.name,hd.id 
		""" % (self.date_from)
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		n = 1
		for record in records:
			line_working = self.env['hr.timetable.line.line'].search([]).filtered(lambda p: p.is_work_schedule in ('day','night') and p.department_id.id == record['hd_id'] and p.date == self.date_from)
			line_none = self.env['hr.timetable.line.line'].search([]).filtered(lambda p: p.is_work_schedule =='none' and p.department_id.id == record['hd_id'] and p.date == self.date_from)
			line_leave = self.env['hr.timetable.line.line'].search([]).filtered(lambda p: p.is_work_schedule in ('sick','leave','pay_leave') and p.department_id.id == record['hd_id'] and p.date == self.date_from)
			line_leave = self.env['hr.timetable.line.line'].search([]).filtered(lambda p: p.is_work_schedule in ('sick','leave','pay_leave') and p.department_id.id == record['hd_id'] and p.date == self.date_from)
			emp_pool = self.env['hr.employee'].search([('department_id','=', record['hd_id'])])
			emp_maternity = self.env['hr.employee'].search([('employee_type','in', ('maternity','pregnant_leave'))])

			line_day = self.env['hr.timetable.line.line'].search([]).filtered(lambda p: p.is_work_schedule == 'day' and p.department_id.id == record['hd_id'] and p.date == self.date_from)
			line_night = self.env['hr.timetable.line.line'].search([]).filtered(lambda p: p.is_work_schedule == 'night' and p.department_id.id == record['hd_id'] and p.date == self.date_from)
			line_male = self.env['hr.timetable.line.line'].search([]).filtered(lambda p: p.is_work_schedule in ('day','night') and p.department_id.id == record['hd_id'] and p.date == self.date_from and  p.employee_id.gender=='male')
			line_female = self.env['hr.timetable.line.line'].search([]).filtered(lambda p: p.is_work_schedule in ('day','night') and p.department_id.id == record['hd_id'] and p.date == self.date_from and  p.employee_id.gender=='female')

			sheet.write(rowx, 0, n, center)
			sheet.write(rowx, 1, record['hd_name'], center)
			sheet.write(rowx, 2,len(emp_pool), center)
			sheet.write(rowx, 3,len(line_working), center)
			sheet.write(rowx, 4,len(line_none), center)
			sheet.write(rowx, 5,len(line_leave), center)
			sheet.write(rowx, 6,len(emp_maternity), center)

			sheet.write(rowx, 8, n, center)
			sheet.write(rowx, 9, record['hd_name'], center)
			sheet.write(rowx, 10,len(line_working), center)
			sheet.write(rowx, 11,len(line_day), center)
			sheet.write(rowx, 12,len(line_night), center)
			sheet.write(rowx, 13,len(line_male), center)
			sheet.write(rowx, 14,len(line_female), center)
			rowx += 1
			n+=1
		sheet.merge_range(rowx, 0, rowx, 1, u'НИЙТ', fooder)
		sheet.merge_range(rowx, 8, rowx, 9, u'НИЙТ', fooder)
	
		workbook.close()
		out = encodestring(output.getvalue())
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