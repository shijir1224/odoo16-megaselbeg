from odoo import fields, models, api
from datetime import date, timedelta, datetime
from odoo.http import request
import json
from odoo.exceptions import UserError



class SaleOrder(models.Model):
	_inherit = "sale.order"

	def _digit_to_text(self, amount):
		if type(amount) not in [str] :
			amount = str(amount)
		result = u''
		BUTARHAI = True
		i = 0
		# Форматаас болоод . -ын оронд , орсон байвал засна.
		stramount = amount.replace(',','.')
		if '.' in amount:
			amount = stramount[:stramount.find('.')]
			subamount = stramount[stramount.find('.')+1:]
			if len(subamount)==1:
				subamount=str(int(subamount)*10)
		else :
			amount = stramount
			subamount = u''
		length = len(amount)
		if length == 0 or float(amount) == 0:
			return ''
		place = 0
		try :
			while i < length :
				c = length - i
				if c % 3 == 0 :
					c -= 3
				else :
					while c % 3 != 0 :
						c -= 1
				place = c / 3
				i1 = length - c
				tmp = amount[i:i1]
				j = 0
				if tmp == '000' :
					i = i1
					continue
				while j < len(tmp) :
					char = int(tmp[j])
					p = len(tmp) - j
					if char == 1 :
						if p == 3 :
							result += u'нэг зуун '
						elif p == 2 :
							result += u'арван '
						elif p == 1 :
							if len(result)==0:
								result += u'нэг '
							else:
								result += u'нэгэн '
					elif char == 2 :
						if p == 3 :
							result += u'хоёр зуун '
						elif p == 2 :
							result += u'хорин '
						elif p == 1 :
							result += u'хоёр '
					elif char == 3 :
						if p == 3 :
							result += u'гурван зуун '
						elif p == 2 :
							result += u'гучин '
						elif p == 1 :
							result += u'гурван '
					elif char == 4 :
						if p == 3 :
							result += u'дөрвөн зуун '
						elif p == 2 :
							result += u'дөчин '
						elif p == 1 :
							result += u'дөрвөн '
					elif char == 5 :
						if p == 3 :
							result += u'таван зуун '
						elif p == 2 :
							result += u'тавин '
						elif p == 1 :
							result += u'таван '
					elif char == 6 :
						if p == 3 :
							result += u'зургаан зуун '
						elif p == 2 :
							result += u'жаран '
						elif p == 1 :
							result += u'зургаан '
					elif char == 7 :
						if p == 3 :
							result += u'долоон зуун '
						elif p == 2 :
							result += u'далан '
						elif p == 1 :
							result += u'долоон '
					elif char == 8 :
						if p == 3 :
							result += u'найман зуун '
						elif p == 2 :
							result += u'наян '
						elif p == 1 :
							result += u'найман '
					elif char == 9 :
						if p == 3 :
							result += u'есөн зуун '
						elif p == 2 :
							result += u'ерэн '
						elif p == 1 :
							result += u'есөн '
					j += 1
				if place == 3 :
					result += u'тэрбум '
				elif place == 2 :
					result += u'сая '
				elif place == 1 :
					result += u'мянга '
				i = i1
		except Exception as e :
			return e

		if len(subamount) > 0 and float(subamount) > 0 :
			result2 = self._digit_to_text(subamount)
			BUTARHAI = False
			result2 = result2.replace(u'төгрөг', u'мөнгө')
			result += u' төгрөг %s' % result2
		if BUTARHAI:
			result += u' төгрөг'

		num = result
		if u"мянга төгрөг" in num:
			result = num.replace(u"мянга төгрөг",u"мянган төгрөг")
		else:
			result = num
		return result

	def get_user(self):
		return self.env.user.ids

	sale_order_plan_line = fields.One2many('sale.order.plan', 'sale_id')
	sale_team_members_ids = fields.Many2many('res.users', 'sale_members', default = get_user)
	partner_po_number = fields.Char('Харилцагчийн ПО дугаар')
	partner_invoice_number = fields.Char('Харилцагчийн нэхэмжлэлийн дугаар')
	prepayment_amount = fields.Float('Урьдчилгаа төлбөр /дүн/')
	amount_for_delivery = fields.Float('Гэрээний төлбөрийн нөхцөл /дүн/')
	quotation_end_date = fields.Date('Үнийн санал илгээх огноо', required=False)
	is_file = fields.Boolean(default=False, string='Гэрээ дүгнэсэн акт оруулах эсэх')
	attachment_ids = fields.Many2many('ir.attachment', string='Файл')
	total_amount_text = fields.Char(string='Урьдчилгаа дүн/үсгээр/', readonly=True, compute='_compute_total_confirmed_amount', store=True)
	pre_percent = fields.Float(string='Урьдчилгаа хувь')
	pre_amount_all = fields.Monetary(string='Урьдчилгаа дүн', compute='_compute_pre_amount_all')
	file_type = fields.Selection([
		('pdf','PDF'), 
		('excel','Excel')
	], default='pdf', string='Хавсралтын төрөл', required=True, readonly=True)
	partner_mail = fields.Char(related='partner_id.email', string='Бүртгэлгүй мэйл', readonly=False)
	mail_title = fields.Char(string='Гарчиг')
	mail_html = fields.Html(string='Мэйл загвар')
	supply_date = fields.Date(string='Нийлүүлэхээр тохирсон огноо')
	picking_date_done = fields.Datetime(related='picking_ids.date_done', string='Хэрэгжсэн огноо', store=True, readonly=True)
	time_delay = fields.Float('Хугацааны хоцрогдол', compute='_compute_time_delay', store=True, readonly=True)
	pr_id = fields.Many2one(related='order_line.pr_id', string='ХА хүсэлт дугаар', readonly=True)
	pr_state = fields.Many2one(related='pr_id.flow_line_id', string='ХА хүсэлт төлөв', readonly=True)
	currency_name = fields.Char('Мөнгөн тэмдэгт')
	inkonterm = fields.Char('Инкотерм')
	invoice_date = fields.Date('Нэхэмжилсэн огноо', default=fields.Date.context_today)
	payment_date = fields.Date('Төлбөр хийх хугацаа', compute='_compute_payment_date')
	partner_type = fields.Selection([
		('new', 'Шинэ'), 
		('old', 'Хуучин')
	], string='Харилцагчийн төлөв', tracking=True, copy=False)
	sale_price_buyer_id = fields.Many2one(related='order_line.sale_price_buyer_id', string='Supplier', store=True)
	sale_price_currency_id = fields.Many2one(related='order_line.sale_price_currency_id', string='Curreny/sale price/', store=True)

	p_order_ids = fields.One2many(related='order_line.pr_id.purchase_order_ids', string='ХА', readonly=True)
	sale_price_calc_ids = fields.One2many('sale.price.calculator', 'sale_id', string='Үнэ тооцоолол', readonly=True)
	sale_price_calc_line_ids = fields.One2many('sale.price.calculator.line', 'so_id', string='Үнэ тооцоолол мөр', readonly=True)

	niit_urtug = fields.Float(string='Нийт өртөг', compute='_compute_niit_urtug', store=True, readonly=True)

	total_delivered_price = fields.Float(string='Захиалгын дүн/Хүргэгдсэн/', compute='_com_delivered_amount', store=True, readonly=True)
	total_delivered_nuat_price = fields.Float(string='Захиалын НӨАТ дүн/Хүргэгдсэн/', compute='_com_delivered_amount', store=True, readonly=True)

	@api.depends('order_line')
	def _com_delivered_amount(self):
		for item in self:
			if item.order_line:
				item.total_delivered_price = sum(item.order_line.mapped('delivered_total_price'))
				item.total_delivered_nuat_price = sum(item.order_line.mapped('delivered_nuat_total_price'))
			else:
				item.total_delivered_price = 0
				item.total_delivered_nuat_price = 0
	
	
	@api.depends('picking_ids')
	def _compute_niit_urtug(self):
		for item in self:
			if item.picking_ids:
				item.niit_urtug = sum(item.picking_ids.filtered(lambda r: r.state == 'done').move_ids.mapped('niit_urtug'))
			else:
				item.niit_urtug = 0
	
	def button_niit_urtug(self):
		sales = self.env['sale.order'].search([('id','!=', False)])
		for sale in sales:
			if sale.picking_ids:
				sale.niit_urtug = sum(sale.picking_ids.filtered(lambda r: r.state == 'done').move_ids.mapped('niit_urtug'))
			else:
				sale.niit_urtug = 0


	@api.depends('invoice_date')
	def _compute_payment_date(self):
		for item in self:
			item.payment_date = item.invoice_date + timedelta(days=3)

	@api.depends('supply_date','picking_date_done')
	def _compute_time_delay(self):
		today = datetime.now().date()
		for item in self:
			if item.supply_date and today:
				# secs = (item.supply_date - item.picking_date_done.date()).total_seconds() tur haav
				if item.picking_ids.filtered(lambda r: r.state != 'done'):
					secs = (item.supply_date - today).total_seconds()
					item.time_delay = (secs/3600)/24
				else:
					item.time_delay = 0

	@api.depends('pre_percent', 'amount_total')
	def _compute_pre_amount_all(self):
		for item in self:
			if item.amount_total and item.pre_percent:
				item.pre_amount_all = item.amount_total * item.pre_percent / 100
			else:
				item.pre_amount_all = 0

	def send_emails(self, subject, body, attachment_ids, is_partner_mail):
		mail_obj = self.env['mail.mail'].sudo().create({
			# 'email_from': self.env.user.email_formatted,
			'email_from': self.company_id.email,
			'email_to': self.partner_mail if is_partner_mail else self.partner_id.email,
			'reply_to': self.env.user.email_formatted,
			'subject': subject,
			'body_html': '%s' % body,
			'attachment_ids': attachment_ids
		})
		mail_obj.send()

	def action_to_sent_mail_sale_order_mn(self):
		if self.file_type == 'pdf':
			reportname = 'sale.sale_order_s'			
			report = request.env['ir.actions.report']._get_report_from_name(reportname)
			context = dict(request.env.context)
			data = self.env.context
			docids = self.id
			if report.populating_ms_word_template:
				if data.get('options'):
					data.update(json.loads(data.pop('options')))
				if data.get('context'):
					data['context'] = json.loads(data['context'])
					if data['context'].get('lang'):
						del data['context']['lang']
					context.update(data['context'])
				datas = request.env[report.model].search([('id', '=', docids)])
				if report.type_export == 'pdf':
					pdf = report.with_context(context).render_doc_doc(datas, data=data)[0]
					pdfhttpheaders = [
						('Content-Type','application/pdf'),
						('Content-Length', len(pdf))
					]
					attachment_id = self.env['ir.attachment'].search([('res_id','=',docids),('res_model','=',report.model)], limit=1)
					if not self.partner_mail:
						# self.env.user.send_chat(self.mail_html, [self.partner_id], with_mail=True, subject_mail=self.mail_title, attachment_ids=[attachment_id.id])
						self.send_emails(subject=self.mail_title, body=self.mail_html, attachment_ids=[attachment_id.id], is_partner_mail=False)
					else:
						self.send_emails(subject=self.mail_title, body=self.mail_html, attachment_ids=[attachment_id.id], is_partner_mail=True)
					return request.make_response(pdf, headers=pdfhttpheaders)


	def action_to_sent_mail_sale_order_s(self):
		if self.file_type == 'pdf':
			reportname = 'sale.sale_order_mn'
			report = request.env['ir.actions.report']._get_report_from_name(reportname)
			context = dict(request.env.context)
			data = self.env.context
			docids = self.id
			if report.populating_ms_word_template:
				if data.get('options'):
					data.update(json.loads(data.pop('options')))
				if data.get('context'):
					data['context'] = json.loads(data['context'])
					if data['context'].get('lang'):
						del data['context']['lang']
					context.update(data['context'])
				datas = request.env[report.model].search([('id', '=', docids)])
				if report.type_export == 'pdf':
					pdf = report.with_context(context).render_doc_doc(datas, data=data)[0]
					pdfhttpheaders = [
						('Content-Type','application/pdf'),
						('Content-Length', len(pdf))
					]
					attachment_id = self.env['ir.attachment'].search([('res_id','=',docids),('res_model','=',report.model)], limit=1)
					if not self.partner_mail:
						# self.env.user.send_chat(self.mail_html, [self.partner_id], with_mail=True, subject_mail=self.mail_title, attachment_ids=[attachment_id.id])
						self.send_emails(subject=self.mail_title, body=self.mail_html, attachment_ids=[attachment_id.id], is_partner_mail=False)
					else:
						self.send_emails(subject=self.mail_title, body=self.mail_html, attachment_ids=[attachment_id.id], is_partner_mail=True)
					return request.make_response(pdf, headers=pdfhttpheaders)
	
	def action_to_sent_mail_sale_order_zarlaga(self):
		if self.file_type == 'pdf':
			reportname = 'sale.order_zarlaga'
			report = request.env['ir.actions.report']._get_report_from_name(reportname)
			context = dict(request.env.context)
			data = self.env.context
			docids = self.id
			if report.populating_ms_word_template:
				if data.get('options'):
					data.update(json.loads(data.pop('options')))
				if data.get('context'):
					data['context'] = json.loads(data['context'])
					if data['context'].get('lang'):
						del data['context']['lang']
					context.update(data['context'])
				datas = request.env[report.model].search([('id', '=', docids)])
				if report.type_export == 'pdf':
					pdf = report.with_context(context).render_doc_doc(datas, data=data)[0]
					pdfhttpheaders = [
						('Content-Type','application/pdf'),
						('Content-Length', len(pdf))
					]
					attachment_id = self.env['ir.attachment'].search([('res_id','=',docids),('res_model','=',report.model)], limit=1)
					if not self.partner_mail:
						# self.env.user.send_chat(self.mail_html, [self.partner_id], with_mail=True, subject_mail=self.mail_title, attachment_ids=[attachment_id.id], is_partner_mail=False)
						self.send_emails(subject=self.mail_title, body=self.mail_html, attachment_ids=[attachment_id.id], is_partner_mail=False)
					else:
						self.send_emails(subject=self.mail_title, body=self.mail_html, attachment_ids=[attachment_id.id], is_partner_mail=True)
					return request.make_response(pdf, headers=pdfhttpheaders)


	@api.depends('order_line','order_line.price_unit', 'state','pre_percent')
	def _compute_total_confirmed_amount(self):
		for item in self:
			item.total_amount_text = self.env['sale.order']._digit_to_text(int(item.pre_amount_all))

	def action_next_stage(self):
		res = super(SaleOrder, self).action_next_stage()
		if self.flow_line_id.state_type == 'done':
			self.picking_ids.write({'eh_barimt_user_id': self.create_uid.id})
		if self.flow_line_id.state_type == 'done' and self.user_id.id != self.env.user.id:
			raise UserError('Борлуулалтын захиалга болгох хэрэглэгч %s' % self.user_id.name)
		return res

	def action_draft_stage(self):
		stages = self.history_flow_ids.mapped('flow_line_id.name')
		if 'Үнийн санал' in stages:
			flow_line_id = self.env['dynamic.flow.line'].search([('flow_id', '=', self.flow_id.id), ('name', '=', 'Үнийн санал')], limit=1)
		else:
			flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.action_draft()
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'so_id', self)
		else:
			raise UserError(('You are not draft user'))

	def send_chat_for_expiration(self):
		so_p = self.env['sale.order'].search([])
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('sale.action_quotations_with_onboarding').id
		for p in so_p:
			if p.quotation_end_date:
				date_diff = (p.quotation_end_date - date.today()).days
				if 0 < date_diff <= 10:
					html = u"""<b><a target="_blank"  href=%s/web#action=%s&id=%s&view_type=form&model=sale.order>%s</a></b>,""" % (base_url, action_id, p.id, p.name)
					html += u'<b> Үнийн санал илгээх хугацаа дуусахад </b><i style="color: red">%s</i> хоног үлдлээ</br>' % (date_diff)
					self.env.user.send_chat(html, p.user_id.partner_id)

class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"

	sale_price_calculator_line_id = fields.Many2one('sale.price.calculator.line', string='Sale Price Calculator Line ID')
	pr_id = fields.Many2one('purchase.request', 'ХА хүсэлт дугаар')
	pre_payment_amount = fields.Float(string='Урьдчилгаа төлбөр', compute='_compute_prepayment', store=True)
	pre_payment_percent = fields.Float(string='Урьдчилгаа хувь')
	balance_amount = fields.Float(string='Үлдэгдэл дүн', compute='_compute_prepayment', store=True)
	date_order = fields.Datetime(related='order_id.date_order', string='Захиалгын огноо', store=True)
	categ_id = fields.Many2one(related='product_id.categ_id', string='Барааны ангилал', store=True)
	sale_price_buyer_id = fields.Many2one(related='sale_price_calculator_line_id.buyer_id', string='Supplier', store=True)
	sale_price_currency_id = fields.Many2one(related='sale_price_calculator_line_id.currency_id', string='Curreny/sale price/', store=True)

	delivered_total_price = fields.Float(string='Захиалгын хүргэгдсэн дүн', compute='_compute_delivered_amount', store=True)
	delivered_nuat_total_price = fields.Float(string='Захиалгын хүргэгдсэн дүн/НӨАТ/', compute='_compute_delivered_amount', store=True)

	@api.depends('qty_delivered','price_unit')
	def _compute_delivered_amount(self):
		for item in self:
			if item.qty_delivered!=0:
				item.delivered_total_price = item.price_unit * item.qty_delivered
				item.delivered_nuat_total_price = item.delivered_total_price/1.1*0.1
			else:
				item.delivered_total_price = 0
				item.delivered_nuat_total_price = 0


	@api.depends('pre_payment_percent','product_uom_qty','price_unit','price_total','pre_payment_amount','balance_amount')
	def _compute_prepayment(self):
		for item in self:
			if item.pre_payment_percent and item.price_total:
				item.pre_payment_amount = (item.product_uom_qty*item.price_unit) * item.pre_payment_percent/100
				item.balance_amount = item.price_total - item.pre_payment_amount
			else: 
				item.pre_payment_amount = 0
				item.balance_amount = item.price_total

class SaleOrderPlan(models.Model):
	_name = "sale.order.plan"
	_description = 'Sale Order Plan'
	_order = 'date asc'

	sale_id = fields.Many2one('sale.order', 'Sale ID', ondelete='cascade')
	date = fields.Date('Огноо', required=True)
	amount = fields.Float('Дүн', required=True)
	paid_amount = fields.Float('Төлсөн дүн', readonly=True)
	unpaid_amount = fields.Float('Үлдэгдэл дүн', readonly=True)
	date_diff = fields.Integer(compute="_compute_date_diff", store=True)
	state = fields.Selection([('draft', 'Draft'),('check', 'Check'),('done', 'Done'),('over','Over')], 'Төлөв', default='draft')
	sale_order_plan_line = fields.One2many('sale.order.plan.line', 'plan_id')
	partner_id = fields.Many2one('res.partner', 'Харилцагч', related='sale_id.partner_id', store=True)

	@api.depends('date','date_diff','paid_amount','amount')
	def _compute_date_diff(self):
		for record in self:
			if record.state != 'done':
				record.date_diff = (record.date - date.today()).days if record.date else 0
			record.write({'state': 'draft'})
			if record.date_diff and 0 <= record.date_diff <= 30 or record.paid_amount:
				record.write({'state': 'check'})
			elif record.date_diff < 0:
				record.write({'state': 'over'})
			if record.paid_amount and record.paid_amount == record.amount:
				record.write({'state': 'done'})
	
	@api.onchange('sale_order_plan_line')
	def update_numbers(self):
		for item in self:
			item.paid_amount = sum(item.sale_order_plan_line.mapped('amount'))
			item.unpaid_amount = item.amount - item.paid_amount

class SaleOrderPlanLine(models.Model):
	_name = "sale.order.plan.line"
	_description = 'Sale Order Plan Line'

	plan_id = fields.Many2one('sale.order.plan', 'Plan ID', ondelete='cascade')
	sale_id = fields.Many2one('sale.order', 'Sale ID', related='plan_id.sale_id')
	date = fields.Date('Огноо', required=True)
	amount = fields.Float('Дүн', required=True)

class ProductProduct(models.Model):
	_inherit = 'product.product'

	sol_ids = fields.One2many('sale.order.line', 'product_id', 'Борлуулалтын түүх', 
						#    compute='com_sol_ids'
						   )

	def com_sol_ids(self):
		for item in self:
			if self.env.context.get('allowed_company_ids',False):
				item.sol_ids = self.env['sale.order.line'].search([('product_id','=',item.id),('company_id','in',self.env.context.get('allowed_company_ids',False))])
			else:
				item.sol_ids = False


class ProductTemplate(models.Model):
	_inherit = 'product.template'

	sol_tmpl_ids = fields.One2many('sale.order.line', related='product_variant_ids.sol_ids', readonly=True)