from odoo.exceptions import UserError
from odoo import fields, models, _
from tempfile import NamedTemporaryFile
import base64
from odoo.osv import osv
import xlrd
import  os

class TrainingRegistration(models.Model):
	_inherit = "training.registration"

	file = fields.Binary('Файл')
			
	def action_import(self):
		data_pool =  self.env['training.registration.line']
		if self.line_ids:
			self.line_ids.unlink()
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.file))
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
			default_code = row[6].value
			employee_id = self.env['hr.employee'].search([('passport_id','=',default_code)],limit=1)
			if employee_id:
				tr_data_id = data_pool.create({
					't_employee_id':employee_id.id,
					'department_id':employee_id.department_id.id,
					'job_id':employee_id.job_id.id,
					'passport':employee_id.passport_id,
					'parent_id': self.id,
					})
			else:
				raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))
		print('aaaaaaaaaa', self.action_import)