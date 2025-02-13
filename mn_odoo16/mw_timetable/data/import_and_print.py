from odoo import api, fields, models, _
from odoo.osv import osv
from xlsxwriter.utility import xl_rowcol_to_cell
from tempfile import NamedTemporaryFile
import xlsxwriter
from io import BytesIO
import base64
import xlrd
import  os
from datetime import  datetime, timedelta
from odoo.exceptions import UserError

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class HrTimetable(models.Model):
	_inherit = "hr.timetable"


#7 Цагийн төлөвлөгөө импорт хийх товч /Цагийг ростер тохируулахгүйгээр ээлжүүд үүсгэн импорт хийж болно/
	def action_import_timetable(self):
		timetable_data_pool =  self.env['hr.timetable.line']
		timetable_ll_pool =  self.env['hr.timetable.line.line']
		if self.line_ids:
			self.line_ids.unlink()
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise osv.except_osv(u'Aldaa')
		book = xlrd.open_workbook(fileobj.name)
		try :
			sheet = book.sheet_by_index(0)
		except:
			raise osv.except_osv(u'Aldaa')
		nrows = sheet.nrows
		ncols = sheet.ncols
		data = []
		for item in range(7,nrows):
			row = sheet.row(item)
			
			default_code = row[1].value
			employee_ids = self.env['hr.employee'].search([('identification_id','=',default_code)])
			from_dt = datetime.strptime(str(self.date_from), DATE_FORMAT).date()
			step = timedelta(days=1)
			if employee_ids:
				timetable_data_id = timetable_data_pool.create({'employee_id':employee_ids.id,
					'year':self.year,
					'month':self.month,
					'parent_id': self.id,
					'department_id':employee_ids.department_id.id,
					'job_id':employee_ids.job_id.id,
					})
				line_obj = timetable_data_pool.browse(timetable_data_id)
				col=4
				for lo in line_obj:
					for cl in range(4,ncols):
						data = row[col].value
						hr_shift_time_id = self.env['hr.shift.time'].search([('flag','=',data)],limit=1)
						timetable_ll_id = timetable_ll_pool.create({'employee_id':employee_ids.id,
							'year':self.year,
							'month':self.month,
							'parent_id': lo.id.id,
							'department_id':employee_ids.department_id.id,
							'job_id':employee_ids.job_id.id,
							'date':from_dt,
							'shift_plan_id':hr_shift_time_id.id,
							'shift_attribute_id':hr_shift_time_id.id,
							'hour_to_work':hr_shift_time_id.compute_sum_time
							})
						from_dt += step
						data = []
						col +=1
			else: 
				raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))

#7 Цагийн төлөвлөгөө эксел татах товч
	def print_timetable(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'Timetable'

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
		theader.set_bg_color('#c4d79b')

		content_right = workbook.add_format()
		content_right.set_text_wrap()
		content_right.set_font('Times new roman')
		content_right.set_font_size(9)
		content_right.set_border(style=1)
		content_right.set_align('right')

		content_left = workbook.add_format({'num_format': '###,###,###.##'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(9)
		content_left.set_border(style=1)
		content_left.set_align('left')
		
		center = workbook.add_format({'num_format': '###,###,###.##'})
		center.set_text_wrap()
		center.set_font('Times new roman')
		center.set_font_size(9)	 
		center.set_align('right')
		center.set_border(style=1)
		
		center_bold = workbook.add_format({'num_format': '###,###,###.##','bold': 1})
		center_bold.set_text_wrap()
		center_bold.set_font('Times new roman')
		center_bold.set_font_size(9)
		center_bold.set_align('right')
		center_bold.set_border(style=1)
		
		sheet = workbook.add_worksheet(u'Төлөвлөгөө')


		month_code=0
		
		if self.month=='90':
			month_code=10
		if self.month=='91':
			month_code=11
		if self.month=='92':
			month_code=12 
		else:
			month_code=self.month

		sheet.merge_range(0,0,0,3, u'Байгууллагын нэр:'+ ' ' + self.company_id.name, content_right),
		sheet.merge_range(2, 0, 2, 8, u'%s ОНЫ %s-р САРЫН ЦАГ БҮРТГЭЛ'%(self.year,month_code), h1)

		rowx=4
		save_row=4
		sheet.merge_range(rowx, 0,rowx+2,0, u'Д/д', theader),
		sheet.merge_range(rowx,1,rowx+2,1, u'Код', theader),
		sheet.merge_range(rowx,2,rowx+2,2, u'Овог', theader),
		sheet.merge_range(rowx,3,rowx+2,3, u'Нэр', theader),

		sheet.set_column('A:A', 4)
		sheet.set_column('B:B', 7)
		sheet.set_column('C:C', 15)
		sheet.set_column('D:D', 15)
		sheet.set_column('E:BB', 4)

		from_dt = datetime.strptime(str(self.date_from), DATE_FORMAT).date()
		to_dt = datetime.strptime(str(self.date_to), DATE_FORMAT).date()
		step = timedelta(days=1)
		col=4
		while from_dt <= to_dt:
			sheet.merge_range(rowx,col,rowx+2,col, str(from_dt), theader),
			from_dt += step
			col+=1

		n=1
		rowx+=3

		for data in self.line_ids:
			sheet.write(rowx, 0, n,content_left)
			sheet.write(rowx, 1, data.employee_id.identification_id,content_left)
			sheet.write(rowx, 2,data.employee_id.last_name,content_left)
			sheet.write(rowx, 3,data.employee_id.name,content_left)

			colx=4
			for line in data.line_ids:
				sheet.write(rowx, colx,line.name,center)
				colx+=1
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

#8 Цагийн төлөвлөгөө импорт хийх загвар эксел файл татах товч
	def print_timetable_import(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'Timetable'

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
		theader.set_bg_color('#c4d79b')

		content_right = workbook.add_format()
		content_right.set_text_wrap()
		content_right.set_font('Times new roman')
		content_right.set_font_size(9)
		content_right.set_border(style=1)
		content_right.set_align('right')

		content_left = workbook.add_format({'num_format': '###,###,###.##'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(9)
		content_left.set_border(style=1)
		content_left.set_align('left')
		
		center = workbook.add_format({'num_format': '###,###,###.##'})
		center.set_text_wrap()
		center.set_font('Times new roman')
		center.set_font_size(9)	 
		center.set_align('right')
		center.set_border(style=1)
		
		center_bold = workbook.add_format({'num_format': '###,###,###.##','bold': 1})
		center_bold.set_text_wrap()
		center_bold.set_font('Times new roman')
		center_bold.set_font_size(9)
		center_bold.set_align('right')
		center_bold.set_border(style=1)
		
		sheet = workbook.add_worksheet(u'Төлөвлөгөө')

		month_code=0
		
		if self.month=='90':
			month_code=10
		if self.month=='91':
			month_code=11
		if self.month=='92':
			month_code=12 
		else:
			month_code=self.month

		sheet.merge_range(0,0,0,3, u'Байгууллагын нэр:'+ ' ' + self.company_id.name, content_right),
		sheet.merge_range(2, 0, 2, 8, u'%s ОНЫ %s-р САРЫН ЦАГ БҮРТГЭЛ'%(self.year,month_code), h1)

		rowx=4
		save_row=4
		sheet.merge_range(rowx, 0,rowx+2,0, u'Д/д', theader),
		sheet.merge_range(rowx,1,rowx+2,1, u'Код', theader),
		sheet.merge_range(rowx,2,rowx+2,2, u'Овог', theader),
		sheet.merge_range(rowx,3,rowx+2,3, u'Нэр', theader),

		sheet.set_column('A:A', 4)
		sheet.set_column('B:B', 7)
		sheet.set_column('C:C', 15)
		sheet.set_column('D:D', 15)
		sheet.set_column('E:BB', 4)

		from_dt = datetime.strptime(str(self.date_from), DATE_FORMAT).date()
		to_dt = datetime.strptime(str(self.date_to), DATE_FORMAT).date()
		step = timedelta(days=1)
		col=4
		while from_dt <= to_dt:
			sheet.merge_range(rowx,col,rowx+2,col, str(from_dt), theader),
			from_dt += step
			col+=1

		n=1
		rowx+=3

		for data in self.line_ids:
			sheet.write(rowx, 0, n,content_left)
			sheet.write(rowx, 1, data.employee_id.identification_id,content_left)
			sheet.write(rowx, 2,data.employee_id.last_name,content_left)
			sheet.write(rowx, 3,data.employee_id.name,content_left)

			colx=4
			for line in data.line_ids:
				sheet.write(rowx, colx,line.shift_plan_id.flag,center)
				colx+=1
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
