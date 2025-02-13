# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import time
import pytz

class MaintenanceCall(models.Model):
	_name = 'maintenance.call'
	_description = 'Maintenance Call'
	_order = 'date_required desc'
	_inherit = ['mail.thread']

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,
		states={'open':[('readonly',True)],'to_wo':[('readonly', True)],'closed':[('readonly', True)]}, default=lambda self: self.env.user.branch_id)

	display_name = fields.Char(string="Display_name", compute="_compute_display_name", store=True)
	name = fields.Char(string=u'Дугаар', readonly=True, copy=False )
	description = fields.Text(string=u'Хийгдэх ажил', required=True,
		states={'open': [('readonly', True)],'to_wo': [('readonly', True)],'to_expense': [('readonly', True)],'closed': [('readonly', True)]})
	date = fields.Datetime(string=u'Дуудлага үүсгэсэн огноо', default=datetime.now(), readonly=True)
	date_required = fields.Date(string=u'Дуудлагын огноо', required=True, default=datetime.now().astimezone(pytz.timezone('Asia/Ulaanbaatar')),
		states={'open': [('readonly', True)],'to_wo': [('readonly', True)],'to_expense': [('readonly', True)],'closed': [('readonly', True)]})

	technic_id = fields.Many2one('technic.equipment', string=u'Техник', copy=True,
		help=u"Choose the technic", domain=[('state','in',['stopped','repairing','working'])],
		states={'open': [('readonly', True)],'to_wo': [('readonly', True)],'to_expense': [('readonly', True)],'closed': [('readonly', True)]})
	workorder_id = fields.Many2one('maintenance.workorder', string=u'WorkOrder', readonly=True, copy=False)

	department_id = fields.Many2one('hr.department', string=u'Хэлтэс нэгж', readonly=False)
	user_id = fields.Many2one('res.users', string=u'Клерк', default=_get_user, readonly=True)
	validator_id = fields.Many2one('res.users', string=u'Баталсан', readonly=True, copy=False,)
	close_user_id = fields.Many2one('res.users', string=u'WO хаасан', readonly=True, copy=False,)

	date_open = fields.Datetime(string=u'Нээсэн огноо', readonly=True, copy=False,)
	date_close = fields.Datetime(string=u'Хаасан огноо', readonly=True, copy=False,)

	damaged_type_id = fields.Many2one('maintenance.damaged.type', string=u'Эвдэрлийн төрөл', copy=False,
		states={'open': [('readonly', True)],'to_wo': [('readonly', True)],'to_expense': [('readonly', True)],'closed': [('readonly', True)]})

	# Гүйцэтгэл
	perform_department_id = fields.Many2one('hr.department', string=u'Гүйцэтгэх хэлтэс нэгж',
		states={'to_wo': [('readonly', True)],'to_expense': [('readonly', True)],'closed': [('readonly', True)]})
	expense_id = fields.Many2one('stock.product.other.expense', string=u'Холбоотой шаардах', readonly=True, copy=False)

	# Сэлбэг материалууд зарлага хийх
	required_part_line = fields.One2many('call.required.part.line', 'parent_id', string=u'Шаардлагатай сэлбэг материал зарлагадах',
		states={'draft': [('readonly', True)],'to_wo': [('readonly', True)],'to_expense': [('readonly', True)],'closed': [('readonly', True)]},
		help=u"Бараа зарлагадах мэдээлэл")

	performance_description = fields.Text(u'Хийгдсэн ажил',
		states={'closed': [('readonly', True)]})
	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),],
			string=u'Ээлж', required=True,
		states={'open': [('readonly', True)],'to_wo': [('readonly', True)],'to_expense': [('readonly', True)],'closed': [('readonly', True)]})

	call_type = fields.Selection([
			('technic', u'Техникийн засвар'),
			('medeelel_tech','Мэдээлэл технологи'),
			('grane_job', u'Краны ажил'),
			('welding_job', u'Гагнуурын ажил'),
			('other_repair', u'Аж ахуйн засвар'),
			('medeelel_tech','Мэдээлэл технологи'),],
			string=u'Ажлын хүсэлтийн төрөл', required=True, default='technic',
		states={'open': [('readonly', True)],'to_wo': [('readonly', True)],'to_expense': [('readonly', True)],'closed': [('readonly', True)]})

	state = fields.Selection([
			('draft', u'Ноорог'),
			('open', u'Илгээсэн'),
			('to_wo', u'WO нээсэн'),
			('to_expense', u'Шаардах үүссэн'),
			('closed', u'Хаагдсан'),
			('cancelled', u'Цуцлагдсан'),],
			default='draft', string=u'Төлөв', tracking=True)

	employee_timesheet_lines = fields.One2many('maintenance.employee.timesheet.line', 'parent_id_2', string=u'Ажилтны цаг',
		states={'draft': [('readonly', True)],'closed': [('readonly', True)]},)
	
	@api.depends('employee_timesheet_lines')
	def _compute_worked_manhours(self):
		for obj in self:
			if obj.employee_timesheet_lines:
				time = sum(obj.employee_timesheet_lines.mapped('spend_time'))
				obj.worked_man_hours = time
			else:
				obj.worked_man_hours = 0
	worked_man_hours = fields.Float(string='Ажилласан хүн цаг', store=True, compute='_compute_worked_manhours')

	date_start = fields.Datetime(string=u'Эхлэсэн цаг', copy=False,
		states={'closed': [('readonly', True)]})
	date_end = fields.Datetime(string=u'Дууссан цаг', copy=False,
		states={'closed': [('readonly', True)]})
	@api.depends('date_start','date_end')
	def _compute_time(self):
		for obj in self:
			time = 0
			if obj.date_start and obj.date_end:
				date = obj.date_start
				end_date = obj.date_end
				time = (end_date-date).total_seconds() / (60*60)
				# Зарцуулсан цаг + байх ёстой
				if time < 0:
					raise UserError(_(u'Цагийг зөв оруулна уу! /Дуудлага/'))
			obj.spend_time = time
	spend_time = fields.Float(compute=_compute_time, store=True, string=u'Засварын цаг', readonly=True, )

	current_odometer = fields.Float(string='Тоног төхөөрөмжийн засвар хийх үеийн цаг', digits = (16,1), help="When calling odometer value",
		states={'open': [('readonly', True)],'to_wo': [('readonly', True)],'to_expense': [('readonly', True)],'closed': [('readonly', True)]})
	current_km = fields.Float(string=u'Дуудлага авах үеийн км', digits = (16,1), help="When calling km value",
		states={'open': [('readonly', True)],'to_wo': [('readonly', True)],'to_expense': [('readonly', True)],'closed': [('readonly', True)]})

	contractor_type = fields.Selection([('internal', 'Дотооддоо засварлах'),('external', 'Гадны гүйцэтгэгчээр')], 
		string=u'Perform by', default='internal', 
		states={'to_wo': [('readonly', True)],'to_expense': [('readonly', True)],'closed': [('readonly', True)],'cancelled': [('readonly', True)]})

	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй бичлэгийг устгаж болно!'))
		return super(MaintenanceCall, self).unlink()

	# ===================================== Custom methods ------------------------------
	def action_to_draft(self):
		if self.workorder_id and self.workorder_id.state not in ['draft','cancelled']:
			raise UserError(_(u'Холбоотой WorkOrder байна, цуцлах боломжгүй!'))
		self.state = 'draft'

	def action_to_open(self):
		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code('maintenance.call')
		self.state = 'open'
		self.date_open = datetime.now()
		# Хэлтэс олох
		emp = self.env['hr.employee'].sudo().search([('user_id','=',self.env.user.id)], limit=1)
		if emp:
			self.department_id = emp.department_id.id if emp.department_id else False

		if not self.perform_department_id:
			raise UserError(_(u'Гүйцэтгэх хэлтэс нэгжийг оруулна уу!'))

		self.user_id = self.create_uid.id
		partners = [self.create_uid.partner_id]
		html = u"<span style='font-size:10pt; font-weight:bold; color:red;'>%s ажлын хүсэлтийг хүлээн авлаа!</span>" % (self.name)
		# self.env.user.send_chat(html, partners)
		# self.env.user.send_emails(partners=partners, body=html, attachment_ids=False)

	def action_to_wo_created(self):
		if self.workorder_id and self.state == 'open':
			self.state = 'to_wo'

	def action_create_workorder(self):
		if self.workorder_id:
			raise UserError(_(u'WO үүссэн байна!'))

		origin = ''
		m_type = ''
		if self.call_type == 'welding_job':
			origin = 'daily_welding_job'
			m_type = 'other_repair'
		elif self.call_type == 'grane_job':
			origin = 'crane_job'
			m_type = 'daily_works'
		elif self.call_type=='technic':
			origin = self.name
			m_type = 'not_planned'
		elif self.call_type == 'medeelel_tech':
			origin = self.name
			m_type = 'medeelel_tech'
		else:
			origin = self.name
			m_type = 'other_repair'

		# WO үүсгэх
		print(self.current_odometer)
		vals = {
			'date_required': self.date_required,
			'maintenance_type': m_type,
			'damaged_type_id': self.damaged_type_id.id,
			'origin': origin,
			'branch_id': self.branch_id.id,
			'technic_id': self.technic_id.id,
			'description': self.description,
			'start_odometer': self.current_odometer,
			'shift': self.shift,
			'contractor_type': 'internal',
			'call_id': self.id,
		}
		wo_id = self.env['maintenance.workorder'].create(vals)
		self.workorder_id = wo_id.id
		self.workorder_id.action_to_open()
		# self.workorder_id.name = 'WorkOrder шилжих'
		self.state = 'to_wo'
		self.validator_id = self.env.user.id
		# Timeline set xiix
		for ll in self.employee_timesheet_lines:
			ll.parent_id = wo_id.id

		# Planner луу MSG илгээх
		# partners = self.env['hr.employee'].sudo().search([('job_id.maintenance_job_types', 'in', ['clerk'])]).mapped('partner_id')
		# html = u"<span style='font-size:10pt; font-weight:bold; color:red;'>%s ажлын хүсэлтээс WO үүсгэлээ!</span>" % (self.name)
		# if partners:
		# 	self.env.user.send_chat(html, partners)

	# Шаардах үүсгэх
	def create_expense_request(self):
		if not self.required_part_line:
			raise UserError(_(u'Сэлбэг, материалын мэдээллийг оруулна уу!'))

		emp = self.env['hr.employee'].sudo().search([('user_id','=',self.env.user.id)], limit=1)

		expense = self.env['stock.product.other.expense'].create(
			# Аж ахуйн агуулах
			{'warehouse_id': self.env.user.warehouse_id.id,
			 'branch_id': self.branch_id.id,
			 'state': 'draft',
			 'date_required': self.date_required,
			 'employee_id': emp.id,
			 'description': self.description +' : '+self.name,
			#  'shift': self.shift,
			 'department_id': self.department_id.id,
			})

		for line in self.required_part_line:
			# MOVE үүсгэх
			vals = {
				'parent_id': expense.id,
				'product_id': line.product_id.id,
				'qty': line.qty,
			}
			line_id = self.env['stock.product.other.expense.line'].create(vals)

		self.expense_id = expense.id
		self.state = 'to_expense'

	def view_expense(self):
		self.ensure_one()
		action = self.env.ref('mw_stock_moves.action_stock_product_other_expense_all').read()[0]
		action['domain'] = [('id', '=', self.expense_id.id)]
		view = self.env.ref('mw_stock_moves.maintenance_call_form_view', False)
		view_id = view and view.id or False
		action['views'] = [(view and view.id or False, 'form')]
		action['view_id'] = view_id
		action['res_id'] = self.expense_id.id
		action['view_type'] = 'form'
		action['new'] = 'current'
		return action
	
	def view_wo(self):
		self.ensure_one()
		action = self.env.ref('mw_technic_maintenance.action_maintenance_workorder').read()[0]
		action['domain'] = [('id', '=', self.workorder_id.id)]
		view = self.env.ref('mw_technic_maintenance.maintenance_workorder_form_view', False)
		view_id = view and view.id or False
		action['views'] = [(view and view.id or False, 'form')]
		action['view_id'] = view_id
		action['res_id'] = self.workorder_id.id
		action['view_type'] = 'form'
		action['new'] = 'current'
		return action

	# Дуусгах
	def action_to_close(self):
		if not self.performance_description:
			raise UserError(_(u'Гүйцэтгэсэн ажлыг оруулна уу!'))
		if not self.date_end:
			raise UserError(_(u'Засварын дууссан цагыг оруулан уу!'))
		# Засварчдын ажлын цагийг шалгах
		if not self.employee_timesheet_lines and not self.workorder_id and self.contractor_type == 'internal':
			raise UserError(_(u'Засварчны цагийг оруулна уу! Call'))
		else:
			for line in self.employee_timesheet_lines:
				if not line.date_start or not line.date_end:
					raise UserError(_(u'Засварчны эхэлсэн, дууссан цагийг оруулна уу!'))

		self.date_close = datetime.now()
		self.state = 'closed'
		self.close_user_id = self.env.user.id

	@api.depends('name','technic_id')
	def _compute_display_name(self):
		for record in self:
			if record.name or record.technic_id:
				record.display_name = record.name if record.name else ''
			else:
				record.display_name = ' '

class CallRequiredPartLine(models.Model):
	_name = 'call.required.part.line'
	_description = 'Call Required Part Line'

	# Columns
	parent_id = fields.Many2one('maintenance.call', 'Parent ID', ondelete='cascade')

	product_id = fields.Many2one('product.product', string=u'Бараа', required=True, )
	uom_id = fields.Many2one(related='product_id.uom_id', string=u'Хэмжих нэгж', store=True, readonly=True, )
	qty = fields.Float(string=u'Тоо хэмжээ', required=True, default=1,)
