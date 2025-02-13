# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime, time, timedelta
import collections
import time

import logging
_logger = logging.getLogger(__name__)
from odoo.addons.mw_technic_maintenance.models.maintenance_workorder import MAINTENANCE_TYPE

class SelectedMaintenancePlanDelete(models.TransientModel):
	_name = "selected.maintenance.plan.delete"
	_description = "selected maintenance plan delete"

	with_delete = fields.Boolean(string=u'Давхар устгах эсэх', default=False)

	def action_cancel(self):
		obj_ids = self.env['maintenance.plan.line'].browse(self._context['active_ids'])
		for plan in obj_ids:
			plan.action_to_cancel()
			if self.with_delete:
				plan.action_to_draft()
				plan.unlink()

class MaintenancePlan(models.Model):
	_name = 'maintenance.plan'
	_description = 'Maintenance plan'
	_inherit = 'mail.thread'
	_order = 'year desc, month desc'

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,
		states={'confirmed': [('readonly', True)],'done': [('readonly', True)]})


	date = fields.Datetime(string=u'Үүсгэсэн огноо', readonly=True, default=datetime.now(), copy=False)
	description = fields.Char(string=u'Тайлбар', copy=True, required=True,
		states={'confirmed': [('readonly', True)],'done': [('readonly', True)]})
	name = fields.Char(string=u'Дугаар', readonly=True, copy=False)
	# ---
	year = fields.Integer(string=u'Жил', copy=False, required=True,
		states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})

	month = fields.Selection([
			('1', u'January'),
			('2', u'February'),
			('3', u'March'),
			('4', u'April'),
			('5', u'May'),
			('6', u'June'),
			('7', u'July'),
			('8', u'August'),
			('9', u'September'),
			('10', u'October'),
			('11', u'November'),
			('12', u'December'),
		], string=u'Сар', copy=True, required=True,
		states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})

	planner_id = fields.Many2one('res.users', string=u'Баталсан', readonly=True)

	plan_line = fields.One2many('maintenance.plan.line', 'parent_id', 'Lines', copy=False,
		states={'confirmed': [('readonly', True)],'done': [('readonly', True)]})

	state = fields.Selection([
			('draft', 'Draft'),
			('confirmed', 'Confirmed'),
			('done', 'Done')
		], default='draft', required=True, string='Төлөв', tracking=True)

	@api.depends('plan_line')
	def _methods_compute(self):
		for obj in self:
			obj.total_amount = sum(obj.mapped('plan_line.total_amount'))
	total_amount = fields.Float(compute=_methods_compute, store=True, string=u'Total amount', tracking=True, default=0)

	# ============ Override ===============
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('In order to delete a record, it must be draft first!'))
		return super(MaintenancePlan, self).unlink()

	# ============ Custom methods =========
	def action_to_draft(self):
		self.state = 'draft'
	
	def action_to_confirm(self):
		if 2000 > self.year or self.year > 3000:
			raise UserError(_(u'Сарын төлөвлөгөөний оныг буруу оруулсан байна!'))
		self.planner_id = self.env.user.id
		self.message_post(body="Баталсан %s" % self.planner_id.name)
		if not self.name:
			self.name = 'Төлөвлөгөө: '+str(self.year)+'/'+str(self.month)
		self.state = 'confirmed'

	
		if self.plan_line:
			context = dict(self._context)
			# GET views ID
			mod_obj = self.env['ir.model.data']
			search_res = mod_obj._xmlid_lookup('mw_technic_maintenance.maintenance_expense_report_search')
			search_id = search_res and search_res[2] or False
			pivot_res = mod_obj._xmlid_lookup('mw_technic_maintenance.maintenance_expense_report_pivot')
			pivot_id = pivot_res and pivot_res[2] or False

			return {
				'name': self.name+' ('+str(self.year)+')',
				'view_mode': 'pivot',
				'res_model': 'maintenance.expense.report',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': [('mp_id','=',self.id)],
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context,
			}

class MaintenancePlanLine(models.Model):
	_name = 'maintenance.plan.line'
	_description = 'Maintenance plan line'
	_order = 'date_required desc'
	_inherit = ['mail.thread']

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,
		states={'confirmed':[('readonly',True)],'wo_created':[('readonly',True)],'done':[('readonly',True)],'cancelled':[('readonly',True)]})

	name = fields.Char(string=u'Дугаар', readonly=True, copy=False )
	origin = fields.Char(string=u'Эх баримт', readonly=True, )
	parent_id = fields.Many2one('maintenance.plan', string=u'Эцэг төлөвлөгөө',ondelete='cascade')

	date = fields.Datetime(string=u'Үүсгэсэн огноо', default=datetime.now(), readonly=True)
	date_required = fields.Date(string=u'Хийгдэх огноо', tracking=True, 
		states={'confirmed':[('readonly',True)],'wo_created':[('readonly',True)],'done':[('readonly',True)],'cancelled':[('readonly',True)]})

	technic_id = fields.Many2one('technic.equipment', string=u'Техник', copy=True,
		help=u"Choose the technic", required=False,
		states={'confirmed':[('readonly',True)],'wo_created':[('readonly',True)],'done':[('readonly',True)],'cancelled':[('readonly',True)]})
	start_odometer = fields.Float(string='Хийгдэх гүйлт', digits = (16,1), help="When repairing odometer value",
		states={'confirmed': [('readonly', True)],'wo_created':[('readonly',True)],'done': [('readonly', True)],'cancelled': [('readonly', True)]})
	
	work_time = fields.Float(string='Засваын цаг', digits = (16,1), help="Засварт зарцуулах цаг",
		states={'confirmed': [('readonly', True)],'wo_created':[('readonly',True)],'done': [('readonly', True)],'cancelled': [('readonly', True)]})
	man_hours = fields.Float(string=u'Хүн/цаг', 
		states={'confirmed': [('readonly', True)],'wo_created':[('readonly',True)],'done': [('readonly', True)],'cancelled': [('readonly', True)]} )
	description = fields.Text(u'Хийгдэх ажил', required=True,
		states={'confirmed': [('readonly', True)],'wo_created':[('readonly',True)],'done': [('readonly', True)],'cancelled': [('readonly', True)]})
	maintenance_type_id = fields.Many2one('maintenance.type', u'Засварын төрөл 2', copy=False,
		states={'confirmed': [('readonly', True)],'wo_created':[('readonly',True)],'done': [('readonly', True)],'cancelled': [('readonly', True)]})
	is_waiting_part = fields.Boolean(related='maintenance_type_id.is_waiting_part', readonly=True, store=True,)
	is_waiting_tire = fields.Boolean(related='maintenance_type_id.is_waiting_tire', readonly=True, store=True,)
	pm_priority = fields.Text(string=u'PM ийн дугаар', readonly=True, default=0 )

	workorder_id = fields.Many2one('maintenance.workorder', u'Work Order', readonly=True)
	workorder_rate = fields.Selection(related='workorder_id.workorder_rate', readonly=True, )

	user_id = fields.Many2one('res.users', u'Хэрэглэгч', default=_get_user, readonly=True)
	planner_id = fields.Many2one('res.users', u'Төлөвлөгч', readonly=True, copy=False,)

	maintenance_type = fields.Selection([
		('main_service', u'Урсгал засвар'),
		('pm_service', u'PM service'),
		('planned', u'Planned'),
		('stopped', u'Зогсолт'),
		('tire_service', u'Tire service'),
		('daily_works', u'Өдөр тутмын ажил')],
		string=u'Засварын төрөл', required=True,
		states={'confirmed':[('readonly',True)],'wo_created':[('readonly',True)],'done':[('readonly',True)],'cancelled':[('readonly',True)]}
		)

	contractor_type = fields.Selection([
		('internal', u'Дотооддоо засварлах'),
		('external', u'Гадны гүйцэтгэгчээр'),],
		string=u'Гүйцэтгэгч нь', default='internal', required=True,
		states={'confirmed':[('readonly',True)],'wo_created':[('readonly',True)],'done':[('readonly',True)],'cancelled':[('readonly',True)]}
		)

	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),],
		string=u'Ээлж',
		states={'wo_created':[('readonly',True)],'done':[('readonly',True)],'cancelled':[('readonly',True)]})

	to_delay = fields.Boolean(string=u'Хойшлуулах эсэх', default=False, copy=False,
		states={'wo_created':[('readonly',True)],'done': [('readonly', True)],'cancelled': [('readonly', True)]})
	to_delay_description = fields.Text(string=u'Хойшлуулсан шалтгаан', copy=False,
		states={'wo_created':[('readonly',True)],'done': [('readonly', True)],'cancelled': [('readonly', True)]})
	to_delay_date = fields.Date(string=u'Хийгдэх байсан огноо',
		states={'wo_created':[('readonly',True)],'done':[('readonly',True)],'cancelled':[('readonly',True)]})
	# po_request_id = fields.Many2one('purchase.request', u'Худалдан авалтын хүсэлт', readonly=True, copy=False,)

	# Сэлбэг материалууд
	required_material_line = fields.One2many('required.material.line', 'parent_id', string=u'Шаардлагатай сэлбэг материал',
		states={'confirmed':[('readonly',True)],'wo_created':[('readonly',True)],'done':[('readonly',True)],'cancelled':[('readonly',True)]},
		help=u"Бараа зарлагадах мэдээлэл")

	state = fields.Selection([
			('draft', u'Draft'),
			('confirmed', u'Confirmed'),
			('wo_created', u'WO created'),
			('done', u'Done'),
			('cancelled', u'Cancelled'),],
			default='draft', string=u'Төлөв', tracking=True)

	# Нийт зардал
	@api.depends('required_material_line')
	def _methods_compute(self):
		for obj in self:
			obj.total_amount = sum(obj.required_material_line.mapped('amount'))
	total_amount = fields.Float(compute=_methods_compute, store=True, string=u'Total amount', digits=(16,1))

	# Generator
	generator_line_id = fields.Many2one('maintenance.plan.generator.line', string=u'Холбоотой Forecast', readonly=True, )
	ref_plan_id = fields.Many2one('maintenance.plan.line', string=u'Холбоотой төлөвлөгөө', readonly=True, )

	# ==================== Overrided --------------------------
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй бичлэгийг устгаж болно! %s ' % s.name))
			if s.workorder_id:
				if s.workorder_id.state != 'draft':
					raise UserError(_(u'WO нээсэн байна! %s ' % s.workorder_id.name))
				else:
					s.workorder_id.unlink()

		return super(MaintenancePlanLine, self).unlink()

	def write(self, vals):
		if vals.get('to_delay_date'):
			temp = self.date_required
			vals['date_required'] = vals.get('to_delay_date')
			vals['to_delay_date'] = temp
		res = super(MaintenancePlanLine, self).write(vals)
			# REF төлөвлөгөө байвал дагаж хойшлуулах
		if vals.get('to_delay_date'):
			ref_plans = self.env['maintenance.plan.line'].search([('ref_plan_id','=',self.id)])
			if ref_plans:
				d1 = self.date_required
				d2 = temp
				days = (d1 - d2).days
				if days != 0:
					for ppp in ref_plans:
						ppp.date_required = datetime.strptime(ppp.date_required, "%Y-%m-%d") + timedelta(days=days)
		return res

	# ==================== Custom methods ======================
	def action_to_cancel(self):
		if self.state in ['confirmed','wo_created','draft']:
			if self.workorder_id:
				if self.workorder_id.state != 'draft':
					raise UserError(_(u'WO нээсэн байна! %s ' % self.workorder_id.name))
				else:
					self.workorder_id.action_to_cancel()
			self.state = 'cancelled'

	def action_to_draft(self):
		if self.workorder_id:
			if self.workorder_id.state != 'draft':
				raise UserError(_(u'WO нээсэн байна! %s ' % self.workorder_id.name))
			else:
				self.workorder_id.action_to_cancel()
		self.state = 'draft'

	def action_to_done(self):
		self.state = 'done'
		# Холбоотой төлөвлөгөөг дуусгах
		ref_plans = self.env['maintenance.plan.line'].search([('ref_plan_id','=',self.id)])
		for p in ref_plans:
			p.state = 'done'

	
	def action_to_confirm(self):
		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code('maintenance.plan.line')
		# Эцэг төлөвлөгөө байна уу шалгах
		parent_plan = self.env['maintenance.plan'].search([('year','=',datetime.strftime(self.date_required,'%Y')),
														   ('month','=',datetime.strftime(self.date_required,'%m'))],limit=1)
		if parent_plan:
			self.parent_id = parent_plan.id
		else:
			vals = {
				'year': str(self.date_required.year),
				'month': str(self.date_required.month),
				'description': datetime.strftime(self.date_required,'%m') + u' Сарын төлөвлөгөө',
				'branch_id': self.branch_id.id,
			}
			# Эцэг төлөвлөгөөг түр хассан
			# parent_plan = self.env['maintenance.plan'].create(vals)
			# parent_plan.action_to_confirm()
			# self.parent_id = parent_plan.id

		self.state = 'confirmed'
		self.planner_id = self.env.user.id

	# Workorder үүсгэх
	def create_workorder(self):
		if self.workorder_id:
			raise UserError(_(u'Already Workorder created!'))

		if not self.shift:
			raise UserError(_(u'Өдөр шөнө хийгдэх ээлжийг сонгоно уу!'))

		# WO үүсгэх
		ref_extra_time = 0
		ref_plans = self.env['maintenance.plan.line'].search([('ref_plan_id','=',self.id)])
		if ref_plans:
			ref_extra_time = sum(ref_plans.mapped('work_time'))

		vals = {
			'branch_id': self.branch_id.id,
			'date_required': self.to_delay_date if self.to_delay_date else self.date_required,
			'maintenance_type': self.maintenance_type,
			'maintenance_type_id': self.maintenance_type_id.id,
			'pm_priority': self.pm_priority,
			'origin': self.name,
			'technic_id': self.technic_id.id,
			'description': self.description,
			'start_odometer': self.start_odometer,
			# 'planned_time': self.work_time + ref_extra_time,
			'planned_mans': int(self.man_hours/self.work_time),
			'contractor_type': self.contractor_type,
			'plan_id': self.id,
			'shift': self.shift,
		}
		wo_id = self.env['maintenance.workorder'].create(vals)
		wo_id._create_planned_time_line(self.work_time + ref_extra_time)
		# Хэрэглэх ТЭМ үүсгэх
		for line in self.required_material_line:
			vline = {
				'product_id': line.product_id.id,
				'qty': line.qty,
				'price_unit': line.product_id.standard_price,
				'parent_id': wo_id.id,
				'is_pm_material': line.is_pm_material,
				'src_warehouse_id': line.warehouse_id.id if line.warehouse_id else False,
			}
			self.env['required.part.line'].create(vline)
		# WO нээх
		# wo_id.action_to_open()

		self.state = 'wo_created'
		self.workorder_id = wo_id.id

	# Сэлбэг Худалдан авалтын хүсэлт үүсгэх
	def create_po_request_for_parts(self):
		if self.required_material_line:
			req_id = False
			if not self.po_request_id or self.po_request_id.state == 'cancel':
				emp = self.env['hr.employee'].search([('user_id','=',self.env.user.id)], limit=1)
				# Bayasaa nemev
				search_domain = [('model_id.model','=','purchase.request'),('branch_ids','in',[self.env.user.branch_id.id])]
				flow_id = self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1)
				flow_line_id = self.env['dynamic.flow.line'].search([('flow_id','=',flow_id.id)], order='sequence', limit=1)

				req_id = self.env['purchase.request'].create(
					{'employee_id': emp.id if emp else False,
					 'desc': self.name +', '+self.technic_id.name+': '+self.description+'\n',
					 'flow_id': flow_id.id,
					 'flow_line_id': flow_line_id.id,
					 'maintenance_plan_id': self.id,
					})
			else:
				req_id = self.po_request_id

			for line in self.required_material_line:
				vals = {
					'request_id': req_id.id,
					'product_id': line.product_id.id,
					'uom_id': line.uom_id.id,
					'qty': line.qty,
					'price_unit': line.price_unit,
				}
				line_id = self.env['purchase.request.line'].create(vals)

			self.po_request_id = req_id.id
			self.message_post(body=u"%s- дугаартай сэлбэг захиалгын PR үүслээ." %(req_id.name))

		else:
			raise UserError(_(u'Сэлбэг, материалын мэдээллийг оруулна уу!'))

	# Төлөвлөгөөний хугацаа шалгах - Крон метод - CRON
	@api.model
	def _check_plan_date(self):
		# Дуусч байгаа Төлөвлөгөө шалгах
		today = datetime.now()
		date_stop = today + timedelta(days=3)
		plans = self.env['maintenance.plan.line'].search([
			('state','=','confirmed'),
			('date_required','>=',today),
			('date_required','<=',date_stop)])
		msg = []
		for line in plans:
			msg.append(str(line.name or '')+': ('+(line.maintenance_type_id.name or '')+'->'+str(line.technic_id.name or '')+')')

		if msg:
			# Get group
			res_model = self.env['ir.model.data'].search([
				('module','=','mw_technic_maintenance'),
				('name','in',['group_maintenance_planner'])])
			group = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
			partners = []
			for receiver in group.users:
				if receiver.partner_id:
					if self.env.user.partner_id.id != receiver.partner_id.id:
						partners.append(receiver.partner_id)
			html = u"<span style='font-size:8pt; font-weight:bold; color:blue;'>Засварын хийгдэх ажлууд:<br/>" + ','.join(msg)+'</span>'
			# self.env.user.send_chat(html, partners)
			self.env.user.send_emails(partners=partners, body=html, attachment_ids=False)

	# Төлөвлөгөөн дээрээс WO үүсгэх - CRON
	def test_run_cron(self):
		self._auto_create_wo_from_plan()

	@api.model
	def _auto_create_wo_from_plan(self):
		# Маргаашын төлөвлөгөө шалгах
		today = datetime.now()
		date_stop = today + timedelta(days=1)
		# plans = self.env['maintenance.plan.line'].search([
		# 	('state','in',['confirmed']),
		# 	('maintenance_type','!=','stopped'),
		# 	('ref_plan_id','=',False),
		# 	'|',('to_delay_date','=',date_stop),
		# 	'&',('date_required','=',date_stop),('to_delay','=',False),
		# 	])
		# 
		plans = self.env['maintenance.plan.line'].search([
			('state','in',['confirmed']),
			('maintenance_type','!=','stopped'),
			('ref_plan_id','=',False),
			('date_required','=',date_stop)
			])
		# Байвал WO үүсгэх
		for line in plans:
			# print '========', line.name
			if not line.workorder_id:
				line.create_workorder()

class RequiredMaterialLine(models.Model):
	_name = 'required.material.line'
	_description = 'Required Material Line'

	# Columns
	parent_id = fields.Many2one('maintenance.plan.line', 'Parent ID', ondelete='cascade')

	template_id = fields.Many2one('product.template', string=u'Темплате', required=True, )
	product_id = fields.Many2one('product.product', string=u'Бараа', readonly=True, compute='compute_product', store=True)
	uom_id = fields.Many2one(related='product_id.uom_id', string=u'Хэмжих нэгж', store=True, readonly=True, )
	categ_id = fields.Many2one(related='product_id.categ_id', string=u'Ангилал', store=True, readonly=True, )
	qty = fields.Float(string=u'Тоо хэмжээ', required=True, default=1, digits=(16,1))
	price_unit = fields.Float(string=u'Нэгж үнэ', required=True, default=0, digits=(16,1))
	is_pm_material = fields.Boolean(string=u'PM материал', default=False, readonly=True, )
	warehouse_id = fields.Many2one('stock.warehouse', string=u'Агуулах', )

	@api.depends('qty','price_unit')
	def _methods_compute(self):
		for obj in self:
			obj.amount = obj.qty * obj.price_unit

	amount = fields.Float(compute=_methods_compute, store=True, string=u'Дүн', digits=(16,1))

	@api.onchange('product_id')
	def onchange_qty(self):
		if self.product_id:
			self.price_unit = self.product_id.lst_price
	
	@api.depends('template_id','template_id.product_variant_ids')
	def compute_product(self):
		for item in self:
			if item.template_id and not item.product_id:
				variants = item.template_id.product_variant_ids
				last_baraa = False
				if variants:
					last_baraa = self.env['product.product'].sudo().search([('id','in',variants.ids)], order='create_date desc', limit=1)
				if not last_baraa:
					raise Warning(('%s (%s)бараа хувилбаргүй байна. /Object id:%s/') % (item.template_id.name,item.template_id.default_code, item.template_id.id))
				item.product_id = last_baraa.id
				# price_unit = last_baraa.standard_price
				# item.price_unit = price_unit

class DependingSeasonMaterial(models.Model):
	_name = 'depending.season.material'
	_description = 'Depending Season Material'
	_order = 'product_id, date_start'

	# Columns
	name = fields.Char(string=u'Тайлбар', copy=False, required=True,
		states={'confirmed':[('readonly',True)]} )
	date_start = fields.Date(string=u'Эхлэх огноо', required=True,
		states={'confirmed':[('readonly',True)]})
	date_end = fields.Date(string=u'Дуусах огноо', required=True,
		states={'confirmed':[('readonly',True)]})

	template_id = fields.Many2one('product.template', string=u'Темплате', copy=False, required=True,
		states={'confirmed':[('readonly',True)]})
	product_id = fields.Many2one('product.product', string=u'Материал', copy=False, compute='compute_product', store=True, readonly=True)
	
	replace_template_id = fields.Many2one('product.template', string=u'Солих Темлате', copy=False, required=True,
		states={'confirmed':[('readonly',True)]})
	replace_product_id = fields.Many2one('product.product', string=u'Солих материал', copy=False, readonly=True)
	user_id = fields.Many2one('res.users', string=u'Хэрэглэгч', readonly=True)

	state = fields.Selection([
		('draft', u'Ноорог'),
		('confirmed', u'Баталсан')],
		string=u'Төлөв', default='draft',
		)

	# ============ Override ===============
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('In order to delete a record, it must be draft first!'))
		return super(DependingSeasonMaterial, self).unlink()

	def action_to_draft(self):
		self.state = 'draft'
	def action_to_confirm(self):
		self.state = 'confirmed'
		self.user_id = self.env.user.id

	# Улирлаас хамаарсан материал бол тохиргоо байгаа эсэхийг шалгаж солих
	def _check_depend_season_material(self, template, dddd):
		conf = self.env['depending.season.material'].search([
			('state','=','confirmed'),
			('template_id','=',template.id),
			('date_start','<=',dddd),
			('date_end','>=',dddd)], limit=1)
		_logger.info("---_check_depend_season_material ====== %s %d %s ", conf, template.id, dddd)
		if conf:
			return conf.replace_template_id
		return template
	
	@api.depends('template_id','template_id.product_variant_ids')
	def compute_product(self):
		for item in self:
			if item.template_id:
				variants = item.template_id.product_variant_ids
				last_baraa = False
				if variants:
					print('variats',variants)
					last_baraa = self.env['product.product'].search([('id','in',variants.ids)], order='create_date desc', limit=1)
				if last_baraa:
					print(last_baraa)
					item.material_id = last_baraa.id
					price_unit = last_baraa.standard_price
					item.price_unit = price_unit
				if not item.material_id:
					print('FUCK', item.generator_id, item.generator_id.parent_id, item.generator_id.technic_id, item.generator_id.technic_id.name, item.template_id.name)
