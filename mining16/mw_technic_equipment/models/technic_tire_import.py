# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections

import xlrd, os
from tempfile import NamedTemporaryFile
import base64
import xlsxwriter
from io import BytesIO

class technicInspection(models.Model):
	_inherit = 'tire.inspection'

	import_id = fields.Many2one('technic.tire.import', string=u'Import ID')

class technicTireInstall(models.Model):
	_inherit = 'technic.tire.install'

	import_id = fields.Many2one('technic.tire.import', string='Import ID')

class technicTireImport(models.Model):
	_name = 'technic.tire.import'
	_description = 'Technic tire Import'

	@api.model
	def _default_name(self):
		return self.env['ir.sequence'].next_by_code('technic.tire.import')

	name = fields.Char(string=u'Импортын дугаар', readonly=True, default=_default_name)
	date = fields.Date(string=u'Огноо', default=fields.Date.context_today, required=True)
	branch_id = fields.Many2one('res.branch', string=u'Салбар', default=lambda self: self.env.user.branch_id, required=True)
	company_id = fields.Many2one('res.company', string=u'Компани', default=lambda self: self.env.user.company_id, required=True)
	partner_id = fields.Many2one('res.partner', string=u'Бүртгэсэн ажилтан', default=lambda self: self.env.user.partner_id, required=True)
	received_partner_id = fields.Many2one('res.partner', string=u'Хянасан ажилтан')
	attachment_id = fields.Binary(string=u'Импорт файл')

	install_ids = fields.One2many('technic.tire.install', 'import_id',string=u'Угсрах салгах бүртгэл')
	inspection_ids = fields.One2many('tire.inspection', 'import_id', string=u'Дугуйн үзлэг')

	state = fields.Selection([('draft','Draft'),('done','Done')], string=u'Төлөв', default='draft')
	
	# Overrided methods
	@api.model
	def create(self, vals):
		res = super(technicTireImport, self).create(vals)
		return res
		
	def write(self, vals):
		res = super(technicTireImport, self).write(vals)
		return res
		
	# Custom methods

	def export_template(self):
		return False

	def import_action(self):
		self.ensure_one()
		import_data = False
		if self.attachment_id:
			tire_obj = self.evn['technic.tire']
			tire_used_history_obj = self.evn['tire.used.history']
			tire_setting_obj = self.evn['technic.tire.setting']
			tire_inspection_obj = self.evn['tire.inspection']
			tire_inspection_line_obj = self.evn['tire.inspection.line']
			tire_install_obj = self.evn['technic.tire.install']
			tire_install_line_obj = self.evn['technic.tire.install.line']
			tire_remove_line_obj = self.evn['technic.tire.remove.line']
			technic_obj = self.evn['technic.equipment']
			technic_setting_obj = self.evn['technic.equipment.setting']
			workorder_obj = self.evn['maintenance.workorder']

			import_data = self.attachment_id.datas
			fileobj = NamedTemporaryFile('w+b')
			fileobj.write(base64.decodestring(import_data))
			fileobj.seek(0)
			if not os.path.isfile(fileobj.name):
				raise UserError(u'Алдаа Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
			book = xlrd.open_workbook(fileobj.name)
			sheet = book.sheet_by_index('Tire')
			sheet1 = book.sheet_by_index('Inspection')
			sheet2 = book.sheet_by_index('Install & Remove')

			nrows = sheet.nrows
			rowi = 3
			for item in range(rowi,nrows):
				row = sheet.row(item)
		else:
			raise UserWarning(("Импортлох файлаа оруулан уу!"))
		
