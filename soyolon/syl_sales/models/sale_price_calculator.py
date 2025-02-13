from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date, datetime
import math

import os,xlrd
from io import BytesIO
from tempfile import NamedTemporaryFile
import base64
import xlsxwriter



class SalePriceCalculator(models.Model):
	_name = "sale.price.calculator"
	_description = 'Sale Price Calculator'


	def _get_dynamic_flow_line_id(self):
		return self.flow_find()

	def _get_default_flow_id(self):
		search_domain = []
		search_domain.append(('model_id.model','=','sale.price.calculator'))
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

	visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
		default=_get_dynamic_flow_line_id,
		copy=False, domain="[('id','in',visible_flow_line_ids)]")

	flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True,
		default=_get_default_flow_id,
		 copy=True, domain="[('model_id.model','=','sale.price.calculator')]", index=True)
	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True)
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
	state = fields.Char(string='Төлөв', compute='_compute_state', store=True, index=True)
	is_not_edit = fields.Boolean(related="flow_line_id.is_not_edit", readonly=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='Төлөв', store=True, index=True)
	history_ids = fields.One2many('sale.price.calculator.history', 'sale_price_id', 'Түүхүүд')

	def action_done(self):
		for rec in self:
			rec.state = "done"

	# @api.depends('flow_id.line_ids', 'flow_id.is_amount')
	# def _compute_visible_flow_line_ids(self):
	# 	for item in self:
	# 		if item.flow_id:
	# 			item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'sale.price.calculator')])
	# 		else:
	# 			item.visible_flow_line_ids = []

	def send_chat_next_users(self, partner_ids):
		
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('syl_sales.sale_price_calcualtor_action').id
		html = u"""<b><a target="_blank" href=%s/web#action=%s&id=%s&view_type=form&model=sale.price.calculator>%s</a></b> дугаартай үнэ тооцоололыг хянана уу!<br/>"""%(base_url, action_id, self.id, self.name) 
		self.flow_line_id.send_chat(html, partner_ids)	
	@api.depends('flow_id.line_ids', 'flow_id.is_amount', 'total')
	def _compute_visible_flow_line_ids(self):
		for item in self:
			if item.flow_id:
				if item.flow_id.is_amount:
					flow_line_ids = []
					for fl in item.flow_id.line_ids:
						if fl.state_type in ['draft', 'cancel']:
							flow_line_ids.append(fl.id)
						elif fl.amount_price_min == 0 and fl.amount_price_max == 0:
							flow_line_ids.append(fl.id)
						elif fl.amount_price_min <= item.total <= fl.amount_price_max:
							flow_line_ids.append(fl.id)
						if fl.amount_price_min <= item.total:
							flow_line_ids.append(fl.id)
					item.visible_flow_line_ids = flow_line_ids
				else:
					item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id), ('flow_id.model_id.model', '=', 'sale.order')])
			else:
				item.visible_flow_line_ids = []

	@api.depends('flow_line_id.stage_id')
	def _compute_flow_line_id_stage_id(self):
		for item in self:
			item.stage_id = item.flow_line_id.stage_id
	#------------------------------flow------------------
	@api.depends('flow_line_id')
	def _compute_state(self):
		for item in self:
			item.state = item.flow_line_id.state_type

	def flow_find(self, order='sequence'):
		search_domain = []
		if self.flow_id:
			search_domain.append(('flow_id','=',self.flow_id.id))
		search_domain.append(('flow_id.model_id.model','=','sale.price.calculator'))
		return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1).id

	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.flow_line_id = self.flow_find()
		else:
			self.flow_line_id = False

	def action_next_stage(self):
		if self.state == 'sent':
			if not self.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True):
				raise UserError(('Борлуулалт болох сонголт хийгдээгүй байна'))
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if next_flow_line_id:
			if self.visible_flow_line_ids and next_flow_line_id.id not in self.visible_flow_line_ids.ids:
				check_next_flow_line_id = next_flow_line_id
				while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
					
					temp_stage = check_next_flow_line_id._get_next_flow_line()
					if temp_stage.id==check_next_flow_line_id.id or not temp_stage:
						break;
					check_next_flow_line_id = temp_stage
				next_flow_line_id = check_next_flow_line_id

			if next_flow_line_id._get_check_ok_flow(False, False):
				self.flow_line_id = next_flow_line_id
				if self.flow_line_id.state_type=='done':
					self.action_done()

				# History uusgeh
				self.env['sale.price.calculator.history'].create_history(next_flow_line_id, self)
				

				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users(False, False)
					if send_users:
						self.send_chat_next_users(send_users.mapped('partner_id'))
				if self.flow_line_id:
					send_users = self.flow_line_id._get_flow_users(False, False)
					if send_users:
						html = self.flow_line_id.send_chat_html(self)
						self.flow_line_id.send_chat(html, send_users.mapped('partner_id'))
			else:
				con_user = next_flow_line_id._get_flow_users(False, False)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
				# raise UserError(_('You are not confirm user'))


	def action_back_stage(self):
		back_flow_line_id = self.flow_line_id._get_back_flow_line()
		if back_flow_line_id:
			if self.visible_flow_line_ids and back_flow_line_id.id not in self.visible_flow_line_ids.ids:
				check_next_flow_line_id = back_flow_line_id
				while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
					temp_stage = check_next_flow_line_id._get_back_flow_line()
					if temp_stage.id==check_next_flow_line_id.id or not temp_stage:
						break;
					check_next_flow_line_id = temp_stage
				back_flow_line_id = check_next_flow_line_id
				
			if back_flow_line_id._get_check_ok_flow(False, False):
				self.flow_line_id = back_flow_line_id
				# History uusgeh
				self.env['sale.price.calculator.history'].create_history(back_flow_line_id, self)
			else:
				raise UserError('Та буцаах хэрэглэгч биш байна!!!')


	def action_cancel_stage(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow(False, False):
			self.flow_line_id = flow_line_id
			self.env['sale.price.calculator.history'].create_history(flow_line_id, self)
			self.state='cancel'
			return self.action_cancel()
		else:
			raise UserError(('Та цуцлах хэрэглэгч биш байна!!!'))


	def action_draft_stage(self):
		if self.sale_id:
			raise UserError(('Борлуулалт үүсэн байгаа тул устагна уу'))
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.state='draft'
			self.env['sale.price.calculator.history'].create_history(flow_line_id, self)
		else:
			raise UserError(('Та ноороглох хэрэглэгч биш байна!!!'))

	def action_cancel(self):
		for rec in self:
			rec.state = "cancel"

	def _get_number(self):
		return self.env['ir.sequence'].next_by_code('sale.price.calculator')

	name = fields.Char(string='Дугаар', default=_get_number, readonly=True)
	state = fields.Selection([('draft', 'Ноорог'),('sent', 'Хянах'),('done', 'Борлуулалхад бэлэн')], 'Төлөв', default='draft')
	partner_id = fields.Many2one('res.partner', 'Харилцагч', required=True)
	date = fields.Date('Огноо')
	total = fields.Float('Дүн')
	is_check_total = fields.Float('Үнийн саналын дүн')
	total_tax = fields.Float('НӨАТ')
	total_amount = fields.Float('ДҮН/НӨАТ')
	sale_price_calculator_line = fields.One2many('sale.price.calculator.line', 'parent_id')
	sale_id = fields.Many2one('sale.order','Үнийн санал', readonly=True)
	internal_shipping = fields.Float('Internal Shipping', store=True)
	internal_costing = fields.Float('Internal Costing')
	margin = fields.Float('Margin')
	transportation_cost = fields.Float('Transportation cost', store=True)
	is_foreign_sale  = fields.Boolean(string='Гадаад валютын борлуулалт эсэх')
	km = fields.Float(string='Тээвэрлэлтийн зай(km)')
	tn_urtug = fields.Float(string='1тн бараанд ноогдох өртөг CNY')
	cny_usd_ratio = fields.Float(string='USD/CNY Харьцаа', default=0.14)
	is_active = fields.Boolean(string='Surcharge бодуулах', default=False)
	total_price = fields.Float('Нийт дүн', compute='_compute_total_price', store=True)
	currency_id = fields.Many2one('res.currency', 'Валют')
	rate_amount = fields.Float('Ханш', default=1)

	total_price_sum_usd = fields.Float(string='Бүтээгдэхүүний үнэ /USD/', compute='_compute_internal_calc', store=True)
	trans_cost_sum_usd = fields.Float(string='Гадаад тээвэр /USD/', compute='_compute_internal_calc', store=True)
	custom_tax_sum_usd = fields.Float(string='Гаалийн татвар /USD/', compute='_compute_internal_calc', store=True)
	shiffing_sum_usd = fields.Float(string='Дотоод тээвэр, зардал /USD/', compute='_compute_internal_calc', store=True)
	extra_sum_usd = fields.Float(string='Магадлашгүй зардал /USD/', compute='_compute_internal_calc', store=True)
	total_cost_usd = fields.Float(string='Нийт өртөг /USD/', compute='_compute_internal_calc', store=True)
	profit_percent_usd = fields.Float(string='Ашиг % /USD/', compute='_compute_internal_calc', store=True)
	untax_amount_usd = fields.Float(string='Татварын өмнө үнэ /USD/', compute='_compute_internal_calc', store=True)
	nuat_amount_usd = fields.Float(string='НӨАТ /USD/', compute='_compute_internal_calc', store=True)
	total_sum_amount_usd = fields.Float(string='Нийт үнэ /USD/', compute='_compute_internal_calc', store=True)

	total_price_sum_mnt = fields.Float(string='Бүтээгдэхүүний үнэ /MNT/', compute='_compute_internal_calc', store=True)
	trans_cost_sum_mnt = fields.Float(string='Гадаад тээвэр /MNT/', compute='_compute_internal_calc', store=True)
	custom_tax_sum_mnt = fields.Float(string='Гаалийн татвар /MNT/', compute='_compute_internal_calc', store=True)
	shiffing_sum_mnt = fields.Float(string='Дотоод тээвэр, зардал /MNT/', compute='_compute_internal_calc', store=True)
	extra_sum_mnt = fields.Float(string='Магадлашгүй зардал /MNT/', compute='_compute_internal_calc', store=True)
	total_cost_mnt = fields.Float(string='Нийт өртөг /MNT/', compute='_compute_internal_calc', store=True)
	profit_percent_mnt = fields.Float(string='Ашиг % /MNT/', compute='_compute_internal_calc', store=True)
	untax_amount_mnt = fields.Float(string='Татварын өмнө үнэ /MNT/', compute='_compute_internal_calc', store=True)
	nuat_amount_mnt = fields.Float(string='НӨАТ /MNT/', compute='_compute_internal_calc', store=True)
	total_sum_amount_mnt = fields.Float(string='Нийт үнэ /MNT/', compute='_compute_internal_calc', store=True)

	so_one2_id = fields.Many2one('sale.order', related='sale_price_calculator_line.so_id', string='Борлуулалтын дугаар')
	buyer_one2_id = fields.Many2one('res.partner', related='sale_price_calculator_line.buyer_id', string='Supplier')
	excel_data = fields.Binary(string='Импорт хийх файл')


	total_price_percent = fields.Float('Бүтээгдэхүүний үнэ %', compute='_compute_internal_calc', store=True)
	transportation_percent = fields.Float('Гадаад тээвэр %', compute='_compute_internal_calc', store=True)
	custom_tax_percent = fields.Float('Гаалийн татвар %', compute='_compute_internal_calc', store=True)
	internal_shipping_percent = fields.Float('Дотоод тээвэр, зардал %', compute='_compute_internal_calc', store=True)
	extra_cost_percent = fields.Float('Магадлашгүй зардал %', compute='_compute_internal_calc', store=True)
	total_cost_percent = fields.Float('Нийт өртөг %', compute='_compute_internal_calc', store=True)
	profit_percent = fields.Float('Ашиг %', compute='_compute_internal_calc', store=True)
	untax_amount_percent = fields.Float('Татварын өмнө үнэ %', compute='_compute_internal_calc', store=True)

	# @api.depends('km','currency_id','rate_amount','state','sale_price_calculator_line.total_weight','sale_price_calculator_line.is_so_ready')
	# @api.onchange('km','currency_id','rate_amount','state')
	# def _compute_total_weight(self):
	# 	for item in self:
	# 		if item.sale_price_calculator_line:
	# 			# item.all_total_weight = sum(self.sale_price_calculator_line.filtered(lambda r: r.is_so_ready == True).mapped('total_weight')) * 0.001
	# 			item.all_total_weight = sum(self.sale_price_calculator_line.mapped('total_weight')) * 0.001
	# 			print
	# 			if item.currency_id.name == 'MNT':
	# 				item.internal_shipping = item.cny_usd_ratio * item.km * (0.001*item.all_total_weight)
	# 				item.transportation_cost = 0 
	# 			else:
	# 				item.internal_shipping = 0
	# 				item.transportation_cost = item.all_total_weight * 0.001 * (item.tn_urtug*item.rate_amount)
	# 		else:
	# 			item.all_total_weight = 0
	# 			item.internal_shipping = 0

	def export_excel(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		file_name = 'Импорт.xlsx'
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)
		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_bg_color('#6495ED')

		header_wrap = workbook.add_format({'bold': 1})
		header_wrap.set_text_wrap()
		header_wrap.set_font_size(9)
		header_wrap.set_align('center')
		header_wrap.set_align('vcenter')
		header_wrap.set_border(style=1)
		header_wrap.set_bg_color('#6495ED')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)

		worksheet = workbook.add_worksheet(u'Үнэ тооцоолол')
		worksheet.write(0,1, u"Үнэ тооцоолол", h1)
		# TABLE HEADER
		row = 1
		worksheet.write(row, 0, u"Parts", header_wrap)
		worksheet.set_column('A:A', 15)
		worksheet.write(row, 1, u"Buyer", header_wrap)
		worksheet.set_column('B:B', 10)
		worksheet.write(row, 2, u"Qty", header_wrap)
		worksheet.set_column('C:C', 10)
		worksheet.write(row, 3, u"Unit Weight", header_wrap)
		worksheet.set_column('D:D', 10)
		worksheet.write(row, 4, u"Unit price", header_wrap)
		worksheet.set_column('E:E', 10)
		worksheet.write(row, 5, u"Transportation Cost", header_wrap)
		worksheet.set_column('F:F', 10)

		worksheet.write(row, 6, u"Total Weight", header_wrap)
		worksheet.set_column('G:G', 10)
		worksheet.write(row, 7, u"Total Price", header_wrap)
		worksheet.set_column('H:H', 10)
		worksheet.write(row, 8, u"Custom tax", header_wrap)
		worksheet.set_column('I:I', 10)
		worksheet.write(row, 9, u"Internal Shipping", header_wrap)
		worksheet.set_column('J:J', 10)
		worksheet.write(row, 10, u"Internal Costing", header_wrap)
		worksheet.set_column('K:K', 10)
		worksheet.write(row, 11, u"Total Cost", header_wrap)
		worksheet.set_column('L:L', 10)
		worksheet.write(row, 12, u"Distribution", header_wrap)
		worksheet.set_column('M:M', 10)
		worksheet.write(row, 13, u"Margin %", header_wrap)
		worksheet.set_column('N:N', 10)
		worksheet.write(row, 14, u"Margin", header_wrap)
		worksheet.set_column('O:O', 10)
		worksheet.write(row, 15, u"Surcharge", header_wrap)
		worksheet.set_column('P:P', 10)
		worksheet.write(row, 16, u"Total Price", header_wrap)
		worksheet.set_column('Q:Q', 10)

		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

		return {
			'type' : 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
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
		row = 2
		price_calculator = self.env['sale.price.calculator.line']
		for item in range(row, rows):
			row = sheet.row(item)
	
			code = str(row[0].value)		
			partner = row[1].value
			qty = row[2].value
			unit_weight = row[3].value
			unit_price = row[4].value
			transportation_cost = row[5].value
			total_weight = row[6].value
			total_price = row[7].value
			custom_tax = row[8].value
			internal_shipping = row[9].value
			internal_costing = row[10].value
			total_cost = row[11].value
			distribution = row[12].value
			avail_margin = row[13].value
			margin = row[14].value
			surcharge = row[15].value
			total_price_last = row[16].value
			
			# TODO хэрэг болж магадгүй
			try:
				code = str(row[0].value)
				partner = str(row[1].value)
			except ValueError:
				code = str(int(row[0].value))
				partner = str(int(row[1].value))

			product_id = self.env['product.product'].search(['|',('product_code','=',code),('default_code','=',code)], limit=1)
			partner_id = self.env['res.partner'].search([('vat','=',partner)], limit=1)
			if not partner_id:
				raise UserError('%s регистртэй харилцагч олдсонгүй' % (partner))
			if product_id:
				obj = price_calculator.create({
					'parent_id': self.id,
					'product_id': product_id.id,
					'buyer_id': partner_id.id,
					'qty': qty,
					'unit_weight': unit_weight,
					'unit_price': unit_price,
					'transportation_cost': transportation_cost,
					'total_weight': total_weight,
					'total_price': total_price,
					'custom_tax': custom_tax,
					'internal_shipping': internal_shipping,
					'internal_costing': internal_costing,
					'total_cost': total_cost,
					'distribution': distribution,
					'avail_margin': avail_margin,
					'margin': margin,
					'surcharge': surcharge,
					'total_price_last':total_price_last
				})
			else:
				# raise UserError(code + ' кодтой бараа олдсонгүй !!!!!')
				raise UserError('%s кодтой бараа олдсонгүй' % (code))
	
	def unlink(self):
		for bl in self:
			if bl.state != 'draft':
				raise UserError('Ноорог төлөвтэй биш бол устгах боломжгүй.')
		return super(SalePriceCalculator, self).unlink()


	@api.onchange('sale_price_calculator_line','internal_shipping','internal_costing','margin','transportation_cost','sale_price_calculator_line.transportation_cost','sale_price_calculator_line.is_so_ready','tn_urtug','is_active')
	def update_numbers(self):
		total_price = self.total_price
		for item in self.sale_price_calculator_line:
			item.total_weight = item.qty * item.unit_weight
			item.total_price = item.qty * item.unit_price
			if total_price!=0 and item.total_price:
				item.distribution = item.total_price/total_price
			# item.transportation_cost = self.transportation_cost*item.distribution
			# item.internal_shipping = item.transportation_cost*30/100 tur haav
			item.internal_shipping = self.cny_usd_ratio*self.km*(0.001*item.total_weight)
			item.internal_costing = item.internal_shipping*30/100
			# item.transportation_cost = item.total_price*self.transportation_cost/100 tur haav
			print('transportation_cost====', item.total_weight, self.tn_urtug, self.cny_usd_ratio)
			item.transportation_cost = item.total_weight*0.001*self.tn_urtug*self.cny_usd_ratio
			item.custom_tax = (item.transportation_cost*0.2+item.total_price)*0.055
			item.total_cost = item.total_price+item.transportation_cost+item.custom_tax+item.internal_shipping+item.internal_costing
			# item.margin = item.total_cost*self.margin/(100-self.margin)
			item.ochange_avail_margin()
			if self.is_active:
				item.surcharge = ((item.total_cost+item.margin)/0.98)*0.02
			else:
				item.surcharge = 0
			item.total_price_last = item.surcharge+item.margin+item.total_cost
			item.total_price_mnt = math.ceil(item.total_price_last*item.rate / 100) * 100
			item.unit_price_mnt = math.ceil(item.total_price_mnt/item.qty / 100) * 100 if item.qty else 0
			
			
		for buyer in self.sale_price_calculator_line.mapped('buyer_id'):
			for line in self.sale_price_calculator_line.filtered(lambda r: r.buyer_id.id == buyer.id):
				line.distribution = line.total_price/sum(self.sale_price_calculator_line.filtered(lambda r: r.buyer_id.id == buyer.id).mapped('total_price')) if line.total_price else 0
				# line.transportation_cost = line.qty/sum(self.sale_price_calculator_line.filtered(lambda r: r.buyer_id.id == buyer.id).mapped('qty'))*self.transportation_cost if line.qty else 0
				# line.internal_shipping = line.distribution*self.internal_shipping
				# line.internal_shipping = line.transportation_cost*30/100 tur haav
				item.internal_shipping = self.cny_usd_ratio*self.km*(0.001*item.total_weight)
				# line.internal_costing = line.distribution*self.internal_costing
				line.internal_costing = line.internal_shipping*30/100
				# item.transportation_cost = self.transportation_cost*line.distribution
				# item.transportation_cost = item.total_price*self.transportation_cost/100 tur haav
				item.transportation_cost = item.total_weight*0.001*self.tn_urtug*self.cny_usd_ratio
		self.total = sum(line.unit_price_mnt*line.qty for line in self.sale_price_calculator_line)
		self.is_check_total = sum(self.sale_price_calculator_line.filtered(lambda r: r.is_so_ready == True).mapped('total_price_mnt'))
		self.total_tax = self.total*0.1
		self.total_amount = self.total + self.total_tax



	@api.depends('sale_price_calculator_line','sale_price_calculator_line.total_price')
	def _compute_total_price(self):
		for item in self:
			item.total_price = sum(item.sale_price_calculator_line.mapped('total_price'))

	def action_to_confirm(self):
			self.write({'state': 'done'})

	@api.onchange('margin')
	def onchange_margin(self):
		for line in self.sale_price_calculator_line:
			line.avail_margin = self.margin


	def create_sale_order(self):
		if self.sale_id:
			raise UserError(('%s дугаартай үнийн санал үүссэн байна.'%self.sale_id.name))
		vals = []
		for item in self.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True):
			vals.append((0,0,{
				'sale_price_calculator_line_id': item.id,
				'product_id': item.product_id.id,
				'product_uom_qty': item.qty,
				'price_unit': item.unit_price_mnt if not self.is_foreign_sale else item.total_price_last/item.qty
			}))
		sale_val={
			'partner_id': self.partner_id.id,
			'order_line': vals,
			'validity_date': self.date,
			'pricelist_id': self.env['product.pricelist'].search([('currency_id.name','=','MNT')], order='id asc', limit=1).id
			if not self.is_foreign_sale else self.env['product.pricelist'].search([('currency_id.id','in', self.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('currency_id.id'))], order='id asc', limit=1).id
			}
		self.sale_id = self.env['sale.order'].create(sale_val)
	
	@api.depends('rate_amount','sale_price_calculator_line','currency_id','is_active')
	def _compute_internal_calc(self):
		for item in self:
			if item.is_check_total and item.sale_price_calculator_line:
				if item.currency_id.name!='MNT':
					item.total_price_sum_usd = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('total_price'))
					item.trans_cost_sum_usd = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('transportation_cost'))
					item.custom_tax_sum_usd = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('custom_tax'))
					item.shiffing_sum_usd = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('internal_shipping')) + sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('internal_costing'))
					item.extra_sum_usd = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('surcharge'))
					item.total_cost_usd = item.total_price_sum_usd + item.trans_cost_sum_usd + item.custom_tax_sum_usd + item.shiffing_sum_usd + item.extra_sum_usd
					
					item.total_price_sum_mnt = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('total_price')) * item.rate_amount
					item.trans_cost_sum_mnt = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('transportation_cost')) * item.rate_amount
					item.custom_tax_sum_mnt = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('custom_tax')) * item.rate_amount
					item.shiffing_sum_mnt = (sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('internal_shipping')) + sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('internal_costing'))) * item.rate_amount
					item.extra_sum_mnt = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('surcharge')) * item.rate_amount
					item.total_cost_mnt = item.total_price_sum_mnt + item.trans_cost_sum_mnt + item.custom_tax_sum_mnt + item.shiffing_sum_mnt + item.extra_sum_mnt
					item.untax_amount_mnt = item.is_check_total
					item.profit_percent_mnt = item.is_check_total - item.total_cost_mnt
					item.nuat_amount_mnt = item.untax_amount_mnt *0.1
					item.total_sum_amount_mnt = item.untax_amount_mnt + item.nuat_amount_mnt

					if item.profit_percent_mnt and item.rate_amount:
						item.profit_percent_usd = item.profit_percent_mnt/item.rate_amount
					item.untax_amount_usd = item.untax_amount_mnt/item.rate_amount
					item.nuat_amount_usd = item.untax_amount_usd *0.1
					item.total_sum_amount_usd = item.untax_amount_usd + item.nuat_amount_usd

					if item.total_price_sum_mnt:
						item.total_price_percent = (item.total_price_sum_mnt/item.total_cost_mnt)*100
					if item.trans_cost_sum_mnt:
						item.transportation_percent = (item.trans_cost_sum_mnt/item.total_cost_mnt)*100
					if item.custom_tax_sum_mnt:
						item.custom_tax_percent = (item.custom_tax_sum_mnt/item.total_cost_mnt)*100
					if item.shiffing_sum_mnt:
						item.internal_shipping_percent = (item.shiffing_sum_mnt/item.total_cost_mnt)*100
					if item.extra_sum_mnt and item.is_active:
						item.extra_cost_percent = (item.extra_sum_mnt/item.total_cost_mnt)*100
					else:
						item.extra_cost_percent = 0
					item.total_cost_percent = (item.total_cost_mnt/item.untax_amount_mnt)*100
					item.profit_percent = (item.profit_percent_mnt/item.untax_amount_mnt)*100
					item.untax_amount_percent = (item.untax_amount_mnt/item.untax_amount_mnt)*100
					# item.untax_amount_usd = sum(line.unit_price_mnt*line.qty for line in self.sale_price_calculator_line.filtered(lambda r: r.is_so_ready == True))

				else:
					item.total_price_sum_mnt = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('total_price'))
					item.trans_cost_sum_mnt = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('transportation_cost'))
					item.custom_tax_sum_mnt = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('custom_tax'))
					item.shiffing_sum_mnt = (sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('internal_shipping')) + sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('internal_costing')))
					item.extra_sum_mnt = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('custom_tax'))
					item.total_cost_mnt = item.total_price_sum_mnt + item.trans_cost_sum_mnt + item.custom_tax_sum_mnt + item.shiffing_sum_mnt + item.extra_sum_mnt
					item.untax_amount_mnt = item.is_check_total
					item.profit_percent_mnt = item.is_check_total - item.total_cost_mnt
					item.nuat_amount_mnt = item.is_check_total * 0.1
					item.total_sum_amount_mnt = item.is_check_total + item.nuat_amount_mnt
					
					if item.total_price_sum_mnt:
						item.total_price_percent = item.total_price_sum_mnt/item.total_cost_mnt
					if item.trans_cost_sum_mnt:
						item.transportation_percent = item.trans_cost_sum_mnt/item.total_cost_mnt
					if item.custom_tax_sum_mnt:
						item.custom_tax_percent = item.custom_tax_sum_mnt/item.total_cost_mnt
					if item.shiffing_sum_mnt:
						item.internal_shipping_percent = item.shiffing_sum_mnt/item.total_cost_mnt
					if item.extra_sum_mnt and item.is_active:
						item.extra_cost_percent = item.extra_sum_mnt/item.total_cost_mnt
					else:
						item.extra_cost_percent = 0
					item.total_cost_percent = item.total_cost_mnt/item.untax_amount_mnt
					item.profit_percent = item.profit_percent_mnt/item.untax_amount_mnt
					item.untax_amount_percent = item.untax_amount_mnt/item.untax_amount_mnt

					# item.total_price_sum_usd = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('total_price')) / item.rate_amount
					# item.trans_cost_sum_usd = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('transportation_cost'))/ item.rate_amount
					# item.custom_tax_sum_usd = sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('custom_tax'))/ item.rate_amount
					# item.shiffing_sum_usd = (sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('internal_shipping')) + sum(item.sale_price_calculator_line.filtered(lambda r: r.is_so_ready==True).mapped('internal_costing'))) / item.rate_amount
					# item.total_cost_usd = (item.total_price_sum_usd + item.trans_cost_sum_usd + item.custom_tax_sum_usd + item.shiffing_sum_usd + item.extra_sum_usd) / item.rate_amount
					# item.untax_amount_usd = sum(line.unit_price_mnt*line.qty for line in self.sale_price_calculator_line.filtered(lambda r: r.is_so_ready == True)) / item.rate_amount

					# if item.profit_percent_mnt and item.rate_amount:
					# 	item.profit_percent_usd = item.profit_percent_mnt/item.rate_amount
					# item.nuat_amount_usd = item.untax_amount_usd *0.1
					# item.total_sum_amount_usd = item.untax_amount_usd + item.nuat_amount_usd

					item.total_price_sum_usd = 0
					item.trans_cost_sum_usd = 0
					item.custom_tax_sum_usd = 0
					item.shiffing_sum_usd = 0
					item.extra_sum_usd = 0
					item.total_cost_usd = 0
					item.untax_amount_usd = 0
					item.profit_percent_usd = 0
					item.nuat_amount_usd = 0
					item.total_sum_amount_usd = 0
					
			else:
				item.total_price_sum_usd = 0
				item.trans_cost_sum_usd = 0
				item.custom_tax_sum_usd = 0
				item.shiffing_sum_usd = 0
				item.extra_sum_usd = 0
				item.total_cost_usd = 0
				item.untax_amount_usd = 0

				item.total_price_sum_mnt = 0
				item.trans_cost_sum_mnt = 0
				item.custom_tax_sum_mnt = 0
				item.shiffing_sum_mnt = 0
				item.extra_sum_mnt = 0
				item.total_cost_mnt = 0
				item.untax_amount_mnt = 0
				item.profit_percent_mnt = 0
				item.nuat_amount_mnt = 0
				item.total_sum_amount_mnt = 0

				item.profit_percent_usd = 0
				item.nuat_amount_usd = 0
				item.total_sum_amount_usd = 0

class SalePriceCalculatorLine(models.Model):
	_name = "sale.price.calculator.line"
	_description = 'Sale Price Calculator Line'
	_order = "buyer_id"

	parent_id = fields.Many2one('sale.price.calculator', 'Parent ID', ondelete='cascade')
	product_id = fields.Many2one('product.product', 'Parts')
	buyer_id = fields.Many2one('res.partner', 'Supplier')
	currency_id = fields.Many2one(related='parent_id.currency_id', string='Currency', store=True)
	qty = fields.Float('QTY')
	unit_weight = fields.Float('Unit weight')
	unit_price = fields.Float('Unit price')
	transportation_cost = fields.Float(string='Transportation cost')
	rate = fields.Float(related='parent_id.rate_amount', string='Rate', store=True)
	total_weight = fields.Float('Total weight', readonly=True)
	total_price = fields.Float('Total price', readonly=True)
	custom_tax = fields.Float('Custom tax', readonly=True)
	internal_shipping = fields.Float('Internal shipping', readonly=True)
	internal_costing = fields.Float('Internal costing', readonly=True)
	total_cost = fields.Float('Total cost', readonly=True)
	distribution = fields.Float('Distribution', readonly=True, digits=(16,4))
	margin = fields.Float('Margin', readonly=True)
	avail_margin = fields.Float('Margin %', readonly=True)
	surcharge = fields.Float('Surcharge 2%', readonly=True)
	total_price_last = fields.Float('Total Price', readonly=True)
	total_price_mnt = fields.Float('Total Price MNT', readonly=True)
	unit_price_mnt = fields.Float('Unit Price', readonly=True)
	unit_price_tax_added = fields.Float('Unit Price Tax Added', readonly=True)
	is_so_ready = fields.Boolean('SO ready')
	so_id = fields.Many2one(related='parent_id.sale_id', string='S0 дугаар', store=True)
	partner_id = fields.Many2one(related='parent_id.partner_id', string='Харилцагч', store=True)

	@api.onchange('avail_margin', 'total_cost')
	def ochange_avail_margin(self):
		for item in self:
			item.margin = item.total_cost * item.avail_margin / (100 - item.avail_margin)

	@api.onchange('currency_id')
	def ochange_compute_curent_rate(self):
		for item in self:
			date_order = item.parent_id.date or fields.Datetime.now()
			if item.currency_id:
				rr = self.env['res.currency']._get_conversion_rate(item.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, date_order)
				item.rate = rr
			else:
				item.rate = 0


class SalePriceCalculatorHistory(models.Model):
	_name = 'sale.price.calculator.history'
	_description = 'sale price calculator history'

	sale_price_id = fields.Many2one('sale.price.calculator', 'Sale Price ID', ondelete='cascade', index=True)
	user_id = fields.Many2one('res.users','Өөрчилсөн Хэрэглэгч')
	date = fields.Datetime('Огноо', default=fields.Datetime.now, index=True)
	flow_line_id = fields.Many2one('dynamic.flow.line', 'Төлөв', index=True)
	spend_time = fields.Float(string='Зарцуулсан цаг', compute='_compute_spend_time', store=True, readonly=True, digits=(16,2))

	@api.depends('date','sale_price_id')
	def _compute_spend_time(self):
		for obj in self:
			domains = []
			if obj.sale_price_id:
				domains = [('sale_price_id','=',obj.sale_price_id.id),('id','!=',obj.id)]
			if domains and isinstance(obj.id, int):
				ll = self.env['sale.price.calculator.history'].search(domains, order='date desc', limit=1)
				if ll:
					secs = (obj.date-ll.date).total_seconds()
					obj.spend_time = secs/3600
				else:
					obj.spend_time = 0
			else:
				obj.spend_time = 0


	def create_history(self, flow_line_id, sale_price_id):
		self.env['sale.price.calculator.history'].create({
			'sale_price_id': sale_price_id.id,
			'user_id': self.env.user.id,
			'date': datetime.now(),
			'flow_line_id': flow_line_id.id
			})