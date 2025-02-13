from odoo import fields, models
import time
import xlsxwriter
from odoo.exceptions import UserError
from io import BytesIO
import base64

fmt = '%Y-%m-%d'

class ConsolidatedReport(models.TransientModel):
	_name = "consolidated.report"
	_description = "Consolidated Report"

	mining_location_ids = fields.Many2many('env.mining', string='Үйлдвэр, Уурхай', domain="[('is_active','=', 'active')]")
	start_date = fields.Date(string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'), required=True)
	end_date = fields.Date(string=u'Дуусах огноо', required=True)

	def export_report(self):
		if self.start_date and self.end_date:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Нэгтгэл тайлан '+str(self.start_date)+'-'+str(self.end_date)+'.xlsx'

			h1 = workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header = workbook.add_format({'bold': 1})
			header.set_text_wrap()
			header.set_font_size(9)
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)
			header.set_bg_color('#fff2cc')
 
			header_wrap = workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(9)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#99ccff')

			number_right = workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(9)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_right = workbook.add_format()
			contest_right.set_text_wrap()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			sub_total_90 = workbook.add_format({'bold': 1})
			sub_total_90.set_text_wrap()
			sub_total_90.set_font_size(9)
			sub_total_90.set_align('center')
			sub_total_90.set_align('vcenter')
			sub_total_90.set_border(style=1)
			sub_total_90.set_bg_color('#F7EE5E')
			sub_total_90.set_rotation(90)
			
			worksheet = workbook.add_worksheet(u'Сургалт')
			worksheet.set_zoom(100)
			row = 0
			worksheet.merge_range(row,0,row,8, u'Сургалтын тайлан', contest_center)

			trainings = self.env['env.training'].search([('training_date','>=',self.start_date),('training_date','<=',self.end_date),('state','=','done'),('mining_location','in',self.mining_location_ids.ids)])

			inspections = self.env['env.inspection.line'].search([('inspection_id.inspection_date','>=',self.start_date),('inspection_id.inspection_date','<=',self.end_date),('inspection_id.state','=','done'),('inspection_id.mining_location','in',self.mining_location_ids.ids)], order="create_date desc")
			waters = self.env['env.water.line'].search([('water_id.date','>=',self.start_date),('water_id.date','<=',self.end_date),('water_id.state','=','done'),('water_id.mining_location','in',self.mining_location_ids.ids)], order="create_date desc")
			wastes = self.env['env.waste'].search([('waste_date','>=',self.start_date),('waste_date','<=',self.end_date),('state','=','done'),('mining_location','in',self.mining_location_ids.ids)], order="create_date desc")
			rehab_lines = self.env['env.rehab.land'].search([('used_date','>=',self.start_date),('used_date','<=',self.end_date),('state','=','done'),('mining_location','in',self.mining_location_ids.ids)], order="create_date desc")
			rehab_lands = self.env['env.rehab.line'].search([('date','>=',self.start_date),('date','<=',self.end_date),('state','=','done'),('mining_location','in',self.mining_location_ids.ids)], order="create_date desc")
			animals = self.env['env.animal'].search([('date','>=',self.start_date),('date','<=',self.end_date),('state','=','done'),('mining_location','in',self.mining_location_ids.ids)], order="create_date desc")
			expenses = self.env['env.expense'].search([('expense_date','>=',self.start_date),('expense_date','<=',self.end_date),('state','=','done'),('mining_location','in',self.mining_location_ids.ids)], order="create_date desc")
			gardens = self.env['env.garden.line'].search([('date','>=',self.start_date),('date','<=',self.end_date),('state','=','done'),('mining_location','in',self.mining_location_ids.ids)], order="create_date desc")
			trees = self.env['env.tree.line'].search([('date','>=',self.start_date),('date','<=',self.end_date),('state','=','done'),('mining_location','in',self.mining_location_ids.ids)], order="create_date desc")

			# TABLE HEADER
			row = 1
			worksheet.set_row(0, 28)	
			worksheet.write(row, 0, u'№', header)
			worksheet.write(row, 1, u'Үйлдвэр, уурхай', header)
			worksheet.write(row, 2, u'Сургалтын огноо ', header)
			worksheet.write(row, 3, u'Сар', header)
			worksheet.write(row, 4, u'Сургалтын сэдэв', header)
			worksheet.write(row, 5, u'Суралцагчид', header)
			worksheet.write(row, 6, u'Суралцагчдын тоо', header)
			worksheet.write(row, 7, u'Сургалт явуулсан', header)
			worksheet.write(row, 8, u'Бүртгэсэн ', header)
			kk = 2
			number = 1
			worksheet.set_column('A:A', 5)
			worksheet.set_column('B:B', 30)
			worksheet.set_column('C:C', 30)
			worksheet.set_column('D:D', 30)
			worksheet.set_column('E:E', 30)
			worksheet.set_column('F:F', 30)
			worksheet.set_column('G:G', 30)
			worksheet.set_column('H:H', 30)
			worksheet.set_column('I:I', 30)

			# DATA зурах
			if trainings:
				for item in trainings:
					worksheet.write(kk, 0, number, contest_center)
					worksheet.write(kk, 1, item.mining_location.name if item.mining_location else ' ', contest_center)
					worksheet.write(kk, 2, item.training_date.strftime(fmt) if item.training_date else ' ', contest_center)
					worksheet.write(kk, 3, item.training_date.month if item.training_date else ' ', contest_center)
					# worksheet.write(kk, 4, item.topic_id.name if item.topic_id else ' ', contest_center)
					# others = item.filtered(lambda r: r.other != False)
					names = []
					names += item.mapped('topic_id.name')
					# worksheet.merge_range(29, 2, 29, 5, ', '.join([(n) for n in names]) if daily else ' ', normal_wrap)
					worksheet.write(kk, 4, ', '.join([(n) for n in names]) if item.topic_id else ' ', contest_center)
					worksheet.write(kk, 5, dict(item._fields['trainee_type'].selection).get(item.trainee_type) if item.trainee_type else ' ', contest_center)
					worksheet.write(kk, 6, item.number_of_trainees if item.number_of_trainees else 0, contest_center)
					worksheet.write(kk, 7, item.employee_id.name if item.employee_id else ' ', contest_center)
					worksheet.write(kk, 8, item.create_uid.name if item.create_uid else ' ', contest_center)
					kk += 1
					number += 1
			
			worksheet2 = workbook.add_worksheet(u'Үл зөрчих')
			worksheet2.set_zoom(100)
			row = 0
			worksheet2.merge_range(row,0,row,12, u'Үл зохицол тайлан', contest_center)
			
			# TABLE HEADER
			row = 1
			worksheet2.set_row(0, 28)	
			worksheet2.write(row, 0, u'№', header)
			worksheet2.write(row, 1, u'Үйлдвэр, уурхай', header)
			worksheet2.write(row, 2, u'Зөрчил, дутагдал', header)
			worksheet2.write(row, 3, u'Юу', header)
			worksheet2.write(row, 4, u'Яагаад', header)
			worksheet2.write(row, 5, u'Хэн илрүүлсэн', header)
			worksheet2.write(row, 6, u'Байршил', header)
			worksheet2.write(row, 7, u'Хэрхэн арга хэмжээ авсан?', header)
			worksheet2.write(row, 8, u'Хэрхэн арга хэмжээ авсан /Тайлбар/ ', header)
			worksheet2.write(row, 9, u'Удирдлагын зааварчилгаа', header)
			worksheet2.write(row, 10, u'Огноо ', header)
			worksheet2.write(row, 11, u'Сар', header)
			worksheet2.write(row, 12, u'Бүртгэсэн ', header)

			kk = 2
			number = 1
			worksheet2.set_column('A:A', 5)
			worksheet2.set_column('B:B', 30)
			worksheet2.set_column('C:C', 30)
			worksheet2.set_column('D:D', 30)
			worksheet2.set_column('E:E', 30)
			worksheet2.set_column('F:F', 30)
			worksheet2.set_column('G:G', 30)
			worksheet2.set_column('H:H', 30)
			worksheet2.set_column('I:I', 30)
			worksheet2.set_column('J:J', 30)
			worksheet2.set_column('K:K', 30)
			worksheet2.set_column('L:L', 30)
			worksheet2.set_column('M:M', 30)
			worksheet2.set_column('N:N', 30)
			# DATA зурах
			if inspections:
				for item in inspections:
					worksheet2.write(kk, 0, number, contest_center)
					worksheet2.write(kk, 1, item.inspection_id.mining_location.name if item.inspection_id.mining_location else ' ', contest_center)
					worksheet2.write(kk, 2, item.violation.name if item.violation else ' ', contest_center)
					worksheet2.write(kk, 3, item.violation_subtype.violation_subtype if item.violation_subtype else ' ', contest_center)
					worksheet2.write(kk, 4, item.violation_reason.reason if item.violation_reason else ' ', contest_center)
					worksheet2.write(kk, 5, dict(item._fields['inspected_by'].selection).get(item.inspected_by) if item.inspected_by else ' ', contest_center)
					worksheet2.write(kk, 6, item.location.name if item.location else ' ', contest_center)
					names = []
					names += item.violation_response.mapped('response')
					worksheet2.write(kk, 7, ', '.join([(n) for n in names]) if item.violation_response else ' ', contest_center)
					# worksheet2.write(kk, 7, item.violation_response if item.violation_response else ' ', contest_center)
					worksheet2.write(kk, 8, item.violation_response_comment if item.violation_response_comment  else ' ', contest_center)
					worksheet2.write(kk, 9, item.inspection_id.manager_comment if item.inspection_id.manager_comment else ' ', contest_center)
					worksheet2.write(kk, 10, item.inspection_id.inspection_date.strftime(fmt) if item.inspection_id.inspection_date else ' ', contest_center)
					worksheet2.write(kk, 11, item.inspection_id.inspection_date.strftime(fmt) if item.inspection_id.inspection_date else ' ', contest_center)
					worksheet2.write(kk, 12, item.inspection_id.create_uid.name if item.inspection_id.create_uid else ' ', contest_center)

					kk += 1
					number += 1

			worksheet3 = workbook.add_worksheet(u'Ус ашиглалт')
			worksheet3.set_zoom(100)
			row = 0
			worksheet3.merge_range(row,0,row,13, u'Ус ашиглалтын тайлан', contest_center)
			
			# TABLE HEADER
			row = 1
			worksheet3.set_row(0, 28)	
			worksheet3.write(row, 0, u'№', header)
			worksheet3.write(row, 1, u'Үйлдвэр, уурхай', header)
			worksheet3.write(row, 2, u'Он', header)
			worksheet3.write(row, 3, u'Сар', header)
			worksheet3.write(row, 4, u'Зориулалт ', header)
			worksheet3.write(row, 5, u'Усны эх сурвалж', header)
			worksheet3.write(row, 6, u'Зөвшөөрөгдсөн хэмжээ /м3/', header)
			worksheet3.write(row, 7, u'Нийт хэмжээ /м3/', header)
			worksheet3.write(row, 8, u'Үнэ /м3/', header)
			worksheet3.write(row, 9, u'Төлбөр дүгнэлтээр', header)
			worksheet3.write(row, 10, u'Нийт төлөх дүн ', header)
			worksheet3.write(row, 11, u'Нийт төлсөн дүн', header)
			worksheet3.write(row, 12, u'Төлбөрийн үлдэгдэл ', header)
			worksheet3.write(row, 13, u'Бүртгэсэн ', header)

			kk = 2
			number = 1
			worksheet3.set_column('A:A', 5)
			worksheet3.set_column('B:B', 30)
			worksheet3.set_column('C:C', 30)
			worksheet3.set_column('D:D', 30)
			worksheet3.set_column('E:E', 30)
			worksheet3.set_column('F:F', 30)
			worksheet3.set_column('G:G', 30)
			worksheet3.set_column('H:H', 30)
			worksheet3.set_column('I:I', 30)
			worksheet3.set_column('J:J', 30)
			worksheet3.set_column('K:K', 30)
			worksheet3.set_column('L:L', 30)
			worksheet3.set_column('M:M', 30)
			worksheet3.set_column('N:N', 30)
			# DATA зурах
			if waters:
				for item in waters:
					worksheet3.write(kk, 0, number, contest_center)
					worksheet3.write(kk, 1, item.water_id.mining_location.name if item.water_id.mining_location else ' ', contest_center)
					worksheet3.write(kk, 2, item.water_id.date.strftime('%Y') if item.water_id.date else ' ', contest_center)
					worksheet3.write(kk, 3, item.water_id.date.strftime('%m') if item.water_id.date else ' ', contest_center)
					worksheet3.write(kk, 4, item.dedication_id.name if item.dedication_id else ' ', contest_center)
					worksheet3.write(kk, 5, item.water_source.name if item.water_source else ' ', contest_center)
					worksheet3.write(kk, 6, item.water_id.amount if item.water_id else 0, contest_center)
					# worksheet3.write(kk, 7, item.water_id.total_amount if item.water_id else 0, contest_center)
					worksheet3.write(kk, 7, item.amount if item.water_id else 0, contest_center)
					worksheet3.write(kk, 8, item.price if item.price else 0, contest_center)
					worksheet3.write(kk, 9, item.water_id.allowed_payment if item.water_id else 0, contest_center)
					worksheet3.write(kk, 10, item.total_amount if item.water_id else 0, contest_center)
					worksheet3.write(kk, 11, item.water_id.total_payment if item.water_id.total_payment else 0, contest_center)
					# worksheet3.write(kk, 12, item.water_id.balance if item.water_id.balance else 0, contest_center)
					worksheet3.write(kk, 13, item.water_id.create_uid.name if item.create_uid else ' ', contest_center)
					kk += 1
					number += 1

			worksheet4 = workbook.add_worksheet(u'Хог хаягдал')
			worksheet4.set_zoom(100)
			row = 0
			worksheet4.merge_range(row, 0, row, 9, u'Хог хагдал тайлан', contest_center)
			
			# TABLE HEADER
			row = 1
			worksheet4.set_row(0, 28)	
			worksheet4.write(row, 0, u'№', header)
			worksheet4.write(row, 1, u'Үйлдвэр, уурхай', header)
			worksheet4.write(row, 2, u'Он', header)
			worksheet4.write(row, 3, u'Сар', header)
			worksheet4.write(row, 4, u'Хог хаягдлын төрөл ', header)
			worksheet4.write(row, 5, u'Хог хаягдлын хэмжээ /т/', header)
			worksheet4.write(row, 6, u'Дахин ашигласан /т/', header)
			worksheet4.write(row, 7, u'Дахин ашигласан хувь', header)
			worksheet4.write(row, 8, u'Тайлбар', header)
			worksheet4.write(row, 9, u'Бүртгэсэн', header)

			kk = 2
			number = 1
			worksheet4.set_column('A:A', 5)
			worksheet4.set_column('B:B', 30)
			worksheet4.set_column('C:C', 30)
			worksheet4.set_column('D:D', 30)
			worksheet4.set_column('E:E', 30)
			worksheet4.set_column('F:F', 30)
			worksheet4.set_column('G:G', 30)
			worksheet4.set_column('H:H', 30)
			worksheet4.set_column('I:I', 30)
			worksheet4.set_column('J:J', 30)
	
			# DATA зурах
			if wastes:
				for item in wastes:
					worksheet4.write(kk, 0, number, contest_center)
					worksheet4.write(kk, 1, item.mining_location.name if item.mining_location else ' ', contest_center)
					worksheet4.write(kk, 2, item.waste_date.strftime('%Y') if item.waste_date else ' ', contest_center)
					worksheet4.write(kk, 3, item.waste_date.strftime('%m') if item.waste_date else ' ', contest_center)
					worksheet4.write(kk, 4, item.waste_type.name if item.waste_type else ' ', contest_center)
					worksheet4.write(kk, 5, item.amount if item.amount else 0, contest_center)
					worksheet4.write(kk, 6, item.reused_amount if item.reused_amount else 0, contest_center)
					# worksheet4.write(kk, 7, item.reused_percent if item.reused_percent else 0, contest_center)
					worksheet4.write(kk, 8, item.note if item.note else ' ', contest_center)
					worksheet4.write(kk, 9, item.create_uid.name if item.create_uid else ' ', contest_center)
					kk += 1
					number += 1

			worksheet5 = workbook.add_worksheet(u'Газар хөндөлт')
			worksheet5.set_zoom(100)
			row = 0
			worksheet5.merge_range(row,0, row,11, u'Газар хөндөлт', contest_center)
			
			# TABLE HEADER
			row = 1
			worksheet5.set_row(0, 28)	
			worksheet5.write(row, 0, u'№', header)
			worksheet5.write(row, 1, u'Үйлдвэр, уурхай', header)
			worksheet5.write(row, 2, u'Он', header)
			worksheet5.write(row, 3, u'Сар', header)
			worksheet5.write(row, 4, u'Нийт хөндсөн талбай /га/ ', header)
			worksheet5.write(row, 5, u'Хөндсөн талбайн зориулалт', header)
			worksheet5.write(row, 6, u'Тайлбар', header)
			worksheet5.write(row, 7, u'Бүртгэсэн', header)

			kk = 2
			number = 1
			worksheet5.set_column('A:A', 5)
			worksheet5.set_column('B:B', 30)
			worksheet5.set_column('C:C', 30)
			worksheet5.set_column('D:D', 30)
			worksheet5.set_column('E:E', 30)
			worksheet5.set_column('F:F', 30)
			worksheet5.set_column('G:G', 30)
			worksheet5.set_column('H:H', 30)

			# DATA зурах
			if rehab_lines:
				for item in rehab_lines:
					worksheet5.write(kk, 0, number, contest_center)
					worksheet5.write(kk, 1, item.rehab_id.mining_location.name if item.rehab_id.mining_location else ' ', contest_center)
					worksheet5.write(kk, 2, item.used_date.strftime('%Y') if item.used_date else ' ', contest_center)
					worksheet5.write(kk, 3, item.used_date.strftime('%m') if item.used_date else ' ', contest_center)
					worksheet5.write(kk, 4, item.amount if item.amount else 0, contest_center)
					worksheet5.write(kk, 5, item.dedication if item.dedication else ' ', contest_center)
					worksheet5.write(kk, 6, item.note if item.note else ' ', contest_center)
					worksheet5.write(kk, 7, item.create_uid.name if item.create_uid else ' ', contest_center)
					kk += 1
					number += 1
		
			worksheet6 = workbook.add_worksheet(u'Нөхөн сэргээлт')
			worksheet6.set_zoom(100)
			row = 0
			worksheet6.merge_range(row,0, row,11, u'Нөхөн сэргээлтийн тайлан', contest_center)
			
			# TABLE HEADER
			row = 1
			worksheet6.set_row(0, 28)	
			worksheet6.write(row, 0, u'№', header)
			worksheet6.write(row, 1, u'Үйлдвэр, уурхай', header)
			worksheet6.write(row, 2, u'Он', header)
			worksheet6.write(row, 3, u'Сар', header)
			worksheet6.write(row, 4, u'Нийт нөхөн сэргээсэн талбай /га/', header)
			worksheet6.write(row, 5, u'Нөхөн сэргээлтийн ангилал', header)
			worksheet6.write(row, 6, u'Нөхөн сэргээлтийн төрөл', header)
			worksheet6.write(row, 7, u'Тайлбар', header)
			worksheet6.write(row, 8, u'Бүртгэсэн', header)

			kk = 2
			number = 1
			worksheet6.set_column('A:A', 5)
			worksheet6.set_column('B:B', 30)
			worksheet6.set_column('C:C', 30)
			worksheet6.set_column('D:D', 30)
			worksheet6.set_column('E:E', 30)
			worksheet6.set_column('F:F', 30)
			worksheet6.set_column('G:G', 30)
			worksheet6.set_column('H:H', 30)
			worksheet6.set_column('I:I', 30)

			# DATA зурах
			if rehab_lands:
				for item in rehab_lands:
					worksheet6.write(kk, 0, number, contest_center)
					worksheet6.write(kk, 1, item.rehab_id.mining_location.name if item.rehab_id.mining_location else ' ', contest_center)
					worksheet6.write(kk, 2, item.date.strftime('%Y') if item.date else ' ', contest_center)
					worksheet6.write(kk, 3, item.date.strftime('%m') if item.date else ' ', contest_center)
					worksheet6.write(kk, 4, item.amount if item.amount else 0, contest_center)
					worksheet6.write(kk, 5, dict(item._fields['rehab_category'].selection).get(item.rehab_category) if item.rehab_category else ' ', contest_center)
					worksheet6.write(kk, 6, item.rehab_type if item.rehab_type else ' ', contest_center)
					worksheet6.write(kk, 7, item.note if item.note else ' ', contest_center)
					worksheet6.write(kk, 8, item.create_uid.name if item.create_uid else ' ', contest_center)
					kk += 1
					number += 1


			worksheet6 = workbook.add_worksheet(u'Амьтны үзэгдэл')
			worksheet6.set_zoom(100)
			row = 0
			worksheet6.merge_range(row,0,row,10, u'Амьтны үзэгдэл тайлан', contest_center)
			
			# TABLE HEADER
			row = 1
			worksheet6.set_row(0, 28)	
			worksheet6.write(row, 0, u'№', header)
			worksheet6.write(row, 1, u'Үйлдвэр, уурхай', header)
			worksheet6.write(row, 2, u'Он', header)
			worksheet6.write(row, 3, u'Сар', header)
			worksheet6.write(row, 4, u'Өдөр', header)
			worksheet6.write(row, 5, u'Цаг', header)
			worksheet6.write(row, 6, u'Харагдсан зүйл ', header)
			worksheet6.write(row, 7, u'Харагдсан тоо', header)
			worksheet6.write(row, 8, u'Хамаарах ангилал', header)
			worksheet6.write(row, 9, u'Хүйс', header)
			worksheet6.write(row, 10, u'Бүртгэсэн', header)
	
			kk = 2
			number = 1
			worksheet6.set_column('A:A', 5)
			worksheet6.set_column('B:B', 30)
			worksheet6.set_column('C:C', 30)
			worksheet6.set_column('D:D', 30)
			worksheet6.set_column('E:E', 30)
			worksheet6.set_column('F:F', 30)
			worksheet6.set_column('G:G', 30)
			worksheet6.set_column('H:H', 30)
			worksheet6.set_column('I:I', 30)
			worksheet6.set_column('J:J', 30)
			worksheet6.set_column('K:K', 30)
			worksheet6.set_column('L:L', 30)
			
			# DATA зурах
			if animals:
				for item in animals:
					worksheet6.write(kk, 0, number, contest_center)
					worksheet6.write(kk, 1, item.mining_location.name if item.mining_location else ' ', contest_center)
					worksheet6.write(kk, 2, item.date.strftime('%Y') if item.date else ' ', contest_center)
					worksheet6.write(kk, 3, item.date.strftime('%m') if item.date else ' ', contest_center)
					worksheet6.write(kk, 4, item.date.strftime('%d') if item.date else ' ', contest_center)
					worksheet6.write(kk, 5, item.date.strftime('%H:%M') if item.date else ' ', contest_center)
					worksheet6.write(kk, 6, item.animal.name if item.animal else ' ', contest_center)
					worksheet6.write(kk, 7, item.number if item.number else 0, contest_center)
					worksheet6.write(kk, 8, dict(item.animal._fields['category'].selection).get(item.animal.category) if item.animal else ' ', contest_center)
					worksheet6.write(kk, 9, dict(item._fields['gender'].selection).get(item.gender) if item.gender else ' ', contest_center)
					worksheet6.write(kk, 10, item.create_uid.name if item.create_uid else ' ', contest_center)
					kk += 1
					number += 1

			worksheet7 = workbook.add_worksheet(u'Зардал')
			worksheet7.set_zoom(100)
			row = 0
			worksheet7.merge_range(row,0, row,9, u'Зардал тайлан', contest_center)
			
			# TABLE HEADER
			row = 1
		
			worksheet7.set_row(0, 28)	
			worksheet7.write(row, 0, u'№', header)
			worksheet7.write(row, 1, u'Үйлдвэр, уурхай', header)
			worksheet7.write(row, 2, u'Зардлын төрөл', header)
			worksheet7.write(row, 3, u'Зарлын ангилал', header)
			worksheet7.write(row, 4, u'Он', header)
			worksheet7.write(row, 5, u'Сар', header)
			worksheet7.write(row, 6, u'Өдөр', header)
			worksheet7.write(row, 7, u'Мөнгөн дүн/төгрөг/', header)
			worksheet7.write(row, 8, u'Тайлбар', header)
			worksheet7.write(row, 9, u'Бүртгэсэн', header)

			kk = 2
			number = 1
			worksheet7.set_column('A:A', 5)
			worksheet7.set_column('B:B', 30)
			worksheet7.set_column('C:C', 30)
			worksheet7.set_column('D:D', 30)
			worksheet7.set_column('E:E', 30)
			worksheet7.set_column('F:F', 30)
			worksheet7.set_column('G:G', 30)
			worksheet7.set_column('H:H', 30)
			worksheet7.set_column('I:I', 30)
			worksheet7.set_column('J:J', 30)
			# DATA зурах
			if expenses:
				for item in expenses:
					worksheet7.write(kk, 0, number, contest_center)
					worksheet7.write(kk, 1, item.mining_location.name if item.mining_location else ' ', contest_center)
					worksheet7.write(kk, 2, item.expense_type.name if item.expense_type else ' ', contest_center)
					worksheet7.write(kk, 3, dict(item.expense_type._fields['category'].selection).get(item.expense_type.category) if item.expense_type else ' ', contest_center)
					worksheet7.write(kk, 4, item.expense_date.strftime('%Y') if item.expense_date else ' ', contest_center)
					worksheet7.write(kk, 5, item.expense_date.strftime('%m') if item.expense_date else ' ', contest_center)
					worksheet7.write(kk, 6, item.expense_date.strftime('%d') if item.expense_date else ' ', contest_center)
					worksheet7.write(kk, 7, item.amount if item.amount else 0, contest_center)
					worksheet7.write(kk, 8, item.note if item.note else ' ', contest_center)
					worksheet7.write(kk, 9, item.create_uid.name if item.create_uid else ' ', contest_center)
					kk += 1
					number += 1

			worksheet8 = workbook.add_worksheet(u'Ногоон байгууламж, Арчилгаа')
			worksheet8.set_zoom(100)
			row = 0
			worksheet8.merge_range(row,0, row,10, u'Ногоон байгууламж, Арчилгаа тайлан', contest_center)
			
			# TABLE HEADER
			row = 1
		
			worksheet8.set_row(0, 28)	
			worksheet8.write(row, 0, u'№', header)
			worksheet8.write(row, 1, u'Үйлдвэр, уурхай', header)
			worksheet8.write(row, 2, u'Он ', header)
			worksheet8.write(row, 3, u'Сар', header)
			worksheet8.write(row, 4, u'Өдөр', header)
			worksheet8.write(row, 5, u'Үйл ажиллагаа', header)
			worksheet8.write(row, 6, u'Байршил', header)
			worksheet8.write(row, 7, u'Тоо хэмжээ', header)
			worksheet8.write(row, 8, u'Хэмжих нэгж', header)
			worksheet8.write(row, 9, u'Тайлбар', header)
			worksheet8.write(row, 10, u'Бүртгэсэн ', header)

			kk = 2
			number = 1
			worksheet8.set_column('A:A', 5)
			worksheet8.set_column('B:B', 30)
			worksheet8.set_column('C:C', 30)
			worksheet8.set_column('D:D', 30)
			worksheet8.set_column('E:E', 30)
			worksheet8.set_column('F:F', 30)
			worksheet8.set_column('G:G', 30)
			worksheet8.set_column('H:H', 30)
			worksheet8.set_column('I:I', 30)
			worksheet8.set_column('J:J', 30)
			worksheet8.set_column('K:K', 30)
			
			# DATA зурах
			if gardens:
				for item in gardens:
					worksheet8.write(kk, 0, number, contest_center)
					worksheet8.write(kk, 1, item.garden_id.mining_location.name if item.garden_id.mining_location else ' ', contest_center)
					worksheet8.write(kk, 2, item.date.strftime('%Y') if item.date else ' ', contest_center)
					worksheet8.write(kk, 3, item.date.strftime('%m') if item.date else ' ', contest_center)
					worksheet8.write(kk, 4, item.date.strftime('%d') if item.date else ' ', contest_center)
					worksheet8.write(kk, 5, item.garden_activity.name if item.garden_activity else ' ', contest_center)
					worksheet8.write(kk, 6, item.garden_location if item.garden_location else ' ', contest_center)
					worksheet8.write(kk, 7, item.amount if item.amount else 0, contest_center)
					worksheet7.write(kk, 8, dict(item.garden_activity._fields['category'].selection).get(item.garden_activity.category) if item.garden_activity else ' ', contest_center)
					worksheet8.write(kk, 9, item.note if item.note else ' ', contest_center)
					worksheet8.write(kk, 10, item.create_uid.name if item.create_uid else ' ', contest_center)
					kk += 1
					number += 1

			worksheet9 = workbook.add_worksheet(u'Мод бут тооллого')
			worksheet9.set_zoom(100)
			row = 0
			worksheet9.merge_range(row,0, row,9, u'Мод бут тооллого тайлан', contest_center)
			
			# TABLE HEADER
			row = 1
		
			worksheet9.set_row(0, 28)	
			worksheet9.write(row, 0, u'№', header)
			worksheet9.write(row, 1, u'Үйлдвэр, уурхай', header)
			worksheet9.write(row, 2, u'Он ', header)
			worksheet9.write(row, 3, u'Улирал', header)
			worksheet9.write(row, 4, u'Мод бутны нэр', header)
			worksheet9.write(row, 5, u'Хуучин байсан мод', header)
			worksheet9.write(row, 6, u'Шинээр тарьсан мод', header)
			worksheet9.write(row, 7, u'Тарилтын мэдээлэл', header)
			worksheet9.write(row, 8, u'Нийт тоо', header)
			worksheet9.write(row, 9, u'Бүртгэсэн ', header)

			kk = 2
			number = 1
			worksheet9.set_column('A:A', 5)
			worksheet9.set_column('B:B', 30)
			worksheet9.set_column('C:C', 30)
			worksheet9.set_column('D:D', 30)
			worksheet9.set_column('E:E', 30)
			worksheet9.set_column('F:F', 30)
			worksheet9.set_column('G:G', 30)
			worksheet9.set_column('H:H', 30)
			worksheet9.set_column('I:I', 30)
			worksheet9.set_column('J:J', 30)
			# DATA зурах
			if trees:
				for item in trees:
					worksheet9.write(kk, 0, number, contest_center)
					worksheet9.write(kk, 1, item.tree_id.mining_location.name if item.tree_id.mining_location else ' ', contest_center)
					worksheet9.write(kk, 2, item.date.strftime('%Y') if item.date else ' ', contest_center)
					worksheet9.write(kk, 3, dict(item._fields['season'].selection).get(item.season) if item.season else ' ', contest_center)
					worksheet9.write(kk, 4, item.tree.name if item.tree else ' ', contest_center)
					worksheet9.write(kk, 5, item.number if item.number else 0, contest_center)
					worksheet9.write(kk, 6, item.new_number if item.new_number else 0, contest_center)
					# worksheet9.write(kk, 7, item.amount if item.amount else 0, contest_center)
					worksheet9.write(kk, 8, item.total_number if item.total_number else 0, contest_center)
					worksheet9.write(kk, 9, item.create_uid.name if item.create_uid else ' ', contest_center)
					kk += 1
					number += 1
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

			return {
				'type': 'ir.actions.act_url',
				'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
				'target': 'new',
			}
		else:
			raise UserError(u'Бичлэг олдсонгүй!')