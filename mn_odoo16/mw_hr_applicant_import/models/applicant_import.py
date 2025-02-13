
# -*- coding: utf-8 -*-
from tempfile import NamedTemporaryFile

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import osv
import odoo.netsvc, os
import xlrd
import base64

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class ApplicantImport(models.Model):
	_name = "applicant.import"
	_description = 'Applicant Import'
	_inherit = ['mail.thread']

	name = fields.Char('Нэр')
	# open_job_id = fields.Many2one('hr.open.job',string='Нээлттэй ажлын байр')
	source_id = fields.Many2one('utm.source', string='Эх үүсвэр')
	job_id = fields.Many2one('hr.job', string='Албан тушаал')
	date = fields.Date('Огноо')
	data = fields.Binary('Exsel file')
	file_fname = fields.Char(string='File name')

	@api.onchange('data')
	@api.depends('data','file_fname')
	def check_file_type(self):
		if self.data:
			filename,filetype = os.path.splitext(self.file_fname)

	def action_create_applicant(self):
		applicant_pool = self.env['hr.applicant']
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
			last_name = row[1].value
			name = row[2].value
			register = row[3].value
			sex = row[4].value
			partner_mobile = row[5].value
			partner_phone = row[6].value
			email = row[7].value
			license = row[8].value
			salary_expected = row[9].value
			date = row[10].value

			applicant_ids = self.env['hr.applicant'].search([('register','=',register)],limit=1)
			if not applicant_ids:
				applicant_id = applicant_pool.create({
					'last_name':last_name,
					'name': name,
					'partner_name': name,
					'partner_mobile':partner_mobile,
					'register':register,
					'sex':sex,
					'partner_phone':partner_phone,
					'email_from':email,
					'license_type':license,
					'salary_expected':salary_expected,
					'source_id': self.source_id.id,
					'job_id' : self.job_id.id,
					'date':date
					})
			else:
				raise UserError(_('%s регистрийн дугаартай горилогч системд бүртгэлтэй байна.')%(register))