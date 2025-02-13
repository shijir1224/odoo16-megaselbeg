# -*- coding: utf-8 -*-
from odoo import  fields, models, _
import datetime
from datetime import   datetime, timedelta
from io import BytesIO
import xlsxwriter
import base64
try:
	# Python 2 support
	from base64 import encodestring
except ImportError:
	# Python 3.9.0+ support
	from base64 import encodebytes as encodestring



DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class EmployeeShiftChange(models.Model):
	_name = 'employee.shift.change'
	_description = 'Employee shift change'

	parent_id = fields.Many2one('change.shift',string='parent')
	employee_id = fields.Many2one('hr.employee',string='Ажилтан')
	identification_id = fields.Char('Код', related='employee_id.identification_id')
	job_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Албан тушаал')
	alcohol = fields.Char(string='Согтууруулах ундааны хэмжилт',default=0)
	hab = fields.Boolean(string='ХАБ зааварчилгаа өгсөн эсэх',default=True)
	description = fields.Char(string='Тайлбар')

class ChangeShift(models.Model):
	_name = 'change.shift'
	_description = 'Change Shift'
	_inherit = ['mail.thread']

	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	name = fields.Char(string='Нэр')
	date = fields.Datetime(string='Өдөр цаг')
	employee_id = fields.Many2one('hr.employee',string='Бүртгэсэн ажилтан',default=_default_employee )
	project_id = fields.Many2one('hr.project',string='Төсөл')

	
	state = fields.Selection([('draft','Ноорог'), ('send','Илгээсэн'),('done','Дууссан')], default='draft', string='Төлөв')
	shift = fields.Selection([('office', 'Оффис'), ('d', '1-р ээлж'), ('e', '2-р ээлж'), ('f', '3-р ээлж'), ('g', '4-р ээлж'), ('k', '5-р ээлж'),('l', '6-р ээлж'), ('m', '7-р ээлж'), ('n', '8-р ээлж'), ('o', '9-р ээлж'), ('r', '10-р ээлж'), ('w', '11-р ээлж')], default='office', string='Ээлж')
	employee_ids = fields.One2many('employee.shift.change','parent_id',string='Ажилчид')
	shift_g = fields.Selection([('a', 'A'), ('b', 'B'), ('c', 'C')],  string='Бүлэг')
	place = fields.Char(string='Байршил')

	def create_line(self):
		line_data_pool = self.env['employee.shift.change']
		if self.employee_ids:
			self.employee_ids.unlink()
		query = """SELECT 
			hr.id as emp_id,
			hr.shift_g as shift_g,
			hj.name as job_id,
			hr.identification_id as identification_id
			FROM hr_employee hr	
			LEFT JOIN hr_work_location wl On wl.id=hr.work_location_id		
			LEFT JOIN hr_job hj On hj.id=hr.job_id
			WHERE employee_type in ('employee','trainee','contractor') and shift_g='%s'"""%(self.shift_g)
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		for obj in records:
			if self.shift_g:
				line_line_conf = line_data_pool.create({
					'employee_id': obj['emp_id'],
					'parent_id': self.id
				})

	def action_done(self):
		self.write({'state':'done'})
		self.action_send_email()

	def action_send(self):
		self.write({'state':'send'})

	def action_draft(self):
		self.write({'state':'draft'})

	def action_send_email(self):
		date = self.date + timedelta(hours=8)
		shift = dict(self._fields['shift'].selection).get(self.shift)
		html = u'<b>Танд энэ өдрийн мэнд хүргэе!</b><br/>'
		html += u"""<b><a target="_blank"></a></b>%sний ажилчид та бүхэн "%s" цагт %s -д бэлэн байна уу"""% (shift, date, self.place)
		for item in self:
			for line in item.employee_ids:
				if line.employee_id:
					self.env.user.send_chat(html, line.employee_id.user_partner_id,
											with_mail=True, subject_mail='Ээлж солих тухай')
					

	def action_print(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'Ээлж солих ажилтнуудын мэдээлэл'

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
		sheet = workbook.add_worksheet(u'Ээлж солих ажилтнуудын мэдээлэл')
		sheet2 = workbook.add_worksheet(u'ХАБ-ын зааварчилгаа')
		
		sheet2.merge_range(1, 1, 1, 6, u'"Соёолон интернэшнл" ХХК-ийн ажилтнууд"', h1)
		sheet2.merge_range(2, 1, 2, 6, u'төсөл рүү явах аяллын үед мөрдөх журамтай танилцсан бүртгэл', h1)
		

		sheet2.merge_range(5, 0, 5, 6, u'1.Тухайн маршрутын аялал гарахаар төлөвлөсөн цагийг чанд баримтална.', content_left_h)
		sheet2.merge_range(6, 0, 6, 6, u'2. Тухайн маршрутын аялал гарахаар төлөвлөсөн цэгт заавал ирж бүртгэл хийлгэнэ.', content_left_h)
		sheet2.merge_range(7, 0, 7, 6, u'3. Төслийн талбай руу зорчих үед өөрийн хувийн бэлтгэлийг хангасан байна.', content_left_h)
		sheet2.merge_range(8, 0, 9, 6, u'4. Төслийн талбай руу зорчих үед архи согтууруулах ундааны зүйл хэрэглэсэн эсэхийг согтуурал тандагчаар шалгах ба 0,00 заагаагүй тохиолдолд албан тушаал үл харгалзан төслийн талбай руу зорчихыг хориглоно.', content_left_h)
		sheet2.merge_range(10, 0, 10, 6, u'5. Төслийн талбай руу архи согтууруулах ундаа тээвэрлэхийг хатуу хориглоно.', content_left_h)
		sheet2.merge_range(11, 0, 11, 6, u'6. Замаас хүн суулгахыг хориглоно. ', content_left_h)
		sheet2.merge_range(12, 0, 12, 6, u'7. Тээврийн хэрэгсэлд буух болон суух үед бие биедээ саад болохгүй байхаар дарааллын дагуу бууж, сууна.', content_left_h)
		sheet2.merge_range(13, 0, 13, 6, u'8. Тээврийн хэрэгслээр зорчих үед суудлын даруулгыг заавал хэрэглэнэ.', content_left_h)
		sheet2.merge_range(14, 0, 15, 6, u'9. Тээврийн хэрэгсэлд хог хаях, тамхи татах, чангаар ярих, жолоочийн анхаарал сарниулах үг үйлдэл гаргах, жолооч болон бусад зорчигчидтой зүй бусаар харьцахыг хориглоно.', content_left_h)
		sheet2.merge_range(16, 0, 16, 6, u'10. Аяллыг ахалж байгаа албан тушаалтны зүй ёсны шаардлагыг дагаж мөрдөнө.', content_left_h)
		sheet2.merge_range(17, 0, 17, 6, u'11. Аяллаас ирэх үед батлагдсан маршрутын дагуу ажилчдыг буулгана. ', content_left_h)
		sheet2.merge_range(18, 0, 19, 6, u'12. Аяллын өмнө замд хэрэглэх хүнс, ахуйн хэрэглээг сайтар бэлдэх ба батлагдсан маршрутаас бусад суурин газар зогсохыг хориглоно.', content_left_h)

		sheet.merge_range(1, 3, 1, 10, u'Ээлж солих ажилтнуудын мэдээлэл УБ-САЛХИТ', content_left_h)
		tt_date = datetime.strptime(str(self.date), DATETIME_FORMAT) + timedelta(hours=8)
		sheet.merge_range(3, 3, 3, 10, u'Амьсгал дахь спиртийн агууламж тогтоох сорил                     ''     ''         ''%s'%(tt_date.date()), h1)
		sheet2.merge_range(3, 4, 3, 6,'%s'%(tt_date.date()), h1)

		rowx=5
		sheet.set_column('A:A', 4)
		sheet.set_column('B:B', 7)
		sheet.set_column('C:E', 15)
		sheet.set_column('F:J', 10)
		sheet.set_column('K:K', 20)

		sheet2.set_column('A:A', 4)
		sheet2.set_column('B:B', 7)
		sheet2.set_column('C:F', 15)
		sheet2.set_column('G:G', 20)

		sheet.merge_range(rowx, 0,rowx+2,0, u'Д/д', theader),
		sheet.merge_range(rowx,1,rowx+2,1, u'Код', theader),
		sheet.merge_range(rowx,2,rowx+2,2, u'Овог', theader),
		sheet.merge_range(rowx,3,rowx+2,3, u'Нэр', theader),
		sheet.merge_range(rowx,4,rowx+2,4, u'Албан тушаал', theader),
		sheet.merge_range(rowx,5,rowx+2,5, u'Утасны дугаар', theader),
		sheet.merge_range(rowx,6,rowx+1,7, u'Анхан шалгалт', theader),
		sheet.write(rowx+2,6,u'Цаг', theader),
		sheet.write(rowx+2,7,u'Үр дүн %', theader),
		sheet.merge_range(rowx,8,rowx+1,9, u'Дахин шалгалт', theader),
		sheet.write(rowx+2,8, u'Цаг', theader),
		sheet.write(rowx+2,9, u'Үр дүн %', theader),
		sheet.merge_range(rowx,10,rowx+2,10, u'Гарын үсэг', theader),
		rowx2=21
		sheet2.merge_range(rowx2, 0,rowx2+2,0, u'Д/д', theader),
		sheet2.merge_range(rowx2,1,rowx2+2,1, u'Код', theader),
		sheet2.merge_range(rowx2,2,rowx2+2,2, u'Овог', theader),
		sheet2.merge_range(rowx2,3,rowx2+2,3, u'Нэр', theader),
		sheet2.merge_range(rowx2,4,rowx2+2,4, u'Албан тушаал', theader),
		sheet2.merge_range(rowx2,5,rowx2+2,5, u'Утасны дугаар', theader),
		sheet2.merge_range(rowx2,6,rowx2+2,6, u'Зааварчилгаа авсан Гарын үсэг', theader),

		n=1
		rowx=8
		rowx2=24
		for data in self.employee_ids:
			sheet.write(rowx, 0, n,center_att)
			sheet.write(rowx, 1, data.employee_id.identification_id,content_left)
			sheet.write(rowx, 2,data.employee_id.last_name,content_left)
			sheet.write(rowx, 3,data.employee_id.name,content_left)
			sheet.write(rowx, 4,data.employee_id.job_id.name,content_left)
			sheet.write(rowx, 5,data.employee_id.mobile_phone,content_left)
			sheet.write(rowx, 6,'',content_left)
			sheet.write(rowx, 7,'',content_left)
			sheet.write(rowx, 8,'',content_left)
			sheet.write(rowx, 9,'',content_left)
			sheet.write(rowx, 10,'',content_left)
			sheet2.write(rowx2, 0, n,center_att)
			sheet2.write(rowx2, 1, data.employee_id.identification_id,content_left)
			sheet2.write(rowx2, 2,data.employee_id.last_name,content_left)
			sheet2.write(rowx2, 3,data.employee_id.name,content_left)
			sheet2.write(rowx2, 4,data.employee_id.job_id.name,content_left)
			sheet2.write(rowx2, 5,data.employee_id.mobile_phone,content_left)
			sheet2.write(rowx2, 6,'',content_left)

			rowx2+=1
			rowx+=1
			n+=1

		sheet2.merge_range(rowx2+6,0,rowx2+6,6,'Зааварчилгаа өгсөн:' + '.....................................................' ' %s '		   ' %s' '.' '%s' %(self.employee_id.job_id.name,self.employee_id.last_name[:1],self.employee_id.name), content_left_h),

	

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