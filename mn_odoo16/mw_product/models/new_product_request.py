# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from sqlite3 import apilevel
from odoo import fields, models, _, api
from datetime import datetime
from odoo.exceptions import UserError,Warning
from io import BytesIO
import base64
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd
import logging
import re
_logger = logging.getLogger(__name__)

class NewProductRequest(models.Model):
	_name = 'new.product.request'
	_description = 'new.product.request'
	
	_order = 'date_sent, date_done'
	_inherit = ['mail.thread']

	
	def _get_user(self):
		return self.env.user.id

	def get_create_product_users(self):
		res_model = self.env['ir.model.data'].search([('module','=','mw_product'),('name','=','group_stock_product_creating')])
		group = self.env['res.groups'].search([('id','=',res_model.res_id)])
		print('group.users.ids: ', group.users.ids)
		return [('id', 'in', group.users.ids)]

	name = fields.Char(u'Нэр', readonly=True, )
	description = fields.Text(u'Дэлгэрэнгүй тайлбар', required=True,
		states={'sent': [('readonly', True)],'created': [('readonly', True)],
				'done': [('readonly', True)],'cancelled': [('readonly', True)]})
	date = fields.Datetime(u'Үүсгэсэн огноо', default=fields.Datetime.now(), readonly=True)
	date_sent = fields.Datetime(u'Илгээсэн огноо', readonly=True)
	date_done = fields.Datetime(u'Бараа бүртгэсэн огноо', readonly=True)
	user_id = fields.Many2one('res.users', u'Хүсэлт гаргасан', default=_get_user, readonly=True)
	to_user_ids = fields.Many2many('res.users', string='Бараа үүсгэгч', domain=get_create_product_users, required=True, 
		states={'sent': [('readonly', True)],'created': [('readonly', True)],
				'done': [('readonly', True)],'cancelled': [('readonly', True)]})
	create_user_id = fields.Many2one('res.users', u'Бараа үүсгэсэн', readonly=True)
	line_ids = fields.One2many('new.product.request.line', 'parent_id', string='Шинэ бараанууд')
	new_product_id = fields.Many2one('product.product', u'Шинэ бараа', 
		states={'sent': [('readonly', True)],
				'done': [('readonly', True)],'cancelled': [('readonly', True)]})
	done_description = fields.Text(u'Гүйцэтгэсэн тайлбар', 
		states={'draft': [('readonly', True)],'done': [('readonly', True)],'cancelled': [('readonly', True)]})
	state = fields.Selection([
			('draft', u'Ноорог'), 
			('sent', u'Илгээсэн'),
			('created', u'Барааг үүсгэсэн'),
			('done', u'Дууссан'),
			('cancelled', u'Цуцлагдсан'),], 
			default='draft', string=u'Төлөв', tracking=True)
	import_data_id = fields.Many2many('ir.attachment', copy=False)
	import_data = fields.Binary('Импортлох эксел', copy=False)

	# Эдийн дугаар шалгах 
	def chech_eq_number(self):
		for line in self.line_ids:
			product_ids = self.env['product.template'].search([(str('default_code').casefold(),'=',str(line.part_number).casefold())])
			if product_ids:
				raise UserError('Эдийн дугаар үүссэн байна!\n\n%s' %('\n'.join(product_ids.mapped('display_name'))))

	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй бичлэгийг устгаж болно!'))
		return super(NewProductRequest, self).unlink()

	# ----------- CUSTOM METHODs -----------------
	
	def action_notification_send(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_product.action_new_product_request').id
		html = u'<b>Шинэ барааны хүсэлт</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=new.product.request&action=%s>%s</a></b> - дугаартай шинэ барааны хүсэлтийг шалгана уу!"""% (base_url, self.id, action_id, self.name)
		for receiver in self.to_user_ids:
			if receiver:
				subject_mail = "Шинэ барааны хүсэлт ирлээ"
				self.env['res.users'].send_emails(body=html, partners=[receiver.partner_id], subject=subject_mail, attachment_ids=False)
				self.env.user.send_chat(partner_ids=[receiver.partner_id], subject_mail=subject_mail, html=html, with_mail=False)

	def action_notification_done(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_product.action_new_product_request').id
		html = u'<b>Шинэ бараа үүсгэгдсэн</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#action=%s&id=%s&view_type=form&model=new.product.request>%s</a></b> - дугаартай шинэ барааны хүсэлтийг шалгана уу! \n Шинэ барааны код: %s та шалгана уу!"""% (base_url, action_id, self.id, self.name, ', '.join(self.line_ids.mapped('product_id.display_name')))
		for receiver in self.user_id:
			if receiver:
				subject_mail = "Шинэ барааны хүсэлт батлагдлаа"
				self.env['res.users'].send_emails(body=html, partners=[receiver.partner_id], subject=subject_mail, attachment_ids=False)
				self.env.user.send_chat(partner_ids=[receiver.partner_id], subject_mail=subject_mail, html=html, with_mail=False)

	def action_to_draft(self):
		self.state = 'draft'

	def action_to_send(self):
		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code('new.product.request')

		if not self.line_ids and not self.import_data_id:
			raise UserError(('Бараагаа оруулна уу!'))
		self.state = 'sent'
		self.date_sent = datetime.now()
		self.user_id = self.env.user.id
		# Chat илгээх
		self.action_notification_send()

	def action_to_created(self):
		self.state = 'created'
		self.date_done = datetime.now()
		self.create_user_id = self.env.user.id

	def action_to_done(self):
		# if self.line_ids.filtered(lambda r: r.product_id == False):
		# 	raise Warning(('Үүссэн бараагаа сонгон уу!'))
		for line in self.line_ids:
			if not line.product_id:
				raise UserError(('Үүссэн бараагаа сонгон уу! %s - %s' % (line.name, line.part_number)))
		self.state = 'done'
		self.date_done = datetime.now()
		self.create_user_id = self.env.user.id
		# Chat илгээх
		self.action_notification_done()

	def action_to_cancel(self):
		self.state = 'cancelled'
		self.date_done = datetime.now()
		self.create_user_id = self.env.user.id

	def set_old(self):
		request_line = self.env['new.product.request.line']
		request_ids = self.env['new.product.request'].sudo().search([('new_product_id','!=',False),('part_number','!=',False)])
		for request in request_ids:
			vals = {
				"parent_id": request.id,
				"product_id": request.new_product_id.id,
				"part_number": request.part_number,
				"name": request.new_product_id.name,
				"converted_part_number": request.converted_part_number,
			}
			request_line.sudo().create(vals)

	#ERDENEMUNKH - IMPORT PRODUCT USING EXCEL
	def remove_product_line(self):
		self.line_ids.unlink()

	def action_export(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		worksheet = workbook.add_worksheet(u'Хүсэлт')

		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_bg_color('#9ad808')
		header.set_font_name('Arial')

		header_wrap = workbook.add_format({'bold': 1})
		header_wrap.set_font_size(10)
		header_wrap.set_align('center')
		header_wrap.set_align('vcenter')
		header_wrap.set_border(style=1)

		contest_center = workbook.add_format()
		contest_center.set_font_size(9)
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)
		contest_center.set_font_name('Arial')

		contest_left = workbook.add_format()
		contest_left.set_font_size(9)
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)
		contest_left.set_font_name('Arial')

		row = 0
		worksheet.merge_range(row, 0, row, 5, u'Шинэ барааны хүсэлт импортлох загвар', header_wrap)

		if self.state == 'draft':
			row += 1
			worksheet.merge_range(row, 0, row+1, 0, u"Барааны нэр", header)
			worksheet.merge_range(row, 1, row+1, 1, u"Эдийн дугаар", header)
			worksheet.merge_range(row, 2, row+1, 2, u"Хөрвөсөн код", header)
			worksheet.merge_range(row, 3, row+1, 3, u"Барааны мэдээлэл", header)
			worksheet.merge_range(row, 4, row+1, 4, u"Хэмжих нэгж", header)
			worksheet.merge_range(row, 5, row+1, 5, u"Барааны ангилал", header)
			worksheet.set_column('A:F', 20)

			row += 1
			for item in self.line_ids:
				row+=1
				worksheet.write(row, 0, item.name or '', contest_left)
				worksheet.write(row, 1, item.part_number or '', contest_center)
				worksheet.write(row, 2, item.converted_part_number or '', contest_center)
				worksheet.write(row, 3, item.description or '', contest_left)
				worksheet.write(row, 4, item.uom_id.name or '', contest_center)
				worksheet.write(row, 5, item.category_id.name or '', contest_left)
		else:
			row += 1
			worksheet.merge_range(row, 0, row+1, 0, u"Барааны нэр", header)
			worksheet.merge_range(row, 1, row+1, 1, u"Эдийн дугаар", header)
			worksheet.merge_range(row, 2, row+1, 2, u"Хөрвөсөн код", header)
			worksheet.merge_range(row, 3, row+1, 3, u"Барааны мэдээлэл", header)
			worksheet.merge_range(row, 4, row+1, 4, u"Хэмжих нэгж", header)
			worksheet.merge_range(row, 5, row+1, 5, u"Барааны ангилал", header)
			worksheet.merge_range(row, 6, row+1, 6, u"Шинэ бараа", header)
			worksheet.write_comment(row, 6, 'Зөвхөн шинэ барааны мэдээлэл импортлогдоно. Бусад багана импортлогдохгүйг анхаарна уу!')
			worksheet.set_column('A:G', 20)

			row += 1
			for item in self.line_ids:
				row+=1
				worksheet.write(row, 0, item.name or '', contest_left)
				worksheet.write(row, 1, item.part_number or '', contest_center)
				worksheet.write(row, 2, item.converted_part_number or '', contest_center)
				worksheet.write(row, 3, item.description or '', contest_left)
				worksheet.write(row, 4, item.uom_id.name or '', contest_center)
				worksheet.write(row, 5, item.category_id.name or '', contest_left)
				worksheet.write(row, 6, item.product_id.default_code or '', contest_center)

		workbook.close()

		out = base64.encodebytes(output.getvalue())
		file_name = u'Шинэ барааны хүсэлт темплейт'+'.xlsx'
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
		return {
			 'type' : 'ir.actions.act_url',
			 'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			 'target': 'new',
		}

	def action_import_line(self):
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.import_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise UserError(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
		book = xlrd.open_workbook(fileobj.name)
		
		try :
			sheet = book.sheet_by_index(0)
		except:
			raise UserError(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
		nrows = sheet.nrows
		
		r = 3
		line_obj = self.env['new.product.request.line']
		for item in range(r,nrows):
			row = sheet.row(item)
			product_name = row[0].value
			converted_code = row[2].value
			product_info = row[3].value
			product_uom = row[4].value
			product_category = row[5].value
			try:
				product_code = str(row[1].value)
			except ValueError:
				product_code = str(int(row[1].value))
			if self.state != 'draft':
				try:
					new_product_code = str(row[6].value)
				except ValueError:
					new_product_code = str(int(row[6].value))

			if self.state == 'draft':
				uom_obj = self.env['uom.uom'].search([('name','=',product_uom)], limit=1)
				category_obj = self.env['product.category'].search([('name','=',product_category)], limit=1)
				part_number_line = self.line_ids.filtered(lambda r: r.part_number in product_code and r.name in product_name)
				if part_number_line:
					part_number_line.write({
						'name': product_name,
						'part_number': product_code,
						'converted_part_number': converted_code,
						'description': product_info,
						'uom_id': uom_obj.id if uom_obj else '',
						'category_id': category_obj.id if category_obj else ''
					})
				else:
					line_obj.create({
						'parent_id': self.id,
						'name': product_name,
						'part_number': product_code,
						'converted_part_number': converted_code,
						'description': product_info,
						'uom_id': uom_obj.id if uom_obj else False,
						'category_id': category_obj.id if category_obj else False
					})
			else:
				product_obj = self.env['product.product'].search([('default_code','=',new_product_code)], limit=1)
				part_number_line = self.line_ids.filtered(lambda r: r.part_number in product_code and r.name in product_name)
				part_number_line.write({
					'product_id': product_obj.id if product_obj else False,
				})

class newProductRequestLine(models.Model):
	_name = 'new.product.request.line'
	_description = 'New product request line'

	parent_id = fields.Many2one('new.product.request', string='Parent ID')
	name = fields.Char(string='Барааны нэр')
	product_id = fields.Many2one('product.product', string='Шинэ Бараа')
	created_default_code = fields.Char(related='product_id.default_code', string='Internal Reference')
	part_number = fields.Char(string='Эдийн дугаар', required=True)
	converted_part_number = fields.Char(string='Хөрвөсөн код')
	description = fields.Char(string='Барааны мэдээлэл')
	category_id = fields.Many2one('product.category', string='Ангилал', required='1')
	uom_id = fields.Many2one('uom.uom', string='Хэмжих нэгж')

	# Эдийн дугаар орон шалгах
	#TODO болиулсан Манлай
	# @api.onchange('part_number')
	# def check_digits(self):
	# 	result = 0
	# 	for i in self:
	# 		if i.part_number:
	# 			result = len(re.findall('',str(i.part_number)))
	# 			if result != 9:
	# 				raise UserError('Эдийн дугаар 8 оронтой байна.')