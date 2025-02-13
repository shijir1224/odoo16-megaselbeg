# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
from odoo.exceptions import UserError
from datetime import datetime
import base64
from io import BytesIO
import xlsxwriter
from tempfile import NamedTemporaryFile
import os, xlrd

class PurchaseOrderComparison(models.Model):
	_inherit = 'purchase.order.comparison'

	purchase_comparison_js_line_line = fields.Many2many('purchase.comparison.js.line.line', string='Барааны мөрүүд', compute='_compute_purchase_comparison_js_line_line')
	purchase_comparison_js_line = fields.One2many('purchase.comparison.js.line', 'comparison_id', string='Харьцуулалтын мөрүүд')
	comparison_line = fields.One2many('comparison.line', 'comparison_id', string='Харьцуулалтын татварын мөрүүд')
	purchase_comparison_js_vote_line = fields.Many2many('purchase.comparison.js.vote.line', string='Саналын мөрүүд', compute='_compute_purchase_comparison_js_line_line')
	vote_flow_line_ids = fields.Many2many('dynamic.flow.line', string='Санал өгөх төлөв', compute='_compute_vote_flow_line_id')
	vote_start_flow_line = fields.Many2one('dynamic.flow.line', string='Санал эхлэх төлөв', compute='_compute_vote_start_flow_line')
	comparison_desc = fields.Text(string='Тайлбар')
	pr_ids = fields.Many2many('purchase.request', string='ХА-ын хүсэлт', compute='_compute_pr_ids')
	excel_data = fields.Binary(string='Импорт хийх файл', copy=False)
	is_price_import = fields.Boolean(string='Үнэ импортлох?')
	state = fields.Selection(selection_add=[('cancelled', 'Цуцлагдсан')])
	purchase_order_ids = fields.Many2many('purchase.order', 'purchase_order_purchase_order_comparison_js_rel', 'order_id', 'comparison_id', string='Үүссэн үнийн санал')
	count_po = fields.Integer(string='Үнийн саналын тоо', compute='_compute_count_pr_po')
	count_request = fields.Integer(string='ХА хүсэлтийн тоо', compute='_compute_count_pr_po')

	@api.depends('request_line_ids', 'purchase_order_ids')
	def _compute_count_pr_po(self):
		self.count_request = len(self.request_line_ids)
		self.count_po = len(self.purchase_order_ids)

	@api.depends('request_line_ids')
	def _compute_pr_ids(self):
		for item in self:
			item.pr_ids = item.request_line_ids.mapped('request_id').ids

	@api.depends('purchase_comparison_js_line')
	def _compute_purchase_comparison_js_line_line(self):
		self.purchase_comparison_js_line_line = self.purchase_comparison_js_line.product_line
		self.purchase_comparison_js_vote_line = self.purchase_comparison_js_line.vote_line

	@api.depends('flow_id')
	def _compute_vote_start_flow_line(self):
		if self.flow_id:
			vote_start_flow_line = self.flow_id.line_ids.filtered(lambda r: r.state_type == 'start_vote')
			if vote_start_flow_line:
				self.vote_start_flow_line = vote_start_flow_line[0]
			else:
				self.vote_start_flow_line = False
		else:
			self.vote_start_flow_line = False

	@api.depends('flow_id')
	def _compute_vote_flow_line_id(self):
		if self.flow_id:
			vote_flow_line_ids = self.flow_id.line_ids.filtered(lambda r: r.state_type == 'vote')
			if vote_flow_line_ids:
				self.vote_flow_line_ids = vote_flow_line_ids
			else:
				self.vote_flow_line_ids = False
		else:
			self.vote_flow_line_ids = False

	def check_product_vote(self):
		if len(self.purchase_comparison_js_line_line.filtered(lambda r: r.is_vote == False)) == len(self.purchase_comparison_js_line_line):
			raise UserError('Та худалдан авах ямар ч бараа чеклээгүй байна! Хэрэв чеклэсэн бол "Хадгалах" товч дарна уу.')
		product_obj = self.purchase_comparison_js_line_line.mapped('product_id')
		no_check_product = self.env['product.product']
		for product in product_obj:
			if len(self.purchase_comparison_js_line_line.filtered(lambda r: r.product_id.id == product.id and r.is_vote == False)) == len(self.purchase_comparison_js_line_line.filtered(lambda r: r.product_id.id == product.id)):
				no_check_product += product
		if no_check_product:
			raise UserError('Доорх бараанууд худалдан авах чекгүй байна! \n1. Хэрэв чеклэсэн бол "Хадгалах" товч дарна уу. \n2. Худалдан авахгүй бараа бол Барааны мэдээлэл хэсгээс бараагаа устгана уу. \n\n%s' %'\n'.join(no_check_product.mapped('display_name')))

	def check_partner_vote(self):
		flow_line_id = self.vote_flow_line_ids.filtered(lambda r: r.id == self.flow_line_id.id)
		if flow_line_id:
			vote_flow_line_ids = self.purchase_comparison_js_vote_line.filtered(lambda r: r.vote_flow_line_id == flow_line_id)
			no_vote_flow_line_ids = self.purchase_comparison_js_vote_line.filtered(lambda r: r.vote_flow_line_id == flow_line_id and not r.is_user_vote)
			if len(vote_flow_line_ids) == len(no_vote_flow_line_ids):
				raise UserError('Та санал өгөөгүй байна! Хэрэв санал өгсөн бол "Хадгалах" товч дарна уу.')

	def check_partner_all_vote(self):
		mapped_vote_flow_line = self.purchase_comparison_js_vote_line.mapped('vote_flow_line_id')
		partners = []
		for flow_line in mapped_vote_flow_line:
			vote_partners = self.purchase_comparison_js_vote_line.filtered(lambda r: r.vote_flow_line_id.id == flow_line.id and r.is_user_vote == True).mapped('partner_id.id')
			if vote_partners not in partners:
				partners.append(vote_partners)
		if partners and len(partners) == 1:
			self.action_ended()
			self.flow_line_id = self.env['dynamic.flow.line'].search([('flow_id','=',self.flow_id.id),('state_type','=','ended')]).id
			self.state_type = 'ended'

	def check_vote_point(self):
		quality_point_raise = self.purchase_comparison_js_line.filtered(lambda r: r.quality_point > 60 or r.quality_point <= 0)
		price_point_raise = self.purchase_comparison_js_line.filtered(lambda r: r.price_point > 20 or r.price_point <= 0)
		other_point_raise = self.purchase_comparison_js_line.filtered(lambda r: r.other_point > 20 or r.other_point <= 0)
		if quality_point_raise or price_point_raise or other_point_raise:
			raise UserError('Чанар 1-60, Үнэ 1-20, Бусад үзүүлэлт 1-20 хүртэлх оноо өгөх боломжтой! Доорх харилцагч дээрх бүртгэлийг засна уу!')

	def action_next_stage(self):
		self.check_partner_vote()
		if self.comparison_line.filtered(lambda r: not r.currency_id):
			raise UserError('Харилцагч дээр валют сонгоно уу!')
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if next_flow_line_id:
			if self.visible_flow_line_ids and next_flow_line_id.id not in self.visible_flow_line_ids.ids:
				check_next_flow_line_id = next_flow_line_id
				while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
					temp_stage = check_next_flow_line_id._get_next_flow_line()
					if temp_stage.id == check_next_flow_line_id.id or not temp_stage:
						break
					check_next_flow_line_id = temp_stage
				next_flow_line_id = check_next_flow_line_id
			if next_flow_line_id._get_check_ok_flow(False, False):
				self.flow_line_id = next_flow_line_id
				# мэйл, чат явуулах
				next_id = next_flow_line_id._get_next_flow_line() 
				send_users = next_id._get_flow_users() 
				html = self.send_chat_next_user(self.flow_line_id) 
				if send_users:
					# self.env.user.send_chat(html, send_users.mapped('partner_id'), with_mail=False) #TODO түр хаасан
					if next_id.is_mail: 
						self.env.user.send_emails(partners=send_users.mapped('partner_id'), subject='Худалдан авалтын харьцуулалт', body=html, attachment_ids=False)
				if next_flow_line_id.state_type == 'start_vote':
					self.action_start_vote()
					self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'comparison_id', self)
				if next_flow_line_id.state_type == 'vote':
					self.check_vote_point()
					self.check_product_vote()
					self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'comparison_id', self)
					return self.action_agian_return()
				if next_flow_line_id.state_type == 'vote_ended':
					self.action_vote_ended()
					self.check_partner_all_vote()
					self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'comparison_id', self)
					return self.action_agian_return()
				if self.flow_line_id.state_type == 'ended':
					self.action_ended()
					self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'comparison_id', self)
			else:
				con_user = next_flow_line_id._get_flow_users(False, False)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(
					u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)

	def action_back_stage(self):
		back_flow_line_id = self.flow_line_id._get_back_flow_line()
		if back_flow_line_id:
			if self.visible_flow_line_ids and back_flow_line_id.id not in self.visible_flow_line_ids.ids:
				check_next_flow_line_id = back_flow_line_id
				while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
					temp_stage = check_next_flow_line_id._get_back_flow_line()
					if temp_stage.id == check_next_flow_line_id.id or not temp_stage:
						break
					check_next_flow_line_id = temp_stage
				back_flow_line_id = check_next_flow_line_id
			if back_flow_line_id._get_check_ok_flow(False, False):
				self.flow_line_id = back_flow_line_id
				if back_flow_line_id.state_type == 'draft':
					self.action_draft()
					self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'comparison_id', self)
				if back_flow_line_id.state_type == 'start_vote':
					self.action_start_vote()
					self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'comparison_id', self)
					return self.action_agian_return()
				if back_flow_line_id.state_type == 'vote':
					self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'comparison_id', self)
					return self.action_agian_return()
				if back_flow_line_id.state_type == 'vote_ended':
					self.action_vote_ended()
					self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'comparison_id', self)
			else:
				raise UserError('Буцаах хэрэглэгч биш байна!')

	def action_agian_return(self):
		view = self.env.ref('mw_purchase_comparison.purchase_order_comparison_view_form')
		view_id = view and view.id or False
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'purchase.order.comparison',
			'res_id': self.id,
			'view_mode': 'form',
			'views': [(view.id,'form')],
			'view_id': view_id,
			'target': 'current'
		}

	def send_chat_next_user(self, flow_line_id):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action = self.env.ref('mw_purchase_comparison.action_purchase_order_comparison')
		html = u'<b>Худалдан авалтын харьцуулалт</b><br/>'
		html += u"""%s компани дээр <b>%s</b> ажилтны үүсгэсэн <a target="_blank" href=%s/web#action=%s&id=%s&view_type=form&model=purchase.order.comparison>%s</a> баримт <b>%s</b> төлөвт орлоо. Хянана уу!"""% (self.company_id.name, self.user_id.name, base_url, action.id, self.id, self.name, flow_line_id.stage_id.name)
		return html

	def action_ended(self):
		po_obj = self.env['purchase.order']
		po_line_obj = self.env['purchase.order.line']
		flow_id = self.env['dynamic.flow'].search([('model_id','=','purchase.order')], order='sequence', limit=1)
		flow_line_id = self.env['dynamic.flow.line'].search([('flow_id', '=', flow_id.id),('state_type', '=', 'dep_directors')], order='sequence', limit=1)
		for js_line in self.purchase_comparison_js_line.filtered(lambda r: r.is_create_po == False):
			vote_product_lines = js_line.product_line.filtered(lambda r: r.is_vote == True)
			if vote_product_lines:
				currency_id = self.env.user.company_id.currency_id
				if js_line.currency_id:
					currency_id = js_line.currency_id
				if vote_product_lines:
					po_vals = {
						'flow_id': flow_id.id,
						'flow_line_id': flow_line_id.id,
						'state_type': 'dep_directors',
						'partner_id': js_line.partner_id.id,
						'company_id': self.company_id.id,
						'taxes_id': js_line.taxes_id.ids if js_line.taxes_id else False,
						'currency_id': currency_id.id,
						'user_id': self.user_id.id,
						'branch_id': self.branch_id.id,
						'origin': 'Харьцуулсан судалгаа - %s' %(self.name),
						'picking_type_id': self.picking_type_id.id
					}
					po_id = po_obj.create(po_vals)
					po_id.update({'flow_line_id': flow_line_id, 'currency_id': currency_id.id})
					po_attach_item = po_id.check_items.filtered(lambda r: r.type in 'Харьцуулсан баримт')
					po_attach_item.update({'data': js_line.attachment_ids.ids})
					po_id.js_comparison_id = self.id
					js_line.is_create_po = True
					self.purchase_order_ids = [(4, po_id.id)]

					for line in vote_product_lines:
						po_line_id = po_line_obj.create({
							'order_id': po_id.id,
							'product_id': line.product_id.id,
							'product_qty': line.product_qty,
							'price_unit_without_discount': line.price_unit,
							'price_unit': line.discount_price_unit,
							'discount': line.discount,
							'taxes_id': po_id.taxes_id.ids if po_id.taxes_id else False
						})
						line.po_line_ids |= po_line_id
		self.date_order = datetime.today()
		self.state = 'ended'

	def action_start_vote(self):
		if not self.name or self.name == '/':
			self.name = self.env['ir.sequence'].next_by_code('purchase.order.comparison')
		self.state = 'vote_started'

	def action_draft(self):
		self.state = 'draft'
		self.purchase_comparison_js_line = False
		self.comparison_line = False

	def action_draft_stage(self):
		res = super(PurchaseOrderComparison, self).action_draft_stage()
		self.action_draft()
		return res

	def action_vote_ended(self):
		self.state = 'vote_ended'

	def action_cancel_stage(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if not flow_line_id:
			raise UserError('Урсгал тохиргоо буруу байна. Системийн админд хандана уу!')
		if flow_line_id._get_check_ok_flow(False, False):
			self.check_comparison_cancel()
			self.flow_line_id = flow_line_id
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'comparison_id', self)
			self.state = 'cancelled'
		else:
			cancel_user = flow_line_id._get_flow_users(False, False)
			raise UserError(_('Цуцлах хэрэглэгч биш байна!\nЦуцлах хэрэглэгчид: %s' %', '.join(cancel_user.mapped('display_name'))))

	def check_comparison_cancel(self):
		if self.purchase_order_ids:
			if self.purchase_order_ids.filtered(lambda r: r.state_type == 'done'):
				raise UserError('Үүссэн ХА батлагдсан байна. Цуцлах боломжгүй!')
			else:
				for po in self.purchase_order_ids:
					po.action_cancel_stage()
				self.purchase_order_ids.with_context(from_comparison=True).unlink()

	def unlink(self):
		for obj in self:
			if obj.state != 'draft':
				raise UserError(_('Ноорог төлөвтэй бичлэгийг устгах боломжтой!'))
		return super(PurchaseOrderComparison, self).unlink()

	def view_purchase_request(self):
		self.ensure_one()
		action = self.env.ref('mw_purchase_request.action_purchase_request_line_view')
		vals = action.read()[0]
		domain = [('id','in',self.request_line_ids.ids)]
		vals['domain'] = domain
		vals['context'] = {}
		return vals

	def view_purchase_order(self):
		self.ensure_one()
		action = self.env.ref('purchase.purchase_form_action')
		vals = action.read()[0]
		domain = [('id','in',self.purchase_order_ids.ids)]
		vals['domain'] = domain
		vals['context'] = {}
		return vals

	def save_comparison_data(self, desc_data='', discount_data=0, quality_data=0, price_data=0, other_data=0, honog_data=0, teever_tatvar_data=0, insurance_other_expense_data=0, product_list_data={}, vote_list_data={}, partner_data={}):
		purchase_js_line = self.env['purchase.comparison.js.line']
		purchase_js_line_line = self.env['purchase.comparison.js.line.line']
		purchase_js_vote_line = self.env['purchase.comparison.js.vote.line']
		comparison_line = self.env['comparison.line']
		js_line = self.purchase_comparison_js_line.filtered(lambda r: r.partner_id.id == int(partner_data.get('partner_id', False)))
		if js_line:
			if desc_data:
				js_line.write({'description': desc_data})
			if discount_data:
				js_line.write({'discount': discount_data})
			if quality_data:
				js_line.write({'quality_point': quality_data})
			if price_data:
				js_line.write({'price_point': price_data})
			if other_data:
				js_line.write({'other_point': other_data})
			if honog_data:
				js_line.write({'niiluuleh_hugatsaa': honog_data})
			if teever_tatvar_data:
				js_line.write({'teever_tatvar': teever_tatvar_data})
			if insurance_other_expense_data:
				js_line.write({'insurance_other_expense': insurance_other_expense_data})
			if product_list_data:
				for product in product_list_data:
					for product_line in js_line.product_line:
						if product_line.product_id.id == product['product_id']:
							product_line.write({'price_unit': product['price_unit'], 
												'is_vote': product['is_vote'],
												'discount': product['discount']})
							if js_line.discount > 0:
								product_line.write({'discount': discount_data})
			if vote_list_data:
				for vote in vote_list_data:
					for vote_line in js_line.vote_line:
						if vote_line.vote_flow_line_id.id == vote['vote_id']:
							vote_line.write({'is_user_vote': vote['is_user_vote']})
			comparison_line_obj = comparison_line.search([('comparison_id', '=', js_line.comparison_id.id),('partner_id','=',js_line.partner_id.id)])
			if not comparison_line_obj:
				comparison_line.create({
					'comparison_id': js_line.comparison_id.id,
					'partner_id': js_line.partner_id.id
				})
		elif partner_data.get('comparison_id', False) and partner_data.get('partner_id', False) or desc_data or discount_data or quality_data or price_data or other_data or honog_data or teever_tatvar_data or insurance_other_expense_data or product_list_data or vote_list_data:
			js_line_obj = purchase_js_line.create({
				'comparison_id': partner_data['comparison_id'],
				'partner_id': partner_data['partner_id'],
				'description': desc_data,
				'discount': discount_data,
				'quality_point': quality_data,
				'price_point': price_data,
				'other_point': other_data,
				'niiluuleh_hugatsaa': honog_data,
				'teever_tatvar': teever_tatvar_data,
				'insurance_other_expense': insurance_other_expense_data
			})
			for product_line in self.line_ids:
				js_line_line_obj = purchase_js_line_line.create({
					'parent_id': js_line_obj.id,
					'product_id': product_line.product_id.id,
					'product_qty': product_line.product_qty,
					'request_line_ids': [(6, 0, product_line.request_line_ids.ids)]
				})
				for product in product_list_data:
					if product_line.product_id.id == product['product_id']:
						js_line_line_obj.write({'price_unit': product['price_unit'],
												'is_vote': product['is_vote'],
												'discount': product['discount']})
			for vote_line in self.vote_flow_line_ids:
				js_vote_line_obj = purchase_js_vote_line.create({
					'parent_id': js_line_obj.id,
					'vote_flow_line_id': vote_line.id
				})
				for vote in vote_list_data:
					if js_vote_line_obj.vote_flow_line_id.id == vote['vote_id']:
						js_vote_line_obj.write({'is_user_vote': vote['is_user_vote']})

			comparison_line.create({
				'comparison_id': js_line_obj.comparison_id.id,
				'partner_id': js_line_obj.partner_id.id
			})

		return True

	def action_export(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		worksheet = workbook.add_worksheet(u'sheet')

		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_bg_color('#EE9A4D')
		header.set_font_name('Arial')
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)

		contest_center = workbook.add_format()
		contest_center.set_font_size(9)
		contest_center.set_font_name('Arial')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)

		contest_left = workbook.add_format()
		contest_left.set_font_size(9)
		contest_left.set_font_name('Arial')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		row = 0

		worksheet.write(row, 0, u"Харилцагч", header)
		worksheet.write(row, 1, u"Бараа", header)
		worksheet.write(row, 2, u"Үнэ", header)
		worksheet.write(row, 3, u"Худалдан авах?", header)
		worksheet.set_column('A:B', 20)
		worksheet.set_column('C:C', 10)
		worksheet.set_column('D:D', 15)
		worksheet.write_comment(row, 0, 'Харилцагчийн нэр засвар хийхгүй!')
		worksheet.write_comment(row, 1, 'Барааны код засвар хийхгүй!')
		worksheet.write_comment(row, 3, 'Зөвхөн Тийм/Үгүй гэсэн сонголтоос хийнэ үү!')

		for line in self.purchase_comparison_js_line_line:
			row += 1
			worksheet.write(row, 0, line.partner_id.name, contest_center)
			worksheet.write(row, 1, line.product_id.default_code, contest_center)
			worksheet.write(row, 2, line.price_unit, contest_left)
			worksheet.write(row, 3, 'Тийм' if line.is_vote else 'Үгүй', contest_center)

		workbook.close()

		out = base64.encodebytes(output.getvalue())
		file_name = self.name+'.xlsx'
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
		return {
			 'type' : 'ir.actions.act_url',
			 'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			 'target': 'new',
		}

	def import_excel(self):
		if not self.excel_data:
			raise UserError(u'Импорт хийх файлаа оруулна уу!')
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise UserError(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
		book = xlrd.open_workbook(fileobj.name)

		try :
			sheet = book.sheet_by_index(0)
		except:
			raise UserError(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
		rows = sheet.nrows

		row = 1
		for item in range(row, rows):
			row = sheet.row(item)
			try:
				partner = str(row[0].value)
				default_code = str(row[1].value)
			except ValueError:
				partner = str(int(row[0].value))
				default_code = str(int(row[1].value))
			unit_price = row[2].value
			is_vote = row[3].value

			line = self.purchase_comparison_js_line_line.filtered(lambda r: r.partner_id.name == partner and r.product_id.default_code == default_code)

			if line:
				line.update({'price_unit': unit_price, 'is_vote': True if is_vote == 'Тийм' else False})
			else:
				raise UserError('"%s" харилцагч дээрх, "%s" бараа олдсонгүй! Хэрэв байгаа бол ХАДГАЛАХ товч дарна уу.' %(partner, default_code))
		return self.action_agian_return()

class ComparisonLine(models.Model):
	_name = 'comparison.line'
	_description = 'Харьцуулалтын татварын мөрүүд'

	comparison_id = fields.Many2one('purchase.order.comparison', required=True, string='Харьцуулалт', ondelete='cascade')
	partner_id = fields.Many2one('res.partner', string='Харилцагч', ondelete='cascade', readonly=True)
	currency_id = fields.Many2one('res.currency', string='Валют')
	taxes_id = fields.Many2many('account.tax', string='Татвар')
	attachment_ids = fields.Many2many('ir.attachment', string='Хавсралт', required=True)

class PurchaseComparisonJsLine(models.Model):
	_name = 'purchase.comparison.js.line'
	_description = 'Худалдан авалт харьцуулалтийн мөр'

	comparison_id = fields.Many2one('purchase.order.comparison', required=True, string='Харьцуулалт', ondelete='cascade')
	partner_id = fields.Many2one('res.partner', string='Харилцагч', ondelete='cascade')
	description = fields.Char(string='Тайлбар', readonly=True)
	discount = fields.Float(string='Хөнгөлөлт(%)', readonly=True)
	quality_point = fields.Float(string='Чанар', readonly=True)
	price_point = fields.Float(string='Үнэ', readonly=True)
	other_point = fields.Float(string='Бусад үзүүлэлт', readonly=True)
	total_point = fields.Float(string='Нийт оноо', compute='_compute_total_point')
	niiluuleh_hugatsaa = fields.Float(string='Нийлүүлэх хугацаа (хоног)', readonly=True)
	teever_tatvar = fields.Float(string='Тээвэр, Татвар', readonly=True)
	insurance_other_expense = fields.Float(string='Даатгал, бусад нэмэлт зардал', readonly=True)
	total_expense = fields.Float(string='Нийт зардал', compute='_compute_total_expense')
	total_qty = fields.Float(string='Нийт тоо', compute='_compute_total_qty')
	total_price = fields.Float(string='Нийт дүн', compute='_compute_total_price')
	discount_total_price = fields.Float(string='Нийт дүн/хөнгөлөлт хассан/', compute='_compute_total_price')
	voted_total_price = fields.Float(string='Сонгосон барааны нийт дүн', compute='_compute_total_price')
	discount_currency_amount = fields.Float(string='Төгрөгөөр/хөнгөлөлт хассан/', compute='_compute_currency_amount')
	currency_amount = fields.Float(string='Төгрөгөөр', compute='_compute_currency_amount')
	voted_discount_currency_amount = fields.Float(string='Сонгосон бараа төгрөгөөр/хөнгөлөлт хассан/', compute='_compute_currency_amount')
	voted_currency_amount = fields.Float(string='Сонгосон бараа төгрөгөөр', compute='_compute_currency_amount')
	discount_voted_total_price = fields.Float(string='Сонгосон барааны нийт дүн/хөнгөлөлт хассан/', compute='_compute_total_price')
	product_line = fields.One2many('purchase.comparison.js.line.line', 'parent_id', string='Барааны мөрүүд')
	vote_line = fields.One2many('purchase.comparison.js.vote.line', 'parent_id', string='Саналын мөрүүд')
	is_create_po = fields.Boolean(string='PO үүссэн эсэх', readonly=True)
	attachment_ids = fields.Many2many('ir.attachment', string='Хавсралт', compute='_compute_comparison_line')
	currency_id = fields.Many2one('res.currency', string='Валют', compute='_compute_comparison_line')
	taxes_id = fields.Many2many('account.tax', string='Татвар', compute='_compute_comparison_line')

	@api.depends('comparison_id.create_date')
	def _compute_currency_amount(self):
		for item in self:
			if item.currency_id:
				rr = self.env['res.currency']._get_conversion_rate(item.currency_id, item.comparison_id.company_id.currency_id, item.comparison_id.company_id, item.comparison_id.create_date)
				item.discount_currency_amount = rr * item.discount_total_price
				item.currency_amount = rr * item.total_price
				item.voted_discount_currency_amount = rr * item.discount_voted_total_price
				item.voted_currency_amount = rr * item.voted_total_price
			else:
				item.discount_currency_amount = 0
				item.currency_amount = 0
				item.voted_discount_currency_amount = 0
				item.voted_currency_amount = 0

	@api.depends('comparison_id.comparison_line')
	def _compute_comparison_line(self):
		for item in self:
			comparison_line_id = item.comparison_id.comparison_line.filtered(lambda r: r.partner_id.id == item.partner_id.id)
			if comparison_line_id:
				item.attachment_ids = comparison_line_id.attachment_ids if comparison_line_id.attachment_ids else False
				item.currency_id = comparison_line_id.currency_id if comparison_line_id.currency_id else False
				item.taxes_id = comparison_line_id.taxes_id if comparison_line_id.taxes_id else False
			else:
				item.attachment_ids = False
				item.currency_id = False
				item.taxes_id = False

	@api.depends('product_line.product_qty')
	def _compute_total_qty(self):
		for item in self:
			if item.product_line:
				item.total_qty = sum([line.product_qty for line in item.product_line])
			else:
				item.total_qty = 0

	@api.depends('product_line.price_unit')
	def _compute_total_price(self):
		for item in self:
			if item.product_line:
				item.total_price = sum([line.total_price for line in item.product_line])
				item.voted_total_price = sum([line.voted_total_price for line in item.product_line])
				item.discount_total_price = sum([line.discount_price_unit * line.product_qty for line in item.product_line])
				item.discount_voted_total_price = sum([line.discount_price_unit * line.product_qty for line in item.product_line if line.is_vote])
			else:
				item.total_price = 0
				item.voted_total_price = 0
				item.discount_total_price = 0
				item.discount_voted_total_price = 0

	@api.depends('quality_point', 'price_point', 'other_point')
	def _compute_total_point(self):
		for item in self:
			item.total_point = item.quality_point + item.price_point + item.other_point

	@api.depends('teever_tatvar', 'insurance_other_expense')
	def _compute_total_expense(self):
		for item in self:
			item.total_expense = item.teever_tatvar + item.insurance_other_expense

class PurchaseComparisonJsLineLine(models.Model):
	_name = 'purchase.comparison.js.line.line'
	_description = 'Худалдан авалт харьцуулалтийн js мөр'

	parent_id = fields.Many2one('purchase.comparison.js.line', required=True, string='Parent', ondelete='cascade', readonly=True)
	partner_id = fields.Many2one(related='parent_id.partner_id', string='Харилцагч')
	product_id = fields.Many2one('product.product', string='Бараа', readonly=True)
	price_unit = fields.Float(string='Нэгж үнэ(хөнгөлөлтгүй)', readonly=True)
	discount_price_unit = fields.Float(string='Нэгж үнэ', readonly=True, compute='_compute_discount_price_unit')
	discount = fields.Float(string='Хөнгөлөлт(%)', readonly=True)
	product_qty = fields.Float(string='Тоо хэмжээ', readonly=True)
	voted_total_price = fields.Float(string='Сонгосон барааны нийт үнэ', compute='_compute_total_price')
	total_price = fields.Float(string='Нийт үнэ', compute='_compute_total_price')
	is_vote = fields.Boolean(string='Худалдан авах?')
	po_line_ids = fields.One2many('purchase.order.line', 'comparison_js_line_id', string='ХА-ын мөрүүд', readonly=True)
	request_line_ids = fields.Many2many('purchase.request.line', string='Хүсэлтийн мөрүүд', readonly=True)

	@api.depends('discount', 'price_unit')
	def _compute_discount_price_unit(self):
		for item in self:
			item.discount_price_unit = item.price_unit * (1 - (item.discount or 0.0) / 100.0)

	@api.depends('price_unit', 'product_qty')
	def _compute_total_price(self):
		for item in self:
			if item.is_vote:
				item.voted_total_price = item.product_qty * item.price_unit
			else:
				item.voted_total_price = 0
			item.total_price = item.product_qty * item.price_unit

class PurchaseComparisonJsVoteLine(models.Model):
	_name = 'purchase.comparison.js.vote.line'
	_description = 'Худалдан авалт харьцуулалтийн js саналын мөр'

	parent_id = fields.Many2one('purchase.comparison.js.line', required=True, string='Parent', ondelete='cascade', readonly=True)
	partner_id = fields.Many2one(related='parent_id.partner_id', string='Харилцагч')
	vote_flow_line_id = fields.Many2one('dynamic.flow.line', string='Санал өгсөн ажилтан', readonly=True)
	is_user_vote = fields.Boolean(string='Санал өгсөн эсэх?')

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	js_comparison_id = fields.Many2one('purchase.order.comparison', string='Холбоотой харьцуулалт', readonly=True, copy=False)

	def view_purchase_comparison(self):
		self.ensure_one()
		action = self.env.ref('mw_purchase_comparison.action_purchase_order_comparison')
		vals = action.read()[0]
		domain = [('id','=',self.js_comparison_id.id)]
		vals['domain'] = domain
		vals['context'] = {}
		return vals

	def unlink(self):
		for obj in self:
			if obj.js_comparison_id and not self.env.context.get('from_comparison') == True:
				raise UserError(_('Харьцуулалтаас үүссэн ХА устгах боломжгүй!'))
		return super(PurchaseOrder, self).unlink()

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	comparison_js_line_id = fields.Many2one('purchase.comparison.js.line.line', string='Холбоотой харьцуулалтын js мөр', readonly=True, copy=False)