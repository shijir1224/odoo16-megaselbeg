

from odoo import  models,_
from odoo.osv import osv
from tempfile import NamedTemporaryFile
import base64
import xlrd
import  os
from odoo.exceptions import UserError
import xlsxwriter
from io import BytesIO
import base64
try:
	# Python 2 support
	from base64 import encodestring
except ImportError:
	# Python 3.9.0+ support
	from base64 import encodebytes as encodestring
	
DATE_FORMAT = "%Y-%m-%d"

class HrEvaluationPlan(models.Model):
	_inherit = "hr.evaluation.plan"

	def action_print(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'Хэлтсийн сарын төлөвлөгөөт ажил'

		# CELL styles тодорхойлж байна
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(11)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c7def5')

		theader1 = workbook.add_format({'bold': 1})
		theader1.set_font_size(11)
		theader1.set_text_wrap()
		theader1.set_font('Times new roman')
		theader1.set_align('center')
		theader1.set_align('vcenter')
		theader1.set_border(style=1)
		
		
		content_left = workbook.add_format({'num_format': '#,##0'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(11)
		content_left.set_border(style=1)
		content_left.set_align('left')
		content_left.set_num_format('#,##0.00')

		content_left_f = workbook.add_format({})
		content_left_f.set_text_wrap()
		content_left_f.set_font('Times new roman')
		content_left_f.set_font_size(11)
		content_left_f.set_align('left')

		center_att = workbook.add_format({'num_format': '#,##0'})
		center_att.set_text_wrap()
		center_att.set_font('Times new roman')
		center_att.set_font_size(11)	 
		center_att.set_align('center')
		center_att.set_border(style=1)

		fooder = workbook.add_format({'num_format': '#,##0.0','bold': 1})
		fooder.set_font_size(10)
		fooder.set_text_wrap()
		fooder.set_font('Times new roman')
		fooder.set_align('center')
		fooder.set_align('vcenter')
		fooder.set_border(style=1)
		fooder.set_bg_color('#c4d79b')
		sheet = workbook.add_worksheet(u'Хэлтсийн сарын төлөвлөгөөт ажил')

		sheet.merge_range(3, 0, 3, 8, u'%s-р сарын %s ажилтны төлөвлөгөөт ажил гүйцэтгэл'%(self.month,self.department_id.name), h1)

		sheet.set_column('A:A', 4)
		sheet.set_column('B:B', 30)
		sheet.set_column('C:C', 35)
		sheet.set_column('D:E', 15)
		
		rowx=5
		sheet.write(rowx, 0, u'Д/д', theader),
		sheet.write(rowx,1, u'KPI', theader),
		sheet.write(rowx,2, u'Хийгдэх ажлууд', theader),
		sheet.write(rowx,3, u'Өөрийн үнэлгээ', theader),
		sheet.write(rowx,4, u'Удирдлагын үнэлгээ', theader),
		sheet.merge_range(6,0,6,2,'Өдөр тутмын үйл ажиллагааны гүйцэтгэл', theader1),
		sheet.merge_range(7,0,7,4,'Төлөвлөгөөт ажлын гүйцэтгэл', theader1),
		sheet.write(6,3, self.kpi_daily, content_left),
		sheet.write(6,4, self.kpi_daily_head, content_left),
		n=1
		rowx=7
		rowx+=1
		for data in self.line_ids:
			sheet.write(rowx, 0, n,center_att)
			sheet.write(rowx, 1, data.conf_kpi_id.name,content_left)
			sheet.write(rowx, 2,data.task,content_left)
			sheet.write(rowx, 3,data.kpi,content_left)
			sheet.write(rowx, 4,data.kpi_head,content_left)
			rowx+=1
			
			n+=1
		colx=4
		sheet.merge_range(rowx,0,rowx,2,'Төлөвлөгөөт ажлын үнэлгээний дүн', theader1),
		sheet.write(rowx,3, self.kpi_head_own, content_left),
		sheet.write(rowx,4, self.kpi_head, content_left),
		sheet.merge_range(rowx+1, 0, rowx+1, 2, u'Багийн гүйцэтгэлийн үнэлгээний дүн', theader1)
		sheet.merge_range(rowx+1,3,rowx+1, 4, self.kpi_team, content_left),


		sheet.merge_range(rowx+4, 1, rowx+4, 2, u'Үнэлгээг зөвшөөрсөн: ............................/%s.%s/'%(self.employee_id.emp_melen,self.employee_id.name), content_left_f)
		sheet.merge_range(rowx+4, 3, rowx+4, 4, u'Албан тушаал: %s'%(self.employee_id.job_id.name), content_left_f)
		sheet.merge_range(rowx+6, 1, rowx+6, 2, u'Үнэлгээ өгсөн:.................................../%s.%s/'%(self.num_employee_id.emp_melen,self.num_employee_id.name), content_left_f)
		sheet.merge_range(rowx+6, 3, rowx+6, 4, u'Албан тушааl: %s'%(self.num_employee_id.job_id.name), content_left_f)

		
		
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

class HrEvaluationEmp(models.Model):
	_inherit = "hr.evaluation.emp"


	def action_print(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'Ажилтны сарын төлөвлөгөөт ажил'

		# CELL styles тодорхойлж байна
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(11)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c7def5')

		theader1 = workbook.add_format({'bold': 1})
		theader1.set_font_size(11)
		theader1.set_text_wrap()
		theader1.set_font('Times new roman')
		theader1.set_align('center')
		theader1.set_align('vcenter')
		theader1.set_border(style=1)
		
		content_left = workbook.add_format({'num_format': '#,#0'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(11)
		content_left.set_border(style=1)
		content_left.set_align('right')
		content_left.set_num_format('#,#0')

		content_left_f = workbook.add_format({})
		content_left_f.set_text_wrap()
		content_left_f.set_font('Times new roman')
		content_left_f.set_font_size(11)
		content_left_f.set_align('right')

		center_att = workbook.add_format({'num_format': '#,##0'})
		center_att.set_text_wrap()
		center_att.set_font('Times new roman')
		center_att.set_font_size(11)	 
		center_att.set_align('center')
		center_att.set_border(style=1)

		fooder = workbook.add_format({'num_format': '#,##0.0','bold': 1})
		fooder.set_font_size(10)
		fooder.set_text_wrap()
		fooder.set_font('Times new roman')
		fooder.set_align('center')
		fooder.set_align('vcenter')
		fooder.set_border(style=1)
		fooder.set_bg_color('#c4d79b')
		sheet = workbook.add_worksheet(u'Сарын төлөвлөгөөт ажил гүйцэтгэл')

		sheet.merge_range(3, 0, 3, 8, u'%s-р сарын %s ажилтны төлөвлөгөөт ажил гүйцэтгэл'%(self.month,self.employee_id.name), h1)

		sheet.set_column('A:A', 4)
		sheet.set_column('B:B', 30)
		sheet.set_column('C:C', 35)
		sheet.set_column('D:D', 13)
		sheet.set_column('E:E', 15)
		sheet.set_column('F:F', 13)
		sheet.set_column('G:G', 15)

		rowx=6
		tatal_daily=0
		tatalsum_amount=0
		# ,('state','=','done')
		daily_id = self.env['hr.evaluation.line'].search([('year','=',self.year),('month','=',str(self.month)),('employee_id','=',self.employee_id.id)],limit=1)
		plan_id = self.env['hr.evaluation.plan'].search([('year','=',self.year),('month','=',self.month),('department_id','=',self.employee_id.department_id.id)],limit=1)
		cons_id = self.env['hr.evaluation.cons.line'].search([('year','=',self.year),('month','=',self.month),('employee_id','=',self.employee_id.id)],limit=1)
		
		sheet.write(rowx, 0, u'Д/д', theader),
		sheet.write(rowx,1, u'KPI', theader),
		sheet.write(rowx,2, u'Хийгдэх ажлууд', theader),
		sheet.write(rowx,3, u'Эзлэх жин', theader),
		sheet.write(rowx,4, u'Өөрийн үнэлгээ %', theader),
		sheet.write(rowx,5, u'Өөрийн тайлбар', theader),
		sheet.write(rowx,6, u'Удирдлагын үнэлгээ %', theader),
		sheet.write(rowx,7, u'Удирдлагын тайлбар', theader),
		sheet.merge_range(7,0,7,2,'Өдөр тутмын үйл ажиллагааны гүйцэтгэл %', theader1),
		sheet.write(7,3, '60', content_left),
		sheet.write(7,4, daily_id.score, content_left),
		sheet.write(7,5, '', content_left),
		sheet.write(7,6, daily_id.sum_amount, content_left),
		sheet.write(7,7, '', content_left),
		sheet.merge_range(8,0,8,3,'Үнэлгээ %', theader1),
		if daily_id.score:
			tatal_daily= daily_id.score * 0.6
		if daily_id.sum_amount:
			tatalsum_amount= daily_id.sum_amount * 0.6
		sheet.write(8,4,tatal_daily, content_left),
		sheet.write(8,5, '', content_left),
		sheet.write(8,6, cons_id.daily_score, content_left),
		sheet.write(8,7, '', content_left),
		sheet.merge_range(9,0,9,7,'Төлөвлөгөөт ажлын гүйцэтгэл %', theader1),

		n=1
		desc_1=''
		desc_2=''
		rowx=9
		rowx+=1
		for data in self.line_line_ids:
			if data.description:
				desc_1 = data.description
			if data.get_description:
				desc_2 = data.get_description
			sheet.write(rowx, 0, n,center_att)
			sheet.write(rowx, 1, data.conf_kpi_id.name,content_left)
			sheet.write(rowx, 2,data.task,content_left)
			sheet.write(rowx, 3,'',content_left)
			sheet.write(rowx, 4,data.own_score,content_left)
			sheet.write(rowx, 5,desc_1,content_left)
			sheet.write(rowx, 6,data.get_score,content_left)
			sheet.write(rowx, 7,desc_2,center_att)
			rowx+=1
			n+=1
		colx=6
		sheet.merge_range(rowx,0,rowx,2,'Төлөвлөгөөт ажлын үнэлгээний дүн %', theader1),
		sheet.write(rowx,3, '30', content_left),
		sheet.write(rowx,4, self.own_score * 0.3, content_left),
		sheet.write(rowx,5, '', content_left),
		sheet.write(rowx,6, cons_id.plan_score, content_left),
		sheet.write(rowx,7, '', content_left),
		sheet.merge_range(rowx+1, 0, rowx+1, 2, u'Багийн гүйцэтгэлийн үнэлгээний дүн %', theader1)
		sheet.write(rowx+1,3, '10', content_left),
		sheet.merge_range(rowx+1, 4,rowx+1, 7,cons_id.team_score, content_left),
		sheet.merge_range(rowx+2, 0, rowx+2, 2, u'Нийт %', theader1)
		sheet.write(rowx+2,3, '100', content_left),
		sheet.merge_range(rowx+2, 4,rowx+2, 7,cons_id.total_score, content_left),

		sheet.merge_range(rowx+4, 1, rowx+4, 2, u'Үнэлгээг зөвшөөрсөн: ............................/%s.%s/'%(self.employee_id.emp_melen,self.employee_id.name), content_left_f)
		sheet.merge_range(rowx+4, 3, rowx+4, 6, u'Албан тушаал: %s'%(self.employee_id.job_id.name), content_left_f)
		sheet.merge_range(rowx+6, 1, rowx+6, 2, u'Үнэлгээ өгсөн:.................................../%s.%s/'%(self.num_employee_id.emp_melen,self.num_employee_id.name), content_left_f)
		sheet.merge_range(rowx+6, 3, rowx+6, 6, u'Албан тушаал: %s'%(self.num_employee_id.job_id.name), content_left_f)

		
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
	
	def action_import(self):
		data_pool =  self.env['hr.evaluation.emp.line']
		if self.line_line_ids:
			self.line_line_ids.unlink()
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
		for item in range(7,nrows):
			row = sheet.row(item)
			conf_kpi = row[1].value
			task = row[2].value
			own_score = row[3].value
			description = row[4].value
			get_score = row[5].value
			get_description = row[6].value
			conf_id = self.env['ev.kpi.conf'].search([('name','=',conf_kpi)],limit=1)
			evaluation_data_id = data_pool.create({
				'conf_kpi_id':conf_id.id,
				'task':task,
				'own_score':own_score,
				'description':description,
				'get_score':get_score,
				'get_description':get_description,
				'line_parent_id':self.id
				})

			
	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row + 1)

	def _symbol_col(self, col):
		excelCol = str()
		div = col + 1
		while div:
			(div, mod) = divmod(div - 1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol
	

class HrEvaluationCons(models.Model):
	_inherit = "hr.evaluation.cons"
	

	def action_import(self):
		data_pool =  self.env['hr.evaluation.cons.line']
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
		for item in range(4,nrows):
			row = sheet.row(item)
			default_code = row[2].value
			daily_score = row[5].value
			plan_score = row[6].value
			team_score = row[7].value
			total_score = row[8].value
			descrition = row[9].value
			employee_id = self.env['hr.employee'].search([('identification_id','=',default_code)],limit=1)
			if employee_id:
				evaluation_data_id = data_pool.create({
					'employee_id':employee_id.id,
					'department_id':employee_id.department_id.id,
					'job_id':employee_id.job_id.id,
					'parent_id': self.id,
					'daily_score':daily_score,
					'plan_score':plan_score,
					'team_score':team_score,
					'total_score':total_score,
					'descrition':descrition,
					'parent_id':self.id
					})
			else:
				raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))
	
	def action_print(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'Гүйцэтгэлийн үнэлгээ нэгтгэл'

		# CELL styles тодорхойлж байна
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(11)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c4d79b')
		
		content_left = workbook.add_format({'num_format': '#,##0'})
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
		
		center = workbook.add_format({'num_format': '#,##0.0'})
		center.set_text_wrap()
		center.set_font('Times new roman')
		center.set_font_size(11)	 
		center.set_align('right')
		center.set_border(style=1)

		center_att = workbook.add_format({'num_format': '#,##0'})
		center_att.set_text_wrap()
		center_att.set_font('Times new roman')
		center_att.set_font_size(11)	 
		center_att.set_align('center')
		center_att.set_border(style=1)

		fooder = workbook.add_format({'num_format': '#,##0.0','bold': 1})
		fooder.set_font_size(10)
		fooder.set_text_wrap()
		fooder.set_font('Times new roman')
		fooder.set_align('center')
		fooder.set_align('vcenter')
		fooder.set_border(style=1)
		fooder.set_bg_color('#c4d79b')
		sheet = workbook.add_worksheet(u'Гүйцэтгэлийн нэгтгэл')
		

		sheet.merge_range(0, 1, 0, 8, u'БАТЛАВ. ЗАХИРГАА-ХҮНИЙ НӨӨЦИЙН ЗАХИРАЛ ...............................'' %s' '.' '%s' %(self.confirm_emp_id.last_name[:1],self.confirm_emp_id.name), h1)		
		sheet.merge_range(3, 0, 3, 8, u'%s ОНЫ %s-р САРЫН ГҮЙЦЭТГЭЛИЙН ҮНЭЛГЭЭ'%(self.year,self.month), h1)
			
		rowx=6
		
		sheet.write(rowx, 0, u'Д/д', theader),
		sheet.write(rowx,1, u'Код', theader),
		sheet.write(rowx,2, u'Овог', theader),
		sheet.write(rowx,3, u'Нэр', theader),
		sheet.write(rowx,4, u'Хэлтэс', theader),
		sheet.write(rowx,5, u'Албан тушаал', theader),
		sheet.write(rowx,6, u'Өдөр тутмын үйл ажиллагааны гүйцэтгэл-60%', theader),
		sheet.write(rowx,7, u'Төлөвлөгөөт ажлын гүйцэтгэл-30%', theader),
		sheet.write(rowx,8, u'Багийн гүйцэтгэл-10%', theader),
		sheet.write(rowx,9, u'Нийт гүйцэтгэлийн үнэлгээ', theader),
		sheet.write(rowx,10, u'Тайлбар', theader),

		sheet.set_column('A:A', 4)
		sheet.set_column('B:B', 7)
		sheet.set_column('C:C', 15)
		sheet.set_column('D:D', 15)
		sheet.set_column('E:E', 20)
		sheet.set_column('F:F', 30)
		sheet.set_column('G:J', 10)
		sheet.set_column('K:K', 20)
		n=1
		rowx+=1
		desc=''
		for data in self.line_ids:
			if data.descrition:
				desc = data.descrition
			sheet.write(rowx, 0, n,center_att)
			sheet.write(rowx, 1, data.employee_id.identification_id,content_left)
			sheet.write(rowx, 2,data.employee_id.last_name,content_left)
			sheet.write(rowx, 3,data.employee_id.name,content_left)
			sheet.write(rowx, 4,data.employee_id.department_id.name,content_left)
			sheet.write(rowx, 5,data.employee_id.job_id.name,content_left)
			sheet.write(rowx, 6,data.daily_score,center_att)
			sheet.write(rowx, 7,data.plan_score,center_att)
			sheet.write(rowx, 8,data.team_score,center_att)
			sheet.write(rowx, 9,data.total_score,center_att)
			sheet.write(rowx, 10,desc,center_att)
			
			rowx+=1
			n+=1
		colx=10
		sheet.merge_range(rowx, 0, rowx, 5, u'НИЙТ', fooder)
		l=6
		save_row=7
		while l <= colx:
			sheet.write_formula(rowx, l, '{=SUM('+self._symbol(save_row, l) + ': '+ self._symbol(rowx-1, l)+')}', fooder)
			l+=1

		sheet.merge_range(rowx+4,0,rowx+4,10,'Нэгтгэсэн:' + '.....................................................' ' %s '		   ' %s' '.' '%s' %(self.employee_id.job_id.name,self.employee_id.last_name[:1],self.employee_id.name), content_left_h),

		sheet.merge_range(rowx+6,0,rowx+6,10,'Хянасан:' + '.....................................................' ' %s '		   ' %s' '.' '%s' %(self.h_emp_id.job_id.name,self.h_emp_id.last_name[:1],self.h_emp_id.name), content_left_h),
	
		
	
		
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
	
	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row + 1)

	def _symbol_col(self, col):
		excelCol = str()
		div = col + 1
		while div:
			(div, mod) = divmod(div - 1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol
	
class HrEvaluationLine(models.Model):
	_inherit = "hr.evaluation.line"


	def action_print(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'Ажилтны өдөр тутмын ажил'

		# CELL styles тодорхойлж байна
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(11)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c7def5')

		theader1 = workbook.add_format({'bold': 1})
		theader1.set_font_size(11)
		theader1.set_text_wrap()
		theader1.set_font('Times new roman')
		theader1.set_align('center')
		theader1.set_align('vcenter')
		theader1.set_border(style=1)
		
		content_left = workbook.add_format({'num_format': '#,##0'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(11)
		content_left.set_border(style=1)
		content_left.set_align('right')
		content_left.set_num_format('#,##0.0')

		content_left_f = workbook.add_format({})
		content_left_f.set_text_wrap()
		content_left_f.set_font('Times new roman')
		content_left_f.set_font_size(11)
		content_left_f.set_align('right')

		center_att = workbook.add_format({'num_format': '#,##0'})
		center_att.set_text_wrap()
		center_att.set_font('Times new roman')
		center_att.set_font_size(11)	 
		center_att.set_align('center')
		center_att.set_border(style=1)

		fooder = workbook.add_format({'num_format': '#,##0.0','bold': 1})
		fooder.set_font_size(10)
		fooder.set_text_wrap()
		fooder.set_font('Times new roman')
		fooder.set_align('center')
		fooder.set_align('vcenter')
		fooder.set_border(style=1)
		fooder.set_bg_color('#c4d79b')
		sheet = workbook.add_worksheet(u'Сарын өдөр тутмын ажил гүйцэтгэл')

		sheet.merge_range(3, 0, 3, 8, u'%s-р сарын %s ажилтны өдөр тутмын ажил гүйцэтгэл'%(self.month,self.employee_id.name), h1)

		sheet.set_column('A:A', 4)
		sheet.set_column('B:B', 30)
		sheet.set_column('C:C', 35)
		sheet.set_column('D:D', 13)
		sheet.set_column('E:E', 15)
		sheet.set_column('F:F', 13)
		sheet.set_column('G:G', 15)

		rowx=6
		
		
		sheet.write(rowx, 0, u'Д/д', theader),
		sheet.write(rowx,1, u'Үзүүлэлт', theader),
		sheet.write(rowx,2, u'Хүрэх үр дүн', theader),
		sheet.write(rowx,3, u'Ажлын гүйцэтгэлийн хэмжүүр', theader),
		sheet.write(rowx,4, u'Өөрийн үнэлгээ %', theader),
		sheet.write(rowx,5, u'Өөрийн тайлбар', theader),
		sheet.write(rowx,6, u'Удирдлагын үнэлгээ %', theader),
		sheet.write(rowx,7, u'Удирдлагын тайлбар', theader),

		n=1
		desc_1=''
		desc_2=''
		goal=''
		rowx+=1
		for data in self.line_line_ids:
			if data.description:
				desc_1 = data.description
			if data.get_desc:
				desc_2 = data.get_desc
			if data.goal:
				goal = data.goal
			sheet.write(rowx, 0, n,center_att)
			sheet.write(rowx, 1, data.conf_id.name,content_left)
			sheet.write(rowx, 2,goal,content_left)
			sheet.write(rowx, 3,data.desc,content_left)
			sheet.write(rowx, 4,data.own_score,content_left)
			sheet.write(rowx, 5,desc_1,content_left)
			sheet.write(rowx, 6,data.get_score,content_left)
			sheet.write(rowx, 7,desc_2,center_att)
			rowx+=1
			n+=1

		sheet.merge_range(rowx, 0, rowx, 3, 'Нийт', theader)
		sheet.write(rowx, 4,self.own_score,content_left)
		sheet.write(rowx, 5,'',content_left)
		sheet.write(rowx, 6,self.sum_amount,content_left)
		sheet.write(rowx, 7,'',content_left)

		# sheet.merge_range(rowx+4, 1, rowx+4, 2, u'Үнэлгээг зөвшөөрсөн: ............................/%s.%s/'%(self.employee_id.emp_melen,self.employee_id.name), content_left_f)
		# sheet.merge_range(rowx+4, 3, rowx+4, 6, u'Албан тушаал: %s'%(self.employee_id.job_id.name), content_left_f)
		# sheet.merge_range(rowx+6, 1, rowx+6, 2, u'Үнэлгээ өгсөн:.................................../%s.%s/'%(self.num_employee_id.emp_melen,self.num_employee_id.name), content_left_f)
		# sheet.merge_range(rowx+6, 3, rowx+6, 6, u'Албан тушааl: %s'%(self.num_employee_id.job_id.name), content_left_f)

		
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
	
class HrEvaluationYearPlan(models.Model):
	_inherit = "hr.evaluation.year.plan"


	def action_print(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'Улирлын төлөвлөгөө'

		# CELL styles тодорхойлж байна
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(11)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c4d79b')
		
		content_left = workbook.add_format({'num_format': '#,##0'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(11)
		content_left.set_border(style=1)
		content_left.set_align('left')
		content_left.set_align('vcenter')
		content_left.set_num_format('#,##0.00')

		content_left_h = workbook.add_format({})
		content_left_h.set_text_wrap()
		content_left_h.set_font('Times new roman')
		content_left_h.set_font_size(11)
		content_left_h.set_align('left')
		
		
		center = workbook.add_format({})
		center.set_text_wrap()
		center.set_font('Times new roman')
		center.set_font_size(11)	 
		center.set_align('center')
		center.set_align('vcenter')
		center.set_border(style=1)

		center_att = workbook.add_format({'num_format': '#,##0'})
		center_att.set_text_wrap()
		center_att.set_font('Times new roman')
		center_att.set_font_size(11)	 
		center_att.set_align('vcenter')
		center_att.set_align('center')
		center_att.set_border(style=1)

		fooder = workbook.add_format({'num_format': '#,##0.0','bold': 1})
		fooder.set_font_size(10)
		fooder.set_text_wrap()
		fooder.set_font('Times new roman')
		fooder.set_align('center')
		fooder.set_align('vcenter')
		fooder.set_border(style=1)
		fooder.set_bg_color('#c4d79b')
		sheet = workbook.add_worksheet(u'Улирлын төлөвлөгөө')

		sheet.merge_range(3, 0, 3, 8, u'%s -н %s оны %s-р улирлын төлөвлөгөө'%(self.department_id.name,self.year,self.sprint), h1)

		rowx=6
		
		sheet.write(rowx, 0, u'Д/д', theader),
		sheet.write(rowx,1, u'ЗХ тулгуур зорилго', theader),
		sheet.write(rowx,2, u'Стратеги зорилго', theader),
		sheet.write(rowx,3, u'Хүрэх үр дүн', theader),

		sheet.write(rowx,4, u'KPI', theader),
		sheet.write(rowx,5, u'Хийгдэх ажил', theader),
		sheet.write(rowx,6, u'R:Хянах', theader),
		sheet.write(rowx,7, u'A:Батлах, шийдвэрлэх', theader),
		sheet.write(rowx,8, u'S:Дэмжих зөвлөлдөх', theader),
		sheet.write(rowx,9, u'I:Мэдээлэлтэй байх', theader),
		sheet.write(rowx,10, u'Сар', theader),

		sheet.set_column('A:A', 4)
		sheet.set_column('B:I', 15)
		n=1
		rowx+=1
		for data in self.line_ids:
			rowl = rowx
			t = 0
			for dd in data.line_line_ids:
				sheet.write(rowl, 4,dd.conf_kpi_id.name,content_left)
				sheet.write(rowl, 5,dd.task,content_left)
				sheet.write(rowl, 6,', '.join(dd.r_employee_ids.mapped('name')) or '',center_att)
				sheet.write(rowl, 7,', '.join(dd.t_employee_ids.mapped('name')) or '',center_att)
				sheet.write(rowl, 8,', '.join(dd.s_employee_ids.mapped('name')) or '',center_att)
				sheet.write(rowl, 9,', '.join(dd.i_employee_ids.mapped('name')) or '',center_att)
				sheet.write(rowl, 10,dd.month,center)
				rowl += 1
				t += 1
			if t <= 1:
				sheet.write(rowx, 0, n,center)
				sheet.write(rowx, 1,dict(data._fields['pillar_goal'].selection).get(data.pillar_goal),content_left)
				sheet.write(rowx, 2,data.ev_objective_id.name,content_left)
				sheet.write(rowx, 3,data.goal,content_left)
			else:
				sheet.merge_range(rowx, 0, rowx+t-1, 0, n, center)
				sheet.merge_range(rowx, 1, rowx+t-1, 1, dict(data._fields['pillar_goal'].selection).get(data.pillar_goal), content_left)
				sheet.merge_range(rowx, 2, rowx+t-1, 2, data.ev_objective_id.name, content_left)
				sheet.merge_range(rowx, 3, rowx+t-1, 3, data.goal, content_left)

			rowx+=t
			n+=1
		colx=10

		
		sheet.merge_range(rowx+4,3,rowx+4,10,'Боловсруулсан: %s .....................................................%s.%s ' %(self.employee_id.job_id.name,self.employee_id.emp_melen,self.employee_id.name), content_left_h),
		sheet.merge_range(rowx+6,3,rowx+6,10,'Хянасан: %s .....................................................%s.%s ' %(self.n_employee_id.job_id.name,self.n_employee_id.emp_melen,self.n_employee_id.name), content_left_h),

		
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
	
	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row + 1)

	def _symbol_col(self, col):
		excelCol = str()
		div = col + 1
		while div:
			(div, mod) = divmod(div - 1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol



class HrEvaluationYearPlanLine(models.Model):
	_inherit = "hr.evaluation.year.plan.line"


	def action_import(self):
		data_pool =  self.env['hr.evaluation.year.plan.line.line']
		if self.line_line_ids:
			self.line_line_ids.unlink()
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
		for item in range(1,nrows):
			row = sheet.row(item)
			conf_kpi = row[0].value
			task = row[1].value
			month = row[2].value
			conf = self.env['ev.kpi.conf'].create({
				'name':conf_kpi,
				'department_id':self.department_id.id
			})
			evaluation_data_id = data_pool.create({
				'parent_id': self.id,
				'conf_kpi_id':conf.id,
				'task':task,
				'month':month,
				})


class HrProjectEvaluation(models.Model):
	_inherit = "hr.project.evaluation"


	def action_import(self):
		data_pool =  self.env['hr.project.evaluation.line']
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
		for item in range(4,nrows):
			row = sheet.row(item)
			default_code = row[2].value
			amount_score = row[14].value
			description = row[5].value
			employee_id = self.env['hr.employee'].search([('identification_id','=',default_code)],limit=1)
			if employee_id:
				evaluation_data_id = data_pool.create({
					'employee_id':employee_id.id,
					'employee_type':employee_id.employee_type,
					'parent_id': self.id,
					'amount_score':amount_score,
					'description':description,
					'parent_id':self.id
					})
			else:
				raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))

	def action_print(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'Төслийн гүйцэтгэл'

		# CELL styles тодорхойлж байна
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(11)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c4d79b')
		
		content_left = workbook.add_format({'num_format': '#,##0'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(11)
		content_left.set_border(style=1)
		content_left.set_align('left')
		content_left.set_num_format('#,##0.00')
		
		center = workbook.add_format({'num_format': '#,##0.0'})
		center.set_text_wrap()
		center.set_font('Times new roman')
		center.set_font_size(11)	 
		center.set_align('right')
		center.set_border(style=1)

		center_att = workbook.add_format({'num_format': '#,##0'})
		center_att.set_text_wrap()
		center_att.set_font('Times new roman')
		center_att.set_font_size(11)	 
		center_att.set_align('center')
		center_att.set_border(style=1)

		content_left_h = workbook.add_format({})
		content_left_h.set_text_wrap()
		content_left_h.set_font('Times new roman')
		content_left_h.set_font_size(11)
		content_left_h.set_align('left')

		fooder = workbook.add_format({'num_format': '#,##0.0','bold': 1})
		fooder.set_font_size(10)
		fooder.set_text_wrap()
		fooder.set_font('Times new roman')
		fooder.set_align('center')
		fooder.set_align('vcenter')
		fooder.set_border(style=1)
		fooder.set_bg_color('#c4d79b')
		sheet = workbook.add_worksheet(u'Төслийн гүйцэтгэл')

		sheet.merge_range(0, 1, 0, 8, u'БАТЛАВ. ЗАХИРГАА-ХҮНИЙ НӨӨЦИЙН ЗАХИРАЛ ...............................'' %s' '.' '%s' %(self.confirm_emp_id.last_name[:1],self.confirm_emp_id.name), h1)	

		sheet.merge_range(3, 0, 3, 8, u'%s ОНЫ %s-р САРЫН ТӨСЛИЙН ГҮЙЦЭТГЭЛ'%(self.year,self.month), h1)

		rowx=6
		sheet.set_column('A:A', 4)
		sheet.set_column('B:B', 7)
		sheet.set_column('C:C', 15)
		sheet.set_column('D:D', 15)
		sheet.set_column('E:E', 20)
		sheet.set_column('F:F', 30)
		sheet.set_column('G:J', 10)
		sheet.set_column('K:K', 20)

		sheet.write(rowx, 0, u'Д/д', theader),
		sheet.write(rowx,1, u'Код', theader),
		sheet.write(rowx,2, u'Овог', theader),
		sheet.write(rowx,3, u'Нэр', theader),
		sheet.write(rowx,4, u'Албан тушаал', theader),
		sheet.write(rowx,5, u'Ажилтны төлөв', theader),
		sheet.write(rowx,6, u'Ирцийн хувь', theader),
		sheet.write(rowx,7, u'Сахилгын шийтгэл', theader),
		sheet.write(rowx,8, u'ХАБЭА,БО-ны зөрчил', theader),
		sheet.write(rowx,9, u'Үйлдвэрлэлийн осол, хурц хордлого бүртгэгдсэн эсэх', theader),
		sheet.write(rowx,10, u'Тайлбар', theader),
		sheet.write(rowx,11, u'Хүдрийн бүтээл', theader),
		sheet.write(rowx,12, u'Төл.бус зогсолтын цагт ногдох хувь', theader),
		sheet.write(rowx,13, u'Гүй.урамшуулал тооцох хувь', theader),
		sheet.write(rowx,14, u'Шийтгэлийн шалтгаан', theader),
		sheet.write(rowx,15, u'Үйлд.осол, хурц.хор шалтгаан', theader),
		n=1
		rowx+=1
		for data in self.line_ids:
			description = ''
			disc_type=''
			injury_reason=''
			if data.description:
				description = data.description
			if data.disc_type:
				disc_type = data.disc_type
			if data.injury_reason:
				injury_reason = data.injury_reason
			sheet.write(rowx, 0, n,center_att)
			sheet.write(rowx, 1, data.employee_id.identification_id,content_left)
			sheet.write(rowx, 2,data.employee_id.last_name,content_left)
			sheet.write(rowx, 3,data.employee_id.name,content_left)
			sheet.write(rowx, 4,data.employee_id.job_id.name,content_left)
			sheet.write(rowx,5,dict(data.employee_id._fields['employee_type'].selection).get(data.employee_id.employee_type),content_left)
			sheet.write(rowx, 6,data.attendance,center_att)
			sheet.write(rowx, 7,dict(data._fields['discipline'].selection).get(data.discipline),center_att)
			sheet.write(rowx, 8,dict(data._fields['hab'].selection).get(data.hab),center_att)
			sheet.write(rowx, 9,dict(data._fields['accident'].selection).get(data.accident),center_att)
			sheet.write(rowx, 10,description,center_att)
			sheet.write(rowx, 11,data.huder,center_att)
			sheet.write(rowx, 12,data.stop,center_att)
			sheet.write(rowx, 13,data.amount_score,center_att)
			sheet.write(rowx, 14,disc_type,center_att)
			sheet.write(rowx, 15,injury_reason,center_att)

			rowx+=1
			n+=1
		colx=14
		sheet.merge_range(rowx, 0, rowx, 5, u'НИЙТ', fooder)
		l=6
		save_row=7
		while l <= colx:
			sheet.write_formula(rowx, l, '{=SUM('+self._symbol(save_row, l) + ': '+ self._symbol(rowx-1, l)+')}', fooder)
			l+=1
		

		sheet.merge_range(rowx+4,0,rowx+4,10,'Нэгтгэсэн:' + '.....................................................' ' %s '		   ' %s' '.' '%s' %(self.employee_id.job_id.name,self.employee_id.last_name[:1],self.employee_id.name), content_left_h),

		sheet.merge_range(rowx+6,0,rowx+6,10,'Хянасан:' + '.....................................................' ' %s '		   ' %s' '.' '%s' %(self.h_emp_id.job_id.name,self.h_emp_id.last_name[:1],self.h_emp_id.name), content_left_h),
	
		

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
	
	
		

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row + 1)

	def _symbol_col(self, col):
		excelCol = str()
		div = col + 1
		while div:
			(div, mod) = divmod(div - 1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol