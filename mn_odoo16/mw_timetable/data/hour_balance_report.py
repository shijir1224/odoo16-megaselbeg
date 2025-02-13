import xlrd
import odoo
from xlsxwriter.utility import xl_rowcol_to_cell
import xlsxwriter
from io import BytesIO
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


class HourBalanceDynamic(models.Model):
	_inherit = "hour.balance.dynamic"


	# Динамик цагийн балансыг импорт хийхэд эхлээд цагийн тохиргоог дугаарлан оруулсан байх шаардлагатай бөгөөд экселийн H:5 эхлэн эксел дээр зоосон байх шаардлагатай.
	def action_import_hour_balance(self):
		balance_pool =  self.env['hour.balance.dynamic.line']
		balance_line_pool =  self.env['hour.balance.dynamic.line.line']
		balance_line_hour_pool =  self.env['hour.balance.dynamic.line.line.hour']
		if self.balance_line_ids:
			self.balance_line_ids.unlink()
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
		sequence=1
		for item in range(6,nrows):
			row = sheet.row(item)
			default_code = row[2].value
			day_to_work_month = row[5].value
			hour_to_work_month = row[6].value
			employee_ids = self.env['hr.employee'].search([('identification_id','=',default_code)])
			employee_register_ids = self.env['hr.employee'].search([('passport_id','=',default_code),('company_id','=',self.company_id.id)])
			if self.register_import==True:
				if employee_register_ids:
					balance_data_ids = balance_pool.create({
						'employee_id':employee_register_ids.id,
						'year':self.year,
						'month':self.month,
						'parent_id': self.id,
						'department_id':employee_register_ids.department_id.id,
						'job_id':employee_register_ids.job_id.id,
						'employee_type':employee_register_ids.employee_type,
						'day_to_work_month':day_to_work_month,
						'hour_to_work_month':hour_to_work_month,
						'sequence':sequence,
						})
					sequence+=1
					
				else:
					raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))
			else:
				if employee_ids:
					balance_data_ids = balance_pool.create({'employee_id':employee_ids.id,
						'year':self.year,
						'month':self.month,
						'parent_id': self.id,
						'department_id':employee_ids.department_id.id,
						'job_id':employee_ids.job_id.id,
						'employee_type':employee_ids.employee_type,
						'day_to_work_month':day_to_work_month,
						'hour_to_work_month':hour_to_work_month,
						'sequence':sequence,
						})
					sequence+=1
				else:
					raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))
			for dd in balance_data_ids:
				# дугаарлалт авах 7 буюу H багана
				col = 7
				#  дугаарлалт авах 5 мөр
				rowh = sheet.row(5)
				for ncol in range(7,ncols):
					number = rowh[col].value
					conf_pool =  self.env['hour.balance.dynamic.configuration'].search([('number','=',number),('company_id','=',self.company_id.id),('work_location_id','in',(self.work_location_id.id,False))],limit=1)
					if conf_pool:
						balance_line_pool = balance_line_pool.create({
								'parent_id':dd.id,
								'conf_id':conf_pool.id,
								'hour':row[col].value,
								'hour_type': conf_pool.hour_type
								})
						balance_line_hour_pool = balance_line_hour_pool.create({
								'parent_id':dd.id,
								'conf_id':conf_pool.id,
								'name':row[col].value,
								})
						number = []
						col +=1
						item +=1
					else:
						raise UserError(_('%s дугаартай цагийн тохиргоо хийгдээгүй байна.')%(number))
	

	# excel хэвлэлт
	def print_dyn_hour_balance(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'Цагийн баланс'

		# CELL styles тодорхойлж байна
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		left_h1 = workbook.add_format({'bold': 1})
		left_h1.set_font_size(11)
		left_h1.set_font('Times new roman')
		left_h1.set_align('left')

		h2 = workbook.add_format()
		h2.set_font_size(11)
		h2.set_font('Times new roman')
		h2.set_align('left')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(11)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c4d79b')

		content_right = workbook.add_format()
		content_right.set_text_wrap()
		content_right.set_font('Times new roman')
		content_right.set_font_size(11)
		content_right.set_border(style=1)
		content_right.set_align('right')

		content_left = workbook.add_format({'num_format': '#,##0.00'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(11)
		content_left.set_border(style=1)
		content_left.set_align('left')
		content_left.set_num_format('#,##0.00')
		
		content_left_h = workbook.add_format({})
		content_left_h.set_text_wrap()
		content_left_h.set_font('Times new roman')
		content_left_h.set_font_size(11)
		content_left_h.set_align('left')
		
		center = workbook.add_format({'num_format': '#,##0.00'})
		center.set_text_wrap()
		center.set_font('Times new roman')
		center.set_font_size(11)	 
		center.set_align('right')
		center.set_border(style=1)

		center_att = workbook.add_format({'num_format': '#,##0.0'})
		center_att.set_text_wrap()
		center_att.set_font('Times new roman')
		center_att.set_font_size(11)	 
		center_att.set_align('right')
		center_att.set_border(style=1)

		

		fooder = workbook.add_format({'num_format': '#,##0.0','bold': 1})
		fooder.set_font_size(10)
		fooder.set_text_wrap()
		fooder.set_font('Times new roman')
		fooder.set_align('center')
		fooder.set_align('vcenter')
		fooder.set_border(style=1)
		fooder.set_bg_color('#c4d79b')
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

		
		sheet.merge_range(3, 0, 3, 8, u'%s ОНЫ %s-р САРЫН ЦАГИЙН БАЛАНС'%(self.year,month_code), h1)

		rowx=6
		save_row=4
		sheet.write(rowx, 0, u'Д/д', theader),
		sheet.write(rowx,1, u'Код', theader),
		sheet.write(rowx,2, u'Регистр', theader),
		sheet.write(rowx,3, u'Овог', theader),
		sheet.write(rowx,4, u'Нэр', theader),
		sheet.write(rowx,5, u'Алба нэгж', theader),
		sheet.write(rowx,6, u'Албан тушаал', theader),
		sheet.write(rowx,7, u'АЗ өдөр', theader),
		sheet.write(rowx,8, u'АЗ цаг', theader),

		sheet.set_column('A:A', 4)
		sheet.set_column('B:B', 7)
		sheet.set_column('C:C', 15)
		sheet.set_column('D:D', 15)
		sheet.set_column('E:E', 20)
		sheet.set_column('F:G', 30)
		sheet.set_column('H:BB', 10)

		confs = self.env['hour.balance.dynamic.configuration'].search([('company_id','=',self.company_id.id),('work_location_id','in',(self.work_location_id.id,False))])

		col=9
		for c in confs:
			sheet.write(rowx,col, c.name, theader),
			col+=1
		n=1
		colj=col
		sheet.write(rowx,colj, u'Ирцийн хувь', theader),
		sheet.write(rowx,colj+1, u'Тайлбар', theader),
		rowx+=1
		desc=''
		for data in self.balance_line_ids:
			if data.description:
				desc = data.description
			else:
				desc =''
			sheet.write(rowx, 0, n,content_left)
			sheet.write(rowx, 1, data.employee_id.identification_id,content_left)
			sheet.write(rowx, 2, data.employee_id.passport_id,content_left)
			sheet.write(rowx, 3,data.employee_id.last_name,content_left)
			sheet.write(rowx, 4,data.employee_id.name,content_left)
			sheet.write(rowx, 5,data.employee_id.department_id.name,content_left)
			sheet.write(rowx, 6,data.employee_id.job_id.name,content_left)
			sheet.write(rowx, 7,data.day_to_work_month,center_att)
			sheet.write(rowx, 8,data.hour_to_work_month,center_att)
			
			colx=9
			for line in data.balance_line_line_ids:
				sheet.write(rowx, colx,line.hour,center)
				colx+=1
			
			colj = colx
			sheet.write(rowx, colj,data.att_procent,content_left)
			sheet.write(rowx, colj+1,desc,content_left)
			rowx+=1
			n+=1
			
		rowj = rowx
		sheet.merge_range(rowx, 0, rowx, 6, u'НИЙТ', fooder)
		l=6
		colx = colj
		while l <= colx:
			sheet.write_formula(rowx, l, '{=SUM('+self._symbol(save_row-1, l) +':'+ self._symbol(rowx-1, l)+')}', fooder)
			l+=1
		
		if self.confirm_emp_id:
			sheet.merge_range(rowj+3,5,rowj+3,20,'Баталсан: ' '.....................................................' ' %s '			' %s '' %s' %(self.confirm_job_id.name,self.confirm_emp_id.last_name[:1],self.confirm_emp_id.name),content_left_h),
		sheet.merge_range(rowj+4,5,rowj+4,20,'Тайлан гаргасан:' '.....................................................'			' %s' '.' '%s' %( self.employee_id.last_name[:1],self.employee_id.name), content_left_h),
		
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