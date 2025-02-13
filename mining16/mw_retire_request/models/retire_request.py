# -*- coding: utf-8 -*-

from odoo import api, models, fields, _, tools
from odoo.exceptions import UserError
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
# import collections
# from odoo.osv import expression
import logging
_logger = logging.getLogger(__name__)

class DynamicFlowHistory(models.Model):
	_inherit = 'dynamic.flow.history'

	retire_id = fields.Many2one('retire.request', 'Retire request', ondelete='cascade', index=True)

class RetireRequest(models.Model):
	_name = 'retire.request'
	_description = 'Retire request'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	# default functions
	def _get_dynamic_flow_line_id(self):
		return self.flow_find()

	def _get_default_flow_id(self):
		search_domain = [('model_id.model', '=', 'retire.request'),
						 ('branch_ids', 'in', [self.env.user.branch_id.id])]
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

	def _get_name(self):
		# temp = '1'
		# n = 0
		# date = datetime.strftime(self.date_required,'%y%m%d')
		# query = """SELECT max(w.name) FROM retire_request as w WHERE name like '%{0}%'""".format(date)
		# self.env.cr.execute(query)
		# wo_number = self.env.cr.dictfetchall()
		# if not wo_number[0]['max'] is None:
		# 	n = int(wo_number[0]['max'][9:])
		# temp = str(n + 1)
		# _logger.info(u'-***********-NEW RR ID & NUMBER--*************mining*** %d & %s \n' % (self.id, temp))
		# date_required = datetime.strftime(self.date_required,'%Y-%m-%d')
		# number = 'WO'+date_required[2:4]+date_required[5:7]+date_required[8:]+'-'+ temp.zfill(3)
		# return number
		return self.env['ir.sequence'].next_by_code('retire.request')

	# fields
	name = fields.Char(string='Баримтын дугаар', default=_get_name, readonly=True)
	date = fields.Date(string='Огноо', required=True)
	respondent_id = fields.Many2one('res.partner', string='Хариуцагч', required=True)
	description = fields.Char(string='Актлах тайлбар')
	company_id = fields.Many2one('res.company', 'Компани', default=lambda self: self.env.user.company_id)
	branch_id = fields.Many2one('res.branch', 'Салбар', default=lambda self: self.env.user.branch_id)
	technic_id = fields.Many2one('technic.equipment', string='Техник')
	equipment_id = fields.Many2one('factory.equipment', string='Тоног төхөөрөмж')
	# tire_id = fields.Many2one('technic.tire', string='Дугуй')
	tire_line_ids = fields.One2many('retire.request.line', 'parent_id',string='Дугуйнууд')
	component_id = fields.Many2one('technic.component.part', string='Компонент')
	product_id = fields.Many2one('product.product', string='Сэлбэг')
	amount_total = fields.Float(string='Cost')
	attachment_ids = fields.Many2many('ir.attachment', string="Хавсралтууд")
	retire_type = fields.Selection([('technic','Technic'),('equipment','Equipment'),('tire','Tire'),('component','Component'),('parts','Parts')], string='Retire type', default=lambda self: self.env.context.get('retire_type', False))

	# flow
	flow_id = fields.Many2one('dynamic.flow', string='Урсгал тохиргоо', tracking=True, default=_get_default_flow_id, 
		copy=True, required=True, domain="[('model_id.model', '=', 'retire.request')]")
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True, default=_get_dynamic_flow_line_id, 
		copy=False, domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'retire.request')]")
	state_type = fields.Char(string='Төлвийн төрөл', compute='_compute_state_type', store=True)
	is_not_edit = fields.Boolean(compute='_compute_is_not_edit', string='Is edit?')
	flow_line_next_id = fields.Many2one('dynamic.flow.line', string='Дараагын төлөв', related='flow_line_id.flow_line_next_id', readonly=True, store=True)
	next_state_type = fields.Char(string='Дараагын төлвийн төрөл', compute='_compute_next_state_type')
	flow_line_back_id = fields.Many2one('dynamic.flow.line', 'Өмнөх төлөв', related='flow_line_id.flow_line_back_id', readonly=True)
	history_flow_ids = fields.One2many('dynamic.flow.history', 'retire_id', 'Төлвийн түүх')
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='Төлвийн үе шат', store=True)
	visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлвүүд')

	def flow_find(self, domain=None, order='sequence'):
		if domain is None:
			domain = []
		if self.flow_id:
			domain.append(('flow_id', '=', self.flow_id.id))
		domain.append(('flow_id.model_id.model', '=', 'retire.request'))
		return self.env['dynamic.flow.line'].search(domain, order=order, limit=1).id

	def get_technic_tires(self):
		self.ensure_one()
		if self.technic_id and self.retire_type == 'tire' and not self.tire_line_ids and self.state_type == 'draft':
			self.tire_line_ids.unlink()
			for line in self.technic_id.tire_line:
				self.env['retire.request.line'].create({
					'parent_id': self.id,
					'line': line.tire_id.id,
					'position': line.tire_id.position,
					'is_retire': False,
				})

	@api.depends('flow_line_id.stage_id')
	def _compute_flow_line_id_stage_id(self):
		for item in self:
			item.stage_id = item.flow_line_id.stage_id

	@api.depends('flow_line_id')
	def _compute_state_type(self):
		for item in self:
			item.state_type = item.flow_line_id.state_type if item.flow_line_id and item.flow_line_id.state_type else item.state_type
	

	@api.depends('flow_line_next_id.state_type')
	def _compute_next_state_type(self):
		for item in self:
			item.next_state_type = item.flow_line_next_id.state_type
	
	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.flow_line_id = self.flow_find()
		else:
			self.flow_line_id = False
	
	@api.depends('flow_line_id.is_not_edit')
	def _compute_is_not_edit(self):
		for item in self:
			item.is_not_edit = item.flow_line_id.is_not_edit
	
	@api.depends('flow_id.line_ids', 'flow_id.is_amount', 'amount_total')
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
						elif fl.amount_price_min <= item.amount_total <= fl.amount_price_max:
							flow_line_ids.append(fl.id)
					item.visible_flow_line_ids = flow_line_ids
				else:
					item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),
																					   ('flow_id.model_id.model', '=', 'purchase.order')])
			else:
				item.visible_flow_line_ids = []

	# def get_decision_approver(self):
	# 	action = {
	# 		'type': 'ir.actions.act_window',
	# 		'res_model': 'retire.request',
	# 		'view_mode': 'form',
	# 		'view_id': 'form',
	# 		'context': self.env.context,
	# 		'target': 'new',
	# 	}
	# 	return action

	def view_retire_description(self):
		action = self.env.ref('mw_retire_request.action_retire_approve_description').read()[0]
		object_id = self.env['retire.approve.description'].create({'retire_id': self.id})
		action['name'] = 'Хянагчын шийвдэр'
		action['res_id'] = object_id.id
		action['domain'] = []
		# action['context'] = {'is_retire_description': True}
		action['target'] = 'new'
		return action

	def action_next_stage(self, decision=False):
		if not self.respondent_id.user_ids:
			raise UserError(u'%s ажилтан дээр хэрэглэгч алга байна.' % self.respondent_id.name)
		user_id = self.respondent_id.user_ids[0]
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		history_line_id = False
		if next_flow_line_id:
			if next_flow_line_id._get_check_ok_flow(self.branch_id, user_id.department_id, user_id):
				# Батлах тайлбар дуудах
				self.flow_line_id = next_flow_line_id
				# History uusgeh
				history_line_id = self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'retire_id', self)
				if decision:
					history_line_id.decision_description = decision
				self.send_chat_employee(self.sudo().respondent_id)
				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users(self.branch_id, user_id.department_id, user_id)
					if send_users:
						self.send_chat_next_users(send_users.mapped('partner_id'))
			else:
				con_user = next_flow_line_id._get_flow_users(self.branch_id, False)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)
			# if self.flow_line_id.state_type == 'done':
				# self.approved_date = datetime.now()
		# print('history_line_id', history_line_id)
		# if history_line_id:
		# 	action = self.env.ref('mw_dynamic_flow.action_dynamic_flow_history').read()[0]
		# 	view_id = self.env.ref('mw_retire_request.dynamic_flow_history_retire_description_form').id
		# 	action['name'] = 'Хянагчын тайлбар'
		# 	action['res_id'] = history_line_id.id
		# 	action['views'] = [[view_id, 'form']]
		# 	action['domain'] = []
		# 	action['context'] = {'is_retire_description': True}
		# 	action['target'] = 'new'
		# 	return action
		# else:
		# 	raise Warning(('NO!'))

	def action_back_stage(self):
		if not self.respondent_id.user_ids:
			raise UserError(u'%s ажилтан дээр хэрэглэгч алга байна.' % self.respondent_id.name)
		user_id = self.respondent_id.user_ids[0]
		back_flow_line_id = self.flow_line_id._get_back_flow_line()
		if back_flow_line_id:
			if back_flow_line_id._get_check_ok_flow(self.branch_id, user_id.department_id, user_id):
				self.flow_line_id = back_flow_line_id
				# History uusgeh
				self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'retire_id', self)
				self.send_chat_employee(self.sudo().respondent_id)
			else:
				raise UserError(_('You are not back user'))

	def action_cancel_stage(self):
		if not self.respondent_id.user_ids:
			raise UserError(u'%s ажилтан дээр хэрэглэгч алга байна.' % self.respondent_id.name)
		user_id = self.respondent_id.user_ids[0]
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow(self.branch_id, user_id.department_id, user_id):
			self.flow_line_id = flow_line_id
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'retire_id', self)
			self.send_chat_employee(self.sudo().respondent_id)
		else:
			raise UserError(_('You are not cancel user'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		# if self.line_ids.filtered(lambda r: r.po_line_ids):
		# 	raise UserError(u'Худалдан авалтын захиалга үүссэн тул буцаах боломжгүй!')
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'retire_id', self)
		else:
			raise UserError(_('You are not draft user'))
		
	def send_chat_employee(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		if self.env.context.get('retire_type', False) == 'technic':
			action_id = self.env.ref('mw_retire_request.action_technic_retire_request').id
		elif self.env.context.get('retire_type', False) == 'equipment':
			action_id = self.env.ref('mw_retire_request.action_tire_retire_request').id
		elif self.env.context.get('retire_type', False) == 'tire':
			action_id = self.env.ref('mw_retire_request.action_equipment_retire_request').id
		elif self.env.context.get('retire_type', False) == 'component':
			action_id = self.env.ref('mw_retire_request.action_component_retire_request').id
		else:
			def get_custom_action():
				action = self.env.ref('mw_retire_request.action_technic_retire_request').read()[0]
				action['context'] = {}
				return action
			action_id = self.env.ref('mw_retire_request.action_technic_retire_request').id
		html = u'<b>Актлах хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (self.respondent_id.name)
		html += u"""<b><a target="_blank"  href=%s/web#action=%s&id=%s&view_type=form&model=retire.request>%s</a></b>, дугаартай Актлах хүсэлт <b>%s</b> төлөвт орлоо""" % (base_url, action_id, self.id, self.name, state)
		self.flow_line_id.send_chat(html, partner_ids)

	def send_chat_next_users(self, partner_ids):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		if self.env.context.get('retire_type', False) == 'technic':
			action_id = self.env.ref('mw_retire_request.action_technic_retire_request').id
		elif self.env.context.get('retire_type', False) == 'equipment':
			action_id = self.env.ref('mw_retire_request.action_tire_retire_request').id
		elif self.env.context.get('retire_type', False) == 'tire':
			action_id = self.env.ref('mw_retire_request.action_equipment_retire_request').id
		elif self.env.context.get('retire_type', False) == 'component':
			action_id = self.env.ref('mw_retire_request.action_component_retire_request').id
		else:
			def get_custom_action():
				action = self.env.ref('mw_retire_request.action_technic_retire_request').read()[0]
				action['context'] = {}
				return action
			action_id = self.env.ref('mw_retire_request.action_technic_retire_request').id
		html = u'<b>Актлах хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (self.respondent_id.name)
		html += u"""<b><a target="_blank" href=%s/web#action=%s&id=%s&view_type=form&model=retire.request>%s</a></b>, дугаартай Актлах хүсэлтийг батлана уу""" % (
			base_url, action_id, self.id, self.name)

		# +start activity
		users = self.env['res.users'].search([('partner_id', 'in', partner_ids.ids)])
		if users and self.flow_line_id.flow_id.activity_ok:
			self.env['dynamic.flow.history'].done_activity('purchase.request', self.id)
			self.env['dynamic.flow.history'].create_activity(html, users, 'purchase.request', self.id)
		# -end activity
		self.flow_line_id.send_chat(html, partner_ids)

	def get_user_signature(self, ids):
		report_id = self.browse(ids)
		html = '<table>'
		print_flow_line_ids = report_id.flow_id.line_ids.filtered(lambda r: r.is_print)
		history_obj = self.env['dynamic.flow.history']
		for item in print_flow_line_ids:
			his_id = history_obj.search([('flow_line_id', '=', item.id), ('retire_id', '=', report_id.id)], limit=1)
			image_str = '________________________'
			if his_id.user_id.digital_signature:
				image_buf = his_id.user_id.digital_signature.decode('utf-8')
				image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,%s" />' % image_buf
			user_str = '________________________'
			if his_id.user_id:
				user_str = his_id.user_id.name
			html += u'<tr><td><p>%s</p></td><td>%s</td><td> <p>/%s/</p></td></tr>' % (item.name, image_str, user_str)
		html += '</table>'
		return html

class RetireRequestLine(models.Model):
	_name = 'retire.request.line'
	_description = 'Retire request line'

	parent_id = fields.Many2one('retire.request', string='Parent ID')
	tire_id = fields.Many2one('technic.tire', string='Дугуй')
	position = fields.Integer(string="Байрлал", readonly=True)
	is_retire = fields.Boolean(string='Актлах уу?', default=False)

class RetireApproveDescription(models.TransientModel):
	_name = 'retire.approve.description'
	_description = 'Retire apprive description'

	retire_id = fields.Many2one('retire.request', string='Retire', required=True)
	decision_description = fields.Char(string='Шийдвэр')

	def action_approve(self):
		self.ensure_one()
		self.retire_id.action_next_stage(self.decision_description)