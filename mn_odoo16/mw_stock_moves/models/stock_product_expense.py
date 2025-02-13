
# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
import pytz

from datetime import datetime, time
import collections
import time
import xlsxwriter
from io import BytesIO
import base64
try:
	# Python 2 support
	from base64 import encodestring
except ImportError:
	# Python 3.9.0+ support
	from base64 import encodebytes as encodestring
	
from datetime import datetime, timedelta

import logging
_logger = logging.getLogger(__name__)

# Гүйлгээний утга
class MnTransactionValue(models.Model):
	_name = 'mn.transaction.value'
	_order = 'name'
	_description = 'Transaction value'
	_inherit = ['mail.thread','analytic.mixin']
	

	@api.depends('code','name')
	def name_get(self):
		result = []
		for s in self:
			name = u""+s.code +'. '+ s.name
			result.append((s.id, name))
		return result

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|',  ('name', operator, name), ('code', operator, name)]
		tv = self.search(domain + args, limit=limit)
		return tv.name_get()

	active = fields.Boolean(u'Идэвхитэй', default=True, tracking=True)
	name = fields.Char(u'Гүйлгээний утга', required=True, tracking=True)
	code = fields.Char(u'Гүйлгээний код', required=True, tracking=True)
	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, tracking=True)
	warehouse_id = fields.Many2many('stock.warehouse', 'transaction_value_warehouse_rel', 
		column1='transaction_id', column2='warehouse_id', string=u'Хамааралтай агуулах', tracking=True)
	account_id = fields.Many2one('account.account', u'Данс', copy=False, tracking=True)
	categ_ids = fields.Many2many('product.category', string='Барааны ангилал', copy=False, tracking=True)
	product_ids = fields.Many2many('product.product', string='Барааны нэрc', copy=False, tracking=True)
	is_employee = fields.Boolean(u'Ажилтан заавал сонгох', default=False, tracking=True)
	is_partner = fields.Boolean(u'Харилцагч заавал сонгох', default=False, tracking=True)
	account_analytic_id = fields.Many2one('account.analytic.account', u'Аналитик данс', copy=False, tracking=True)
	flow_ids = fields.Many2many('dynamic.flow', 'mn_transaction_value_dynamic_flow_rel', 'transaction_id', 'flow_id', u'Хамаарах Урсгал Тохиргоо', tracking=True)
	is_list_pirce_view = fields.Boolean(u'Зарах Үнэ Харуулах', default=False, tracking=True)
	available_product = fields.Boolean(string=u'Үлдэгдэлтэй барааг харуулах', default=False, tracking=True)
	choose_fleet = fields.Boolean(string='Техник сонгох', default=False)

	def unlink(self):
		for s in self:
			move_id = self.env['stock.product.other.expense'].search([('transaction_value_id', '=', s.id)])
			if move_id:
				raise UserError((u'Шаардах хуудас үүссэн гүйлгээний утга устгаж болохгүй!'))
		return super(MnTransactionValue, self).unlink()


class StockPicking(models.Model):
	_inherit = 'stock.picking'

	other_expense_id = fields.Many2one('stock.product.other.expense', 'Other expense ID')

	def action_view_other_exepnse_id_mw(self):
		view = self.env.ref('mw_stock_moves.stock_product_other_expense_form_view')
		return {
			'name': 'Шаардах',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'stock.product.other.expense',
			'views': [(view.id, 'form')],
			'view_id': view.id,
			# 'target': 'new',
			'res_id': self.other_expense_id.id,
			'context': dict(
				self.env.context
			),
		}

	def action_cancel(self):
		res = super(StockPicking, self).action_cancel()
		for item in self:
			if item.other_expense_id and item.other_expense_id.state!='cancelled' and not item.backorder_id and item.picking_type_id.code == 'outgoing':
				item.other_expense_id.action_cancel_stage()
		return res

class SelectedOtherExpense(models.TransientModel):
	_name = "selected.other.expense.next"
	_description = "selected other expense open"

	def _default_other_expense(self):
		other_ids = self.env['stock.product.other.expense'].browse(self._context['active_ids']).filtered(lambda r: r.state_type not in ['done','cancel'])
		return [(6, 0, other_ids.ids)]
	other_expense_ids = fields.Many2many('stock.product.other.expense', string='Other expense', default=_default_other_expense)

	def multi_next_stage(self):
		other_expense_ids = self.env['stock.product.other.expense'].browse(self._context['active_ids']).filtered(lambda r: r.state_type not in ['done','cancel'])
		for other_expense in other_expense_ids:
			other_expense.action_next_stage()

class StockProductOtherExpense(models.Model):
	_name = 'stock.product.other.expense'
	_description = 'Stock Product Other Expense'
	_order = 'date desc'
	_inherit = ['mail.thread','analytic.mixin']

	# ==================================
	def _get_dynamic_flow_line_id(self):
		return self.flow_find()

	def _get_default_flow_id(self):
		search_domain = []
		search_domain.append(('model_id.model','=','stock.product.other.expense'))
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

	flow_id = fields.Many2one('dynamic.flow', string='Request Config', tracking=True,
		default=_get_default_flow_id,
		 copy=True, required=True, domain="[('model_id.model', '=', 'stock.product.other.expense')]")

	flow_line_id = fields.Many2one('dynamic.flow.line', string='State', tracking=True, index=True,
		default=_get_dynamic_flow_line_id,
		 copy=False, domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'stock.product.other.expense')]")
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='State', store=True)
	flow_line_next_id = fields.Many2one('dynamic.flow.line', 'Request line next', compute='_compute_flow_line_id', store=True)
	flow_line_back_id = fields.Many2one('dynamic.flow.line', 'Request line back', compute='_compute_flow_line_id')
	is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
	state_type = fields.Char(string='State type', compute='_compute_state_type', store=True)
	confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True)
	choose_fleet = fields.Boolean(string='Техник сонгох', related='transaction_value_id.choose_fleet', readonly=True)

	@api.onchange('analytic_distribution')
	def _onchange_analytic_distribution(self):
		if self.analytic_distribution:
			for line in self.product_expense_line:
				line.analytic_distribution = self.analytic_distribution

	@api.depends('flow_line_id', 'flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
			user_id = item.create_uid
			ooo = item.flow_line_next_id._get_flow_users(item.branch_id, user_id.department_id, user_id)
			temp_users = ooo.ids if ooo else []
			item.confirm_user_ids = [(6, 0, temp_users)]

	@api.depends('flow_line_id')
	def _compute_flow_line_id(self):
		for item in self:
			item.flow_line_next_id = item.flow_line_id._get_next_flow_line()
			item.flow_line_back_id = item.flow_line_id._get_back_flow_line()


	@api.depends('flow_line_id.stage_id')
	def _compute_flow_line_id_stage_id(self):
		for item in self:
			item.stage_id = item.flow_line_id.stage_id


	@api.depends('flow_line_id.is_not_edit')
	def _compute_is_not_edit(self):
		for item in self:
			item.is_not_edit = item.flow_line_id.is_not_edit


	@api.depends('flow_line_id')
	def _compute_state_type(self):
		for item in self:
			item.state_type = item.flow_line_id.state_type

	def flow_find(self, domain=[], order='sequence'):
		search_domain = []
		if self.flow_id:
			search_domain.append(('flow_id','=',self.flow_id.id))
		search_domain.append(('flow_id.model_id.model','=','stock.product.other.expense'))
		return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1).id

	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.flow_line_id = self.flow_find()
		else:
			self.flow_line_id = False

	def print_word(self):
		# report = self.env['ir.actions.report']._get_report_from_name('test')
		# report=self.env['ir.actions.report'].browse(2278)
		report=self.env['ir.actions.report'].search([('model','=','stock.product.other.expense')],limit=1)
		context = dict(self.env.context)
		datas = self #.env['stock.product.other.expense'].search([('id', '=', 743)])
		data={}
		template_name='shaardah'
		file_name = self.name+'.pdf'
		pdf = report.with_context(context).render_doc_doc(datas, data=data)[0]
		options = {
			'page-size': 'A4',
			'encoding': "UTF-8",
		} 
		report_type='.pdf'
		out = encodestring(pdf)
		excel_id = self.env['report.pdf.output'].create({'data': out, 'name': template_name+report_type})
		 
		return {
			'type' : 'ir.actions.act_url',
			'url': "web/content/?model=report.pdf.output&id=" + str(excel_id.id) + "&filename_field=filename&field=data&filename=" + excel_id.name,
			'target': 'new',
		}         
		
	def check_price(self):
		for item in self:
			zero_price_lines = item.product_expense_line.filtered(lambda r: r.product_standard_price == 0 or r.product_total_price == 0)
			if zero_price_lines:
				zero_price_lines.onchange_product_price()
				zero_price_lines.compute_total_price()
		
	def action_next_stage(self):
		no_qty_lines = self.product_expense_line.filtered(lambda r: r.available_qty == 0)
		self.check_price()
		if no_qty_lines:
			raise UserError(('Үлдэгдэлгүй бараа гаргах боломжгүй.\n{0}'.format(', '.join(no_qty_lines.mapped('product_id.display_name')))))
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if next_flow_line_id:
			user_id = self.env['res.users'].sudo().search([('partner_id','=',self.partner_id.id)]) or self.create_uid
			if next_flow_line_id._get_check_ok_flow(self.branch_id, self.sudo().user_id.department_id, self.create_uid):
				if next_flow_line_id.state_type == 'sent':
					self.action_to_send()
				elif next_flow_line_id.state_type == 'done':
					self.action_to_confirm()
				if next_flow_line_id.state_type!='done':
					self.update_available_qty()

				self.flow_line_id = next_flow_line_id
				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'shaardah_id', self)
				# self.send_chat_employee(self.sudo().partner_id)
				# if self.flow_line_next_id:
				# 	send_users = self.flow_line_next_id._get_flow_users(self.branch_id, self.sudo().user_id.department_id, user_id)
				# 	if send_users:
				# 		self.send_chat_next_users(send_users.mapped('partner_id'))
			else:
				con_user = next_flow_line_id._get_flow_users(self.branch_id, False, self.create_uid)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)
				# raise UserError('Та батлах хэрэглэгч биш байна')

	def action_back_stage(self):
		back_flow_line_id = self.flow_line_id._get_back_flow_line()
		if back_flow_line_id:
			if back_flow_line_id._get_check_ok_flow(self.branch_id, self.sudo().user_id.department_id, self.sudo().partner_id.user_id):
				if back_flow_line_id.state_type == 'sent':
					self.state = 'sent'
				self.flow_line_id = back_flow_line_id
				self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'shaardah_id', self)
				# self.send_chat_employee(self.sudo().partner_id)
			else:
				raise UserError(_('You are not back user'))

	def action_cancel_stage(self):

		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow(self.branch_id, self.sudo().user_id.department_id, self.sudo().partner_id.user_id):
			self.flow_line_id = flow_line_id

			# History uusgeh
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'shaardah_id', self)
			# chat ilgeeh
			# self.send_chat_employee(self.sudo().partner_id)
			self.action_to_cancel()
		else:
			raise UserError(_('You are not cancel user'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow(self.branch_id, self.sudo().user_id.department_id, self.sudo().user_id):
			self.flow_line_id = flow_line_id
			# History uusgeh
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'shaardah_id', self)
		else:
			raise UserError(_('You are not draft user'))



	def send_chat_next_users(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data']._xmlid_lookup('mw_stock_moves.action_stock_product_other_expense')[2]
		html = u'<b>Бараа материалын Шаардах хуудас</b><br/><i style="color: red">%s</i> ажилтны үүсгэсэн </br>'%(self.create_uid.partner_id.name or self.partner_id.name)
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=stock.product.other.expense&action=%s>%s</a></b> дугаартай шаардах хуудас батална уу"""% (base_url,self.id,action_id,self.name)
		self.flow_line_id.send_chat(html, partner_ids)

		# +start activity
		users = self.env['res.users'].search([('partner_id', 'in', partner_ids.ids)])
		if users:
			self.env['dynamic.flow.history'].done_activity('stock.product.other.expense', self.id)
			self.env['dynamic.flow.history'].create_activity(html, users, 'stock.product.other.expense', self.id)
		# -end activity

	def send_chat_employee(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_stock_moves.action_stock_product_other_expense').id
		# action_id = self.env['ir.model.data']._xmlid_lookup('mw_stock_moves.action_stock_product_other_expense')[2]
		html = u'<b>Бараа материалын Шаардах хуудас</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>'%(self.create_uid.partner_id.name or self.partner_id.name)
		html += u"""<b><a target="_blank"  href=%s/web#id=%s&view_type=form&model=stock.product.other.expense&action=%s>%s</a></b> дугаартай шаардах хуудас <b>%s</b> төлөвт орлоо"""%\
				(base_url, self.id, action_id, self.name, state)
		self.flow_line_id.send_chat(html,partner_ids)

	# =========================

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	###### name-n readonly tur avav#############
	name = fields.Char(u'Дугаар', copy=False, readonly=True) 
	company_id = fields.Many2one('res.company', 'Компани', default=lambda self: self.env.user.company_id)
	branch_id = fields.Many2one('res.branch', 'Салбар', default=lambda self: self.env.user.branch_id, required=True)
	description = fields.Text(u'Description',
		states={'sent': [('readonly', True)],'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
	date = fields.Datetime('Үүсгэсэн огноо', default=fields.Datetime.now, readonly=True)
	date_required = fields.Date(u'Товлосон огноо', required=True,
		states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})

	warehouse_id = fields.Many2one('stock.warehouse', 'Агуулах', required=True, copy=True,
		states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
	location_id = fields.Many2one(related='warehouse_id.lot_stock_id', readonly=True)

	user_id = fields.Many2one('res.users', 'Хэрэглэгч', default=_get_user, readonly=True)
	validator_id = fields.Many2one('res.users', 'Батласан Хэрэглэгч', readonly=True, copy=False,)

	partner_id = fields.Many2one('res.partner', u'Шаардах бичсэн ажилтан', default=lambda self: self.env.user.partner_id, copy=False,
		help=u"Хэрэв ажилтан сонгогдвол тухайн ажилтаны 'Ашиглалтанд байгаа хангамжийн материал'-ын бүртгэлд бүртгэгдэнэ.",
		states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]}, domain=([('employee','=',True)]))
	# Санхүү
	account_id = fields.Many2one('account.account', u'Данс', copy=False,
		states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]},)
	account_analytic_id = fields.Many2one('account.analytic.account', u'Аналитик данс', copy=False,
		states={'done': [('readonly', True)]}, )
	account_analytic_ids = fields.Many2one('account.analytic.account', u'Аналитик данс', copy=False,
		states={'done': [('readonly', True)]}, )
	# branch_id = fields.Many2one('res.branch', u'Салбар', copy=True, required=False,
	# 	states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})

	department_id = fields.Many2one('hr.department', u'Хэлтэс/нэгж', copy=True, help=u"Хэрэв хэлтэс дээрх зардал бол сонгоно", required=True)

	# warehouse_ids = fields.Many2many(related="user_id.warehouse_ids", string='Warehouses', readonly=True, )

	employee_id = fields.Many2one('hr.employee', u'Ажилтан',
		states={'sent': [('readonly', True)],'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
	
	date_user = fields.Datetime(u'User Date', readonly=True, copy=False,)
	date_validator = fields.Datetime(u'Батласан Огноо', readonly=True, copy=False,)

	product_expense_line = fields.One2many('stock.product.other.expense.line', 'parent_id', string=u'Expense line', copy=True,
		states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]},
		help=u"Бараа зарлагадах мэдээлэл")

	transaction_value_id = fields.Many2one('mn.transaction.value', u'Зарлага гүйлгээний утга',
		states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})

	# categ_ids = fields.Many2many(related="transaction_value_id.categ_ids", string='Ангилал', readonly=True, )
	categ_ids = fields.Many2many('product.category', string='Ангилал', readonly=True, compute='_compute_transaction_categ')
	product_ids = fields.Many2many(related="transaction_value_id.product_ids", string='Барааны нэрс', readonly=True, )
	available_product = fields.Boolean(related="transaction_value_id.available_product", string='Үлдэгдэлтэй барааг харуулах', readonly=True, )
	expense_picking_ids = fields.One2many('stock.picking', 'other_expense_id', u'Зарлага хийсэн хөдөлгөөнүүд', readonly=True, copy=False,)
	expense_picking_count = fields.Integer(u'Зарлагын баримтын тоо', readonly=True, compute='_comute_expense_picking_count')

	state = fields.Selection([
			('cancelled', 'Cancelled'),
			('draft', 'Draft'),
			('sent', 'Sent'),
			('confirmed', 'Confirmed'),
			('done', 'Done')],
			default='draft', string='State', tracking=True)
	history_flow_ids = fields.One2many('dynamic.flow.history', 'shaardah_id', 'Урсгалын түүхүүд')
	history_ids = fields.One2many('stock.product.other.expense.history', 'expense_id', 'Түүхүүд')
	is_employee = fields.Boolean(related='transaction_value_id.is_employee', readonly=True)
	is_partner = fields.Boolean(related='transaction_value_id.is_partner', readonly=True)
	is_list_pirce_view = fields.Boolean(related='transaction_value_id.is_list_pirce_view', readonly=True)
	import_product_ids = fields.Many2many('product.product', string="Импортлох Бараанууд")
	import_employee_ids = fields.Many2many('hr.employee', string="Импортлох Ажилтанууд Буруу") # Хасагдах код
	import_partner_ids = fields.Many2many('res.partner', string="Импортлох Ажилтанууд", domain=([('employee','=',True)]))
	import_qty = fields.Float('Импортлох тоо хэмжээ', default=1)
	product_id = fields.Many2one(related='product_expense_line.product_id', string='Бараа')

	@api.depends('transaction_value_id.categ_ids')
	def _compute_transaction_categ(self):
		if self.transaction_value_id:
			if self.transaction_value_id.categ_ids:
				self.categ_ids = self.transaction_value_id.categ_ids
			else:
				self.categ_ids = self.env['product.category'].search([('possible_to_choose','=',True)]).ids
		else:
			self.categ_ids = False

	def set_account_analytic(self):
		self.ensure_one()
		self.product_expense_line.write({
			'account_id': self.account_id.id,
			'analytic_distribution': self.analytic_distribution,
			})

	def change_history(self):
		obj_min = 5000
		obj = self.env['dynamic.flow.history']
		objs = self.env['stock.product.other.expense.history'].search([
			('create_ok','=',False),
			], limit=obj_min)
		i = len(objs)

		for item in objs:
			obj_id = obj.create({
				'user_id': item.user_id.id,
				'shaardah_id': item.expense_id.id,
				'date': item.date,
				'flow_line_id': item.flow_line_id.id,
			})
			obj_id.create_date = item.create_date
			obj_id.create_uid = item.create_uid.id
			item.create_ok = True
			obj.compute_spend_time('shaardah_id', item.expense_id)
			_logger.info('flow history shiljuuleh %s of %s'%(i,obj_min))
			i -= 1

	@api.depends('expense_picking_ids')
	def _comute_expense_picking_count(self):
		for item in self:
			item.expense_picking_count = len(item.expense_picking_ids)

	@api.onchange('partner_id')
	def onchange_department_id_partner(self):
		for item in self:
			emp_obj = self.env['hr.employee']
			if item.partner_id:
				emp_id = emp_obj.search([('partner_id','=',item.partner_id.id),('company_id','=',item.company_id.id)])
				if emp_id:
					# for emp in emp_id:
					item.department_id = emp_id[0].department_id.id


	def action_employee_import(self):
		if not self.import_product_ids:
			raise UserError(u'Импортлох бараагаа оруулна уу!!')

		if self.is_employee:
			if not self.import_partner_ids:
				raise UserError(u'Импортлох ажилтанаа оруулна уу!!')
			for item in self.import_product_ids:
				for emp in self.import_partner_ids:
					line_id = self.env['stock.product.other.expense.line'].create({
						'parent_id': self.id,
						'res_partner_id': emp.id,
						'product_id': item.id,
						'account_id': self.transaction_value_id.account_id.id if self.transaction_value_id and self.transaction_value_id.account_id else False,
						'qty': self.import_qty or 1,
						})
					if self.account_analytic_ids:
						line_id.account_analytic_ids = [(6,0,self.account_analytic_ids.ids)]
			self.import_partner_ids = False

		else:
			for item in self.import_product_ids:
				line_id = self.env['stock.product.other.expense.line'].create({
					'parent_id': self.id,
					'res_partner_id': self.partner_id.id,
					'product_id': item.id,
					'account_id': self.transaction_value_id.account_id.id if self.transaction_value_id and self.transaction_value_id.account_id else False,
					'qty': self.import_qty or 1
					})
				if self.account_analytic_ids:
					line_id.account_analytic_ids = [(6,0,self.account_analytic_ids.ids)]
		self.import_product_ids = False
		self.import_qty = 1


	def update_last_date(self):
		expense_line_obj = self.env['stock.product.other.expense.line']
		for item in self.product_expense_line:
			partner_id = item.sudo().res_partner_id or self.sudo().partner_id
			prod_search = ' prl.product_id=%s '%item.product_id.id
			if len(item.product_id.product_tmpl_id.product_variant_ids)>1:
				prod_search = ' prl.product_id in %s '%(str(tuple(item.product_id.product_tmpl_id.product_variant_ids.ids)))
			query ="""
			SELECT
				pr.date_required
				FROM stock_product_other_expense_line AS prl
				LEFT JOIN stock_product_other_expense AS pr on (pr.id=prl.parent_id)
				WHERE %s and prl.res_partner_id=%s and pr.id!=%s
				ORDER BY pr.date_required DESC
				LIMIT 1
				"""%(prod_search,partner_id.id,self.id)
			self.env.cr.execute(query)
			records = self.env.cr.fetchall()
			if records:
				item.last_date = records[0][0]

	def update_available_qty(self):
		for item in self.product_expense_line:
			item.update_available_qty()

	@api.depends('product_expense_line')
	def _methods_compute(self):
		# Нийт тоог олгох
		for obj in self:
			tot = 0
			for line in obj.product_expense_line:
				tot += line.qty * line.price_unit
			obj.total_amount = tot

	total_amount = fields.Float(compute=_methods_compute, store=True, string=u'Нийт дүн')

	# asset_category_id = fields.Many2one(comodel_name='account.asset.category', string=u'Хөрөнгийн ангилал', domain=[('is_consumable_product','=',True)])

	#
	def write(self, vals):
		# res = super(StockProductOtherExpense, self).write(vals)
		# p_ids = [ l.product_id for l in self.product_expense_line ]
		# dup_ids = [item for item, count in collections.Counter(p_ids).items() if count > 1]
		# if dup_ids:
		#     names = [d.name for d in dup_ids]
		#     raise UserError(_(u'"%s" бараанууд давхар бүртгэгдсэн байна!' % (', '.join(names))))
		self.check_price()
		return super(StockProductOtherExpense, self).write(vals)

	def unlink(self):
		for s in self:
			if s.state_type not in ['draft','cancel']:
				raise UserError(_(u'Ноорог болон Цуцлагдсан төлөвтэй бичлэгийг устгаж болно!'))
		return super(StockProductOtherExpense, self).unlink()

	@api.onchange('transaction_value_id')
	def onchange_transaction_value_id(self):
		if self.transaction_value_id:
			# self.description = self.transaction_value_id.name
			self.account_id = self.transaction_value_id.account_id.id
			# if self.transaction_value_id.analytic_distribution:
			#     self.analytic_distribution=self.transaction_value_id.analytic_distribution

	@api.onchange('department_id')
	def onchange_department_id(self):
		if self.department_id:
			# self.description = self.transaction_value_id.name
			distribution_model =self.env['account.analytic.distribution.model'].search([('department_id','=',self.department_id.id),
																						('company_id','=',self.env.company.id)],limit=1)
			self.analytic_distribution=distribution_model.analytic_distribution


	def action_to_draft(self):
		if self.expense_picking_ids:
			self.expense_picking_ids.filtered(lambda r: r.picking_type_id.code == 'outgoing').action_cancel()
			self.state = 'draft'
		elif not self.expense_picking_ids:
			self.state = 'draft'
		else:
			raise UserError(_(u'Хөдөлгөөн цуцлах боломжгүй, цуцлах шаардлагатай бол хөдөлгөөнийг эхлээд цуцлуулна уу!'))

	@api.onchange('user_id')
	def onchange_user(self):
		if self.user_id:
			emp = self.env['hr.employee'].sudo().search([('user_id','=',self.user_id.id)], limit=1)
			if emp:
				self.employee_id = emp.id
				self.department_id = emp.sudo().department_id.id
				self.onchange_employee_id()

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.department_id = self.sudo().employee_id.department_id.id
			self.partner_id = self.sudo().employee_id.partner_id.id
			self.branch_id = self.sudo().employee_id.user_id.branch_id.id or self.env.user.branch_id.id

	@api.onchange('asset_category_id')
	def onchange_asset_category_id(self):
		if self.asset_category_id:
			self.account_id = self.asset_category_id.account_asset_id.id
		else:
			self.account_id = False

	def action_to_cancel(self):
		self.state = 'cancelled'
		self.expense_picking_ids.filtered(lambda r: r.picking_type_id.code == 'outgoing').action_cancel()

	# CUSTOM

	def action_to_print(self):
		model_id = self.env['ir.model'].search([('model','=','stock.product.other.expense')], limit=1)
		template = self.env['pdf.template.generator'].search([('model_id','=',model_id.id)], limit=1)

		if template:
			res = template.print_template(self.id)
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))


	def action_to_send(self):
		if self.product_expense_line:
			_logger.info(u'-***********-NUMBER--*************%d %s \n' % (self.id, self.name))
			if not self.name:
				self.name = self.env['ir.sequence'].next_by_code('stock.product.other.expense')
			self.user_id = self.env.user.id
			self.date_user = datetime.now()
			self.state = 'sent'
		else:
			raise UserError(_(u'Бараа зарлагадах мэдээллийг оруулна уу!'))

		tran_value = ""
		if self.transaction_value_id:
			tran_value = self.transaction_value_id.name +', '
		if self.description:
			tran_value += self.description
		self.state = 'sent'

	def get_prepare_stock_move_line(self, line, sp_id, price_unit, desc, dest_loc):
		return {
				'name': desc,
				'picking_id': sp_id.id,
				'product_id': line.product_id.id,
				'product_uom': line.product_id.uom_id.id,
				'product_uom_qty': line.qty,
				'price_unit': price_unit,
				'location_id': self.warehouse_id.lot_stock_id.id,
				'location_dest_id': dest_loc.id,
				'state': 'draft',
				'expense_line_id': line.id,
				'new_expense_line_id': line.id,
			}

	def action_to_confirm(self):
		# Батлах - Агуулахын менежер батлах
		# if self.warehouse_id.confirm_user_id:
		#     if self.warehouse_id.confirm_user_id.id != self.env.user.id:
		#         raise UserError(_(u'Та зарлага хийх эрхгүй байна! \n "%s" хэрэглэгч батлах ёстой'%self.warehouse_id.confirm_user_id.name))

		# Гарах байрлалыг олох
		dest_loc = self.env['stock.location'].sudo().search(
						[('usage','=','customer')], limit=1)

		if not dest_loc:
			raise UserError(_(u'Зарлагадах байрлал олдсонгүй!'))

		tran_value = ""
		if self.transaction_value_id:
			tran_value = self.transaction_value_id.name +', '
		if self.description:
			tran_value += self.description
		for item in self:
			accountant_id =False
			if item.history_flow_ids:
				for history_line in item.history_flow_ids:
					history_ids = self.env['dynamic.flow.history'].search([('shaardah_id','=',item.id)])
					dynamic_id = self.env['dynamic.flow.line'].search([('id','in',history_ids.ids),('state_type','=','done')], limit=1)
					real_user_id = self.env['dynamic.flow.history'].search([('flow_line_id','=',dynamic_id.id)], limit=1)
					if real_user_id:
						accountant_id = real_user_id.user_id

		sp_id = self.env['stock.picking'].create(
			{'picking_type_id': self.warehouse_id.out_type_id.id,
			 'state': 'draft',
			 'move_type': 'one',
			 'partner_id': self.partner_id.id or False,
			 'scheduled_date': self.date_required,
			 'location_id': self.warehouse_id.lot_stock_id.id,
			 'location_dest_id': dest_loc.id,
			 'origin': self.name if self.name else '' + u' - Бусад зарлага хийх, '+tran_value if tran_value else '',
			 'other_expense_id': self.id,
			 'stock_expense_accountant':accountant_id.id if accountant_id else False,
			 'note':self.description if self.description else '',
			})

		for line in self.product_expense_line:
			price_unit = 0
			line.price_unit = price_unit

			desc = self.name+' - '+tran_value
			vals = self.get_prepare_stock_move_line(line, sp_id, price_unit, desc, dest_loc)
			line_id = self.env['stock.move'].create(vals)
			line.move_ids = [(4, line_id.id)]

		con = dict(self._context)
		con['from_code'] = True

		sp_id.with_context(con).action_confirm()
		sp_id.scheduled_date = self.date_required
		# sp_id.action_assign()
		# self.expense_picking_id = sp_id.id

		# Батлах
		self.validator_id = self.env.user.id
		self.date_validator = datetime.now()
		self.message_post(body=u"%s - батлагдлаа" % self.validator_id.name)
		self.state = 'done'


	def action_to_done(self):
		if 'done' not in self.expense_picking_ids.mapped('state'):
			raise UserError(_(u'Барааны зарлагадах хөдөлгөөн дуусаагүй байна!'))

		self.message_post(body=u"Барааг зарлагадаж дууссан")
		self.state = 'done'
		return True


	def get_user_signature(self,ids):
		report_id = self.browse(ids)
		html = '<table>'
		print_flow_line_ids = report_id.flow_id.line_ids.filtered(lambda r: r.is_print)
		history_obj = self.env['dynamic.flow.history']
		for item in print_flow_line_ids:
			his_id = history_obj.search([('flow_line_id','=',item.id),('shaardah_id','=',report_id.id)], limit=1)
			image_str = '________________________'
			if his_id.user_id.digital_signature_from_file:
				image_buf = (his_id.user_id.digital_signature_from_file).decode('utf-8')
				image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,%s" />'%(image_buf)
			elif his_id.user_id.digital_signature:
				image_buf = (his_id.user_id.digital_signature).decode('utf-8')
				image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,%s" />'%(image_buf)
			user_str = '________________________'
			if his_id.user_id:
				user_str = his_id.user_id.name
			html += u'<tr><td><p>%s</p></td><td>%s</td><td> <p>/%s/</p></td></tr>'%(item.display_name,image_str,user_str)
		html += '</table>'
		return html

	def get_line_ids(self, ids):
		headers = [
		u'Бараа',
		u'Хэмжих нэгж',
		u'Тоо',
		]
		report_id = self.browse(ids)
		if report_id.is_employee:
			headers = [
			u'Бараа',
			u'Хэмжих нэгж',
			u'Тоо',
			u'Ажилтан',
			u'Гарын Үсэг',
			]

		datas = []


		lines = report_id.product_expense_line

		sum1 = 0
		sum2 = 0
		sum3 = 0
		nbr = 1
		for line in lines:
			sum1 += line.qty
			if report_id.is_employee:
				temp = [
				u'<p style="text-align: left; height: 20px;">'+(line.product_id.display_name)+u'</p>',
				u'<p style="text-align: center;">'+(line.uom_id.name)+u'</p>',
				"{0:,.0f}".format(line.qty) or '',
				line.sudo().employee_id.display_name or '',
				'',
				]
			else:
				temp = [
				u'<p style="text-align: left;">'+(line.product_id.display_name)+u'</p>',
				u'<p style="text-align: center;">'+(line.uom_id.name)+u'</p>',
				"{0:,.0f}".format(line.qty) or '',
				]
			nbr += 1
			datas.append(temp)
		if report_id.is_employee:
			temp = [
			u'',
			u'<p style="text-align: center; font-weight: bold; ">Нийт дүн</p>',
			"{0:,.0f}".format(sum1) or '',
			'',
			''
			]
		else:
			temp = [
			u'',
			u'<p style="text-align: center; font-weight: bold; ">Нийт дүн</p>',
			"{0:,.0f}".format(sum1) or '',
			]
		if not datas:
			return False
		datas.append(temp)
		res = {'header': headers, 'data':datas}
		return res

	def get_company_logo(self, ids):

		report_id = self.browse(ids)
		company_id = self.env.user.company_id
		image_buf = company_id.logo_web
		image_str = '<img alt="Embedded Image" width="100" src="data:image/png;base64,'+image_buf+'" />'
		return image_str

	def action_view_edit_expense_line(self):
		if not self.product_expense_line:
			return False

		context = {}
		context['create']= False
		tree_view_id = self.env.ref('mw_stock_moves.stock_product_other_expense_line_tree_view').id
		# form_view_id = self.env.ref('account.view_move_form').id
		action = {
				'name': self.name,
				'view_mode': 'tree',
				'res_model': 'stock.product.other.expense.line',
				'views': [(tree_view_id, 'tree')],
				'view_id': tree_view_id,
				'domain': [('id','in',self.product_expense_line.ids)],
				'type': 'ir.actions.act_window',
				'context': context,
				'target': 'current'
			}
		return action


	def action_view_expense_picking_ids(self):
		tree_view_id = self.env.ref('stock.vpicktree').id
		form_view_id = self.env.ref('stock.view_picking_form').id
		return {
			'name': 'Хөдөлгөөн',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'stock.picking',
			'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
			'view_id': tree_view_id,
			'domain': [('id','in',self.expense_picking_ids.ids)],
			'context': {},
		}

	def set_partner(self):
		expenses =  self.env['stock.product.other.expense'].sudo().search([('id','!=',False)])
		for item in expenses:
			# item.partner_id = item.employee_id.partner_id
			for line in item.product_expense_line:
				line.res_partner_id = line.employee_id.partner_id

	def admin_get_move_ids(self, manual=True):
		if manual:
			expense_ids = self.env['stock.product.other.expense'].search([('expense_picking_ids','not in',[])])
		else:
			manual = self
		for item in expense_ids:
			move_ids = item.expense_picking_ids.mapped('move_ids')
			if move_ids:
				for line in item.product_expense_line:
					match_ids = move_ids.filtered(lambda r: r.product_id.id == line.product_id.id)
					line.move_ids = [(6, 0, match_ids.ids)] if match_ids else False
	
	@api.onchange('expense_picking_ids','expense_picking_ids.state')
	def onchange_expense_picking_ids(self):
		for item in self:
			item.admin_get_move_ids()

	def all_expense(self):
		expenses = self.env['stock.product.other.expense'].search([('expense_picking_ids','not in',[])])
		for item in expenses:
			for line in item.product_expense_line:
				line._compute_qty_delivered()

class StockProductOtherExpenseLine(models.Model):
	_name = 'stock.product.other.expense.line'
	_description = 'Stock Product Other Expense Line'
	_inherit = ["analytic.mixin","mail.thread", "mail.activity.mixin"]

	@api.model
	def _get_default_partner(self):
		parent_id =False
		if self.env.context.get('params', False) and self.env.context['params'].get('model', False) == 'stock.product.other.expense':
			parent_id = self.env['stock.product.other.expense'].browse(self.env.context['params'].get('id', False))
		if parent_id and parent_id.partner_id:
			return parent_id.partner_id.id
		else:
			return False

	
	# Columns
	parent_id = fields.Many2one('stock.product.other.expense', 'Parent ID', ondelete='cascade')
	product_id = fields.Many2one('product.product', u'Бараа', required=True)
	product_standard_price = fields.Float(store=True, string='Барааны өртөг', tracking=True)
	product_total_price = fields.Float(store=True, string='Барааны нийт өртөг', tracking=True)
	product_sale_price = fields.Float(store=True, string='Барааны зарах үнэ')
	uom_id = fields.Many2one(related='product_id.uom_id', string=u'Хэмжих нэгж', store=True, readonly=True, )
	categ_id = fields.Many2one(related='product_id.categ_id', string=u'Ангилал', store=True, readonly=True, )
	qty = fields.Float(u'Тоо хэмжээ', required=True, default=1,)
	price_unit = fields.Float(u'Нэгж үнэ', required=True, default=0,)
	available_qty = fields.Float('Үлдэгдэл', readonly=True, store=True, compute='update_available_qty')
	available_qty_template = fields.Float('Үлдэгдэл Хөрвөх Нийт', readonly=True, store=True, compute='update_available_qty')
	reserved_qty = fields.Float('Нөөцлөгдсөн', readonly=True, store=True, compute='update_available_qty')
	delivered_qty = fields.Float('Хүргэгдсэн тоо', readonly=True, store=True, compute='_compute_qty_delivered')
	diff_qty = fields.Float('Зөрүү', readonly=True, compute='_compute_diff_qty')
	employee_id = fields.Many2one('hr.employee', string=u'Ажилтан буруу')
	res_partner_id = fields.Many2one('res.partner', string=u'Хүлээн авсан ажилтан', domain=([('employee','=',True)]), default=_get_default_partner)
	last_date = fields.Date(string=u'Сүүлд авсан огноо')
	is_employee = fields.Boolean(related='parent_id.transaction_value_id.is_employee', readonly=True)
	is_not_edit = fields.Boolean(related='parent_id.is_not_edit')
	state_type = fields.Char(related='parent_id.state_type')
	list_price = fields.Float('Нэгж Үнэ')
	sub_total = fields.Float('Дэд дүн', compute='_sum_sub_total', store=True)
	date_required = fields.Date(related='parent_id.date_required', readonly=True)
	branch_id = fields.Many2one('res.branch', related='parent_id.branch_id', readonly=True)
	department_id = fields.Many2one('hr.department', related='parent_id.department_id', readonly=True)
	account_id = fields.Many2one('account.account', u'Данс', copy=False)
	account_analytic_ids = fields.Many2one('account.analytic.account', u'Аналитик данс', copy=False)
	move_ids = fields.Many2many('stock.move', 'other_expense_line_stock_move_rel', 'line_id','move_id', string="Move ids")
	new_move_ids = fields.One2many('stock.move', 'new_expense_line_id', string="New move ids")
	# analytic_distribution = fields.
	# fleet_id = fields.Many2one('fleet.vehicle', 'Техник /Машин/')



	@api.onchange('parent_id', 'parent_id.analytic_distribution','res_partner_id', 'product_id', 'parent_id.transaction_value_id')
	def _compute_analytic_distribution(self):
		for line in self:
			analytic_distribution=False
			if line.res_partner_id:
				employee = self.env['hr.employee'].search([('partner_id','=',line.res_partner_id.id)], limit=1)
				department_id = employee and employee.department_id
				_logger.info('employee %s '%(employee))
				distribution_model =self.env['account.analytic.distribution.model'].search([('department_id','=',department_id.id),
																							('company_id','=',self.env.company.id)],limit=1)
				_logger.info('distribution_model %s '%(distribution_model))
				analytic_distribution=distribution_model.analytic_distribution
			_logger.info('line.res_partner_id %s '%(line.res_partner_id))
			_logger.info('analytic_distribution %s '%(analytic_distribution))
			if analytic_distribution:
				line.analytic_distribution = analytic_distribution
			elif line.parent_id and line.parent_id.analytic_distribution:
				line.analytic_distribution = line.parent_id.analytic_distribution
			if line.parent_id and line.parent_id.transaction_value_id:
				line.account_id = line.parent_id.transaction_value_id.account_id.id if line.parent_id.transaction_value_id else False

	# @api.depends('parent_id', 'paren')
	# def _compute_account(self):

	# @api.model
	# def create(self, values):
	#     res = super(StockProductOtherExpenseLine, self).create(values)
	#     active = self.env.context.get('active_id')
	#     print('active aa: ', active, active._origin.id)
	#     return res

	@api.onchange('product_id')
	# @api.depends('product_id')
	def onchange_product_price(self):
		for obj in self:
			obj.product_standard_price = obj.product_id.standard_price
			obj.product_sale_price = obj.product_id.list_price
			obj.product_total_price = obj.product_id.standard_price*obj.qty

	@api.onchange('product_id','qty','product_standard_price')
	# @api.depends('product_id','qty')
	def compute_total_price(self):
		for obj in self:
			obj.product_total_price = obj.product_id.standard_price*obj.qty
			

	@api.depends('parent_id.warehouse_id','product_id')
	def update_available_qty(self):
		quant_obj = self.env['stock.quant']
		for item in self:
			quant_ids = []
			quant_temp_ids = []
			domain = self.env['product.product'].get_qty_template_domain(item.product_id)
			if item.parent_id.warehouse_id:
				quant_ids = quant_obj.search([('product_id','=',item.product_id.id),('location_id.set_warehouse_id','=',item.parent_id.warehouse_id.id),('location_id.usage','=','internal')])
				domain+=[('location_id.set_warehouse_id','=',item.parent_id.warehouse_id.id),('location_id.usage','=','internal')]
				quant_temp_ids = quant_obj.search(domain)
			else:
				quant_ids = quant_obj.search([('product_id','=',item.product_id.id),('location_id.usage','=','internal')])
				domain+=[('location_id.usage','=','internal')]
				quant_temp_ids = quant_obj.search(domain)
			item.available_qty_template = sum(quant_temp_ids.mapped('quantity'))
			reserved_qty_template = sum(quant_temp_ids.mapped('quantity'))
			item.available_qty = sum(quant_ids.mapped('quantity'))
			item.reserved_qty = sum(quant_ids.mapped('reserved_quantity'))

	@api.depends('new_move_ids.state', 'new_move_ids.scrapped', 'new_move_ids.product_uom_qty', 'new_move_ids.product_uom')
	def _compute_qty_delivered(self):
		for line in self:
			qty = 0.0
			outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
			for move in outgoing_moves:
				if move.state != 'done':
					continue
				qty += move.product_uom._compute_quantity(move.product_uom_qty, line.uom_id, rounding_method='HALF-UP')
			for move in incoming_moves:
				if move.state != 'done':
					continue
				qty -= move.product_uom._compute_quantity(move.product_uom_qty, line.uom_id, rounding_method='HALF-UP')
			line.delivered_qty = qty

	def _get_outgoing_incoming_moves(self):
		outgoing_moves = self.env['stock.move']
		incoming_moves = self.env['stock.move']

		moves = self.new_move_ids.filtered(lambda r: r.state != 'cancel' and not r.scrapped and self.product_id == r.product_id)
		for move in moves:
			if move.location_dest_id.usage == "customer":
				if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
					outgoing_moves |= move
			elif move.location_dest_id.usage != "customer" and move.to_refund:
				incoming_moves |= move

		return outgoing_moves, incoming_moves

	# @api.depends('qty','move_ids', 'parent_id.expense_picking_ids')
	# def compute_delivered_qty(self):
	# 	for item in self:
	# 		if item.move_ids:
	# 			move = self.env['stock.move'].browse(item.move_ids.ids)
	# 			query = """SELECT SUM(coalesce((m.product_qty / u.factor * u2.factor),0)) AS qty, 
	# 							SUM(coalesce((m.price_unit * m.product_qty / u.factor * u2.factor),0)) AS cost 
	# 						FROM stock_move AS m 
	# 							JOIN product_product AS pp ON (m.product_id = pp.id) 
	# 							JOIN product_template AS pt ON (pp.product_tmpl_id = pt.id) 
	# 							JOIN uom_uom AS u ON (m.product_uom = u.id) 
	# 							JOIN uom_uom AS u2 ON (pt.uom_id = u2.id) 
	# 						WHERE m.origin_returned_move_id in (%s) AND m.location_dest_id in (%s) 
	# 							AND m.state = 'done' """ % (','.join(str(move.id) for move in item.move_ids), ','.join(str(loc) for loc in item.move_ids.mapped('location_id.id')))
	# 			self._cr.execute(query)
	# 			result = self._cr.dictfetchall()
	# 		else:
	# 			result = []
	# 		if result:
	# 			item.returned_qty = sum([r['qty'] for r in result if r['qty']])
	# 		else:
	# 			item.returned_qty = 0
	# 		qty = sum(item.move_ids.mapped('quantity_done')) if item.move_ids else 0
	# 		item.delivered_qty = qty - item.returned_qty

	def write(self, values):
		if 'qty' in values:
			for line in self:
				if line.parent_id.state_type != 'draft':
					line.parent_id.message_post_with_view('mw_stock_moves.track_po_line_template',
														 values={'line': line, 'qty': values['qty']},
														 subtype_id=self.env.ref('mail.mt_note').id)
		return super(StockProductOtherExpenseLine, self).write(values)

	def unlink(self):
		for item in self:
			if item.parent_id.state_type != 'draft':
				item.parent_id.message_post_with_view('mw_stock_moves.track_po_line_template_delete',
														values={'line': item},
														subtype_id=self.env.ref('mail.mt_note').id)
		return super(StockProductOtherExpenseLine, self).unlink()

	@api.depends('list_price','qty')
	def _sum_sub_total(self):
		for item in self:
			item.sub_total = item.list_price*item.qty

	# Зарах үнэ харсан хараагүй цэнэглэдэг байх
	@api.onchange('product_id')
	def onchange_list_price(self):
		if self.product_id:
			self.price_unit = self.product_id.standard_price
			self.list_price = self.product_id.list_price or self.product_id.standard_price

	@api.depends('available_qty','qty')
	def _compute_diff_qty(self):
		for item in self:
			if item.available_qty > item.qty:
				item.diff_qty = item.available_qty - item.qty
			else:
				item.diff_qty = 0

	# @api.constrains('product_id', 'parent_id','employee_id')
	# def _constraint_product_employee(self):
	#     for item in self:
	#         if item.is_employee:
	#             item_id = item.parent_id.product_expense_line.filtered(lambda r: r.product_id.id==item.product_id.id and r.sudo().employee_id.id==item.sudo().employee_id.id and r.id!=item.id)
	#             if item_id:
	#                 raise ValidationError((u'Давхардсан бараанууд %s Ажилтанууд %s') % (', '.join(item_id.mapped('product_id.display_name')),', '.join(item_id.sudo().mapped('employee_id.display_name'))))
	#         else:
	#             item_id = item.parent_id.product_expense_line.filtered(lambda r: r.product_id.id==item.product_id.id and r.id!=item.id)
	#             if item_id:
	#                 raise ValidationError((u'Давхардсан бараанууд %s') % (', '.join(item_id.mapped('product_id.display_name'))))

class dynamic_flow_history(models.Model):
	_inherit = 'dynamic.flow.history'

	shaardah_id = fields.Many2one('stock.product.other.expense', 'БМ Шаардах', ondelete='cascade', index=True)

class stock_product_exepense_history(models.Model):
	_name = 'stock.product.other.expense.history'
	_description = 'stock product exepense history'
	_order = 'date desc'

	expense_id = fields.Many2one('stock.product.other.expense','Хүсэлт', ondelete='cascade')
	user_id = fields.Many2one('res.users','Өөрчилсөн хэрэглэгч')
	date = fields.Datetime('Огноо', default=fields.Datetime.now)
	flow_line_id = fields.Many2one('dynamic.flow.line', 'Төлөв')
	create_ok = fields.Boolean('Create ok', default=False)

	# def create_history(self, flow_line_id, expense_id):
	#     return self.env['dynamic.flow.history'].create_history(flow_line_id, expense_id)
		# self.env['stock.product.other.expense.history'].create({
		#     'expense_id': expense_id.id,
		#     'user_id': self.env.user.id,
		#     'date': datetime.now(),
		#     'flow_line_id': flow_line_id.id
		#     })


class product_product(models.Model):
	_inherit = 'product.product'

	def get_qty_template_domain(self, product_id):
		return [('product_id.product_tmpl_id','=',product_id.product_tmpl_id.id),('product_id','!=',product_id.id)]
