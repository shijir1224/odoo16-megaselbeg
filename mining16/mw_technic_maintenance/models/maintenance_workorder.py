# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime, time, timedelta
import collections
import logging
_logger = logging.getLogger(__name__)
import time
import pytz
MAINTENANCE_TYPE = [
			('main_service', u'Урсгал засвар'),
			('pm_service', u'PM үйлчилгээ'),
			('planned', u'Planned'),
			('not_planned', u'Төлөвлөгөөт бус'),
			('component_repair', u'Компонент засвар'),
			('hose_repair', u'Hose repair'),
			('tire_service', u'Tire service'),
			('daily_works', u'Өдөр тутмын ажил'),
			('other_repair', u'Засварын бусад ажил'),
			('other_repair2', u'Няряд, ээлж хүлээлцэх'),
			('other_repair3', u'Хуваарьт үзлэг'),
			('other_repair4', u'Тосолгоо'),
			('other_repair5', u'Бусад'),
]

# Change order date
class WorkOrderChangeDate(models.TransientModel):
	_name = 'workorder.change.date'
	_description = u'WorkOrder change date'

	date = fields.Date('Солих Огноо', required=True)
	shift = fields.Selection([
		('day', u'Өдөр'),
		('night', u'Шөнө'),],
		string='Ээлж', required=True, )

	def set_to_date(self):
		if self._context['wo_id']:
			obj = self.env['maintenance.workorder'].browse(self._context['wo_id'])
			if obj.state != 'open':
				obj.date_required = self.date
				obj.shift = self.shift

class SelectedMaintenanceWorkorderOpen(models.TransientModel):
	_name = "selected.maintenance.workorder.open"
	_description = "selected maintenance workorder open"

	def action_open(self):
		obj_ids = self.env['maintenance.workorder'].browse(self._context['active_ids'])
		for wo in obj_ids:
			if wo.state == 'draft':
				wo.action_to_open()

	def action_done(self):
		obj_ids = self.env['maintenance.workorder'].browse(self._context['active_ids'])
		for wo in obj_ids:
			if wo.state == 'processing':
				wo.action_to_done()

class SelectedMaintenanceWorkorderInvoice(models.TransientModel):
	_name = "selected.wo.invoice"
	_description = "selected maintenance workorder create invoice"

	def _compute_partner(self):
		return self.env['maintenance.workorder'].search([]).mapped('technic_partner_id').ids

	partner_id = fields.Many2one('res.partner', string='Харилцагч', required=True)
	posible_partner_ids = fields.Many2many('res.partner', string='Partners', default=_compute_partner)
	workorder_ids = fields.Many2many('maintenance.workorder', string='Workorder')
	invoice_line_ids = fields.One2many('selected.wo.invoice.line', 'parent_id', string='Нэхэмжлэх мөрүүд')
	date = fields.Date(string='Огноо', help='Нэхэмжлэлийн огноо')

	def get_lines(self):
		self.invoice_line_ids = []
		wo_ids = self.env['maintenance.workorder'].browse(self._context['active_ids']).filtered(lambda r: r.state in ['done','closed'])
		for item in wo_ids:
			item.create_add_timesheet()
		lines = []
		for line in wo_ids.mapped('required_part_line'):
			old_idx = False
			for idx, x in enumerate(lines):
				_logger.info('looping')
				if lines[idx][2]['product_id'] == line.product_id.id:
					old_idx = idx
					break
			# _logger.info('%s' % (lines))
			if old_idx:
				lines[old_idx][2]['qty'] += line.qty
				lines[old_idx][2]['part_line_ids'] += [line.id] 
				# _logger.info('Yeap %s %s' % (line.product_id.name, line.product_id.id))
			else:
				# _logger.info('Okeyyy %s %s' % (line.product_id.name, line.product_id.id))
				lines.append((0,0,{
					'parent_id': self.id,
					'product_id': line.product_id.id,
					'qty': line.qty,
					'price_unit': line.price_unit,
					'part_line_ids': [line.id]
			}))	
		self.invoice_line_ids = lines
		self.workorder_ids = wo_ids.ids
		action = self.env.ref('mw_technic_maintenance.selected_maintenance_workorder_invoice_action').read()[0]
		action['res_id'] = self.id
		return action

	def create_invoice(self):
		if not self.env.user.has_group('mw_technic_maintenance.group_maintenance_invoice_user'):
			raise Warning(('Танд WO-с Нэхэмжлэл үүсгэх эрх байхгүй байна.! Систем админд хандана уу!'))
		if not self.invoice_line_ids:
			raise Warning(('Нэхэмжлэл мөрүүд хоосон байна!'))
		wo_ids = self.workorder_ids
		created_invoices = wo_ids.mapped('invoice_ids').filtered(lambda r: r.state != 'cancel')
		if created_invoices:
			raise Warning(('Нэхэмжлэл үүссэн байна! (%s)' % (', '.join(created_invoices.mapped('workorder_ids.name')))))
		invoice_line_ids = []
		for wo in wo_ids:
			invoice_line_ids += wo._get_material_lines()
			invoice_line_ids += wo._get_manhour_lines()
		if invoice_line_ids:
			journal = self.env['account.journal'].search([('type','=','sale')], limit=1)
			invoice_id = self.env['account.move'].create({
				'ref': ', '.join(self.workorder_ids.mapped('name')),
				'move_type': 'out_invoice',
				'company_id': wo_ids.mapped('company_id')[0].id,
				'partner_id': self.partner_id.id if self.partner_id else False,
				'journal_id': journal.id or False,
				'currency_id': wo_ids.mapped('company_id')[0].currency_id.id,
				'invoice_line_ids': invoice_line_ids,
				'invoice_date': self.date,
				'date': self.date,
				'workorder_ids': self.workorder_ids.ids,
			})
			wo_ids.write({'invoice_ids': [(4,invoice_id.id)]})
			print('fucking invoice', wo_ids, wo_ids.mapped('invoice_ids'))
			self.ensure_one()
			action = self.env.ref('account.action_move_out_invoice_type').read()[0]
			view = self.env.ref('account.view_move_form')
			view_id = view and view.id or False
			action['views'] = [(view and view.id or False, 'form')]
			action['view_id'] = view_id
			action['res_id'] = invoice_id.id
			action['view_type'] = 'form'
			action['target'] = 'current'
			return action

class selectedWoInvoiceLine(models.TransientModel):
	_name = 'selected.wo.invoice.line'
	_description = "Selected WOs lines for create invoice"
	
	parent_id = fields.Many2one('selected.wo.invoice', readonly=True, string='Parent ID')
	product_id = fields.Many2one('product.product', string='Product', required=True)
	qty = fields.Float(string='QTY', deaful=0)
	price_unit = fields.Float(string='Price Unit')
	uom_id = fields.Many2one(related='product_id.uom_id', string='Unit measure')
	part_line_ids = fields.Many2many('required.part.line', string='WO lines', readonly=True)
	line_type = fields.Selection([('product','Бараа материал'),('service','Үйлчилгээ')], compute='_compute_type', default='product', readonly=True)

	def _compute_type(self):
		for item in self:
			if item.product_id.type == 'product':
				item.line_type = 'product'
			else:
				item.line_type = 'service'

	@api.onchange('product_id')
	def onchange_product(self):
		self.write({'price_unit': item.product_id.standart_price for item in self if item.product_id.type == 'product'})


class PurchaseRequest(models.Model):
	_inherit = 'purchase.request'

	maintenance_workorder_id = fields.Many2one('maintenance.workorder', 'Холбоотой WO')

class dynamicFlowHistory(models.Model):
	_inherit = 'dynamic.flow.history'

	workorder_id = fields.Many2one('maintenance.workorder', string=u'Workorder ID')

class MaintenanceWorkOrder(models.Model):
	_name = 'maintenance.workorder'
	_description = 'Maintenance work order'
	_order = 'date_required desc, name'
	_inherit = ['mail.thread']

	@api.model
	def _get_user(self):
		return self.env.user.id

	@api.model
	def get_maintenance_type(self):
		return MAINTENANCE_TYPE

	# Columns
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id)
	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True, default=lambda self: self.env.user.branch_id,
		states={'waiting_part':[('readonly',True)],'done':[('readonly',True)],'closed':[('readonly',True)]})

	name = fields.Char(u'Дугаар', readonly=True, copy=False )
	print_count = fields.Integer(string=u'Хэвлэлт', readonly=True, default=0)
	origin = fields.Char(u'Origin',
		states={'waiting_part':[('readonly',True)],'done':[('readonly',True)],'closed':[('readonly',True)]},)
	plan_id = fields.Many2one('maintenance.plan.line', u'Холбоотой төлөвлөгөө', readonly=True)

	workorder_rate = fields.Selection([
		('0', u'Empty'),
		('1', u'Too bad'),
		('2', u'Bad'),
		('3', u'Дунд'),
		('4', u'Good'),
		('5', u'Excellent'),],
 		string=u'Үнэлгээ', default=0, required=False,
		states={'draft': [('readonly', True)],'open': [('readonly', True)],'waiting_part': [('readonly', True)],
		'processing': [('readonly', True)],'closed': [('readonly', True)]})

	workorder_rate_description_id = fields.Many2one('workorder.rate.description', u'Үнэлгээний тайлбар', copy=False,
		states={'waiting_part':[('readonly',True)],'closed':[('readonly',True)]})
	is_checked = fields.Boolean(string=u'Хянасан эсэх',)
	is_checked_user = fields.Many2one('res.users' , string=u'Хянасан ажилтан')

	maintenance_type_id = fields.Many2one('maintenance.type', u'PM төрөл', copy=False,
		states={'done':[('readonly',True)],'closed':[('readonly',True)]},
		domain=[('is_pm','=',True)])
	pm_priority = fields.Integer(u'PM ийн дугаар', default=0,
		states={'done': [('readonly', True)],'closed': [('readonly', True)]})

	priority = fields.Selection([
		('1', u'1-Маш Яаралтай'),
		('2', u'2-Яаралтай'),
		('3', u'3-Энгийн'),],
		string=u'Зэрэглэл', default='3', required=True,
		states={'waiting_part': [('readonly', True)],'processing': [('readonly', True)],
			'done': [('readonly', True)],'closed': [('readonly', True)]})

	description = fields.Text(u'Хийгдэх ажил', required=True,
		states={'ready': [('readonly', True)], 'done': [('readonly', True)],'closed': [('readonly', True)]})
	date = fields.Datetime(u'Үүсгэсэн огноо', default=datetime.now(), readonly=True)
	date_required = fields.Date(u'Хийгдэх огноо', required=True, tracking=True, default=fields.Date.context_today,
		states={'open': [('readonly', True)],'reopen': [('readonly', True)],'analysing': [('readonly', True)],'waiting_part': [('readonly', True)],
			'ready': [('readonly', True)], 'done': [('readonly', True)],'closed': [('readonly', True)]})

	technic_id = fields.Many2one('technic.equipment', string=u'Техник', copy=True,
		help=u"Choose the technic",
		domain=[('state','not in',['draft'])])
		# states={'reopen': [('readonly', True)],'analysing': [('readonly', True)],'waiting_part': [('readonly', True)],
		# 	'ready': [('readonly', True)], 'done': [('readonly', True)],'closed': [('readonly', True)]})
	operator_id = fields.Many2one('hr.employee', string=u'Оператор')
	operator_partner_id = fields.Many2one('res.partner', string=u'Оператор')
	start_odometer = fields.Float(string='Эхлэх гүйлт', digits = (16,1), help="When starting odometer value",
		states={'closed': [('readonly', True)]})
	finish_odometer = fields.Float(string='Дууссан гүйлт', digits = (16,1), help="When finished odometer value",
		states={'closed': [('readonly', True)]})
	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),],
		string=u'Ээлж',
		states={'waiting_part': [('readonly', True)],'processing': [('readonly', True)],
			'done': [('readonly', True)],'closed': [('readonly', True)]})

	# Засварын нийт цагийг бодох
	@api.depends('work_timesheet_lines')
	def _compute_total_time(self):
		for obj in self:
			time = 0
			for ll in obj.work_timesheet_lines:
				date = ll.date_start
				end_date = ll.date_end
				time += (end_date-date).total_seconds() / (60*60)
			obj.total_spend_time = time
	total_spend_time = fields.Float(string='Үргэлжилсэн цаг', store=True, compute='_compute_total_time')

	# Төлөвлөсөн цаг
	planned_time_line = fields.One2many('wo.planned.time.line', 'parent_id', string=u'Төлөвлөсөн цагийн мөр',
		states={'closed': [('readonly', True)]},
		)
	@api.depends('planned_time_line')
	def _compute_planned_time(self):
		for obj in self:
			obj.planned_time = sum(obj.planned_time_line.mapped('planned_time'))
	planned_time = fields.Float(string=u'Нийт төлөвлөсөн цаг', help=u'Засварын ажлын төлөвлөсөн цаг',
		store=True, compute='_compute_planned_time', )
	planned_mans = fields.Integer(string=u'Ажиллах хүн',
		states={'done': [('readonly', True)],'closed': [('readonly', True)]})
	
	# @api.onchange('employee_timesheet_lines')
	# def onchange_planned_mans(self):
	# 	for item in self:
	# 		if item.employee_timesheet_lines:
	# 			item.write({'planned_mans':len(item.employee_timesheet_lines)})
	@api.depends('planned_time_line')
	def _compute_planned_time(self):
		for obj in self:
			if obj.planned_time_line:
				obj.planned_time = sum(obj.planned_time_line.mapped('planned_time'))
			else:
				obj.planned_time = 0
	
	@api.depends('planned_time','planned_mans')
	def _compute_man_hours(self):
		for obj in self:
			obj.planned_man_hours = obj.planned_time * obj.planned_mans
	planned_man_hours = fields.Float(string=u'Төлөвлөсөн хүн цаг', readonly=True,
		store=True, compute='_compute_man_hours', )

	@api.depends('employee_timesheet_lines','employee_timesheet_lines.date_start','employee_timesheet_lines.date_end')
	def _compute_worked_manhours(self):
		for obj in self:
			if obj.employee_timesheet_lines:
				time = sum(obj.employee_timesheet_lines.mapped('spend_time'))
				obj.worked_man_hours = time
			else:
				obj.worked_man_hours = 0

	@api.depends()
	def _compute_maintenance_hours(self):
		for item in self:
			if item.work_timesheet_lines:
				item.total_maintenance_hours = sum(item.work_timesheet_lines.mapped('spend_time'))
			else:
				item.total_maintenance_hours = 0

	worked_man_hours = fields.Float(string='Ажилласан хүн цаг', store=True, compute='_compute_worked_manhours')
	total_maintenance_hours = fields.Float(string='Засварын нийт цаг', compute='_compute_maintenance_hours')

	other_service_title = fields.Char(u'Бусад хийгдэх ажил', copy=False,
		states={'reopen': [('readonly', True)],'analysing': [('readonly', True)],'waiting_part': [('readonly', True)],
			'ready': [('readonly', True)], 'done': [('readonly', True)],'closed': [('readonly', True)]} )

	warehouse_id = fields.Many2one('stock.warehouse', u'Агуулах', copy=False,
		states={'done': [('readonly', True)],'closed': [('readonly', True)]})

	user_id = fields.Many2one('res.users', u'Клерк', default=_get_user, readonly=True)
	# user_warehouse_id = fields.Many2one(related="user_id.warehouse_id", string=u'REF warehouse', readonly=True, store=True, copy=False)

	validator_id = fields.Many2one('res.users', u'Баталсан хэрэглэгч', copy=False,
		states={'done': [('readonly', True)],'closed': [('readonly', True)]})
	close_user_id = fields.Many2one('res.users', u'Хаасан хэрэглэгч', readonly=True, copy=False,)

	date_open = fields.Datetime(u'Нээсэн огноо', readonly=True, copy=False,)
	date_reopen = fields.Datetime(u'Дахин нээсэн огноо', readonly=True, copy=False,)
	date_start = fields.Datetime(u'Эхэлсэн огноо', readonly=True, copy=False,)
	date_done = fields.Datetime(u'Дууссан огноо', readonly=True, copy=False,)
	date_closed = fields.Datetime(u'Хаасан огноо', readonly=True, copy=False,)

	maintenance_type = fields.Selection(MAINTENANCE_TYPE,
			string=u'Засварын төрөл', required=True,
			states={'done': [('readonly', True)],'closed': [('readonly', True)]}, default="main_service"
		)
	is_warrenty = fields.Boolean(string=u'Warranty эсэх', default=False,
		states={'waiting_part': [('readonly', True)],'processing': [('readonly', True)],
			'done': [('readonly', True)],'closed': [('readonly', True)]})
	is_rework = fields.Boolean(string='ReWork эсэх', default=False,
		# states={'waiting_part': [('readonly', True)],'processing': [('readonly', True)],'done': [('readonly', True)],'closed': [('readonly', True)]}\
		)

	damaged_reason_id = fields.Many2one('maintenance.damaged.reason', string=u'Эвдрэлийн шалтгаан', copy=False,
		states={'closed': [('readonly', True)]})
	damaged_type_id = fields.Many2one('maintenance.damaged.type', string=u'Эвдрэлийн төрөл', copy=False,
		states={'closed': [('readonly', True)]})

	into_smr_report = fields.Boolean(u'SMR-д орох эсэх', )
	comment_smr_report = fields.Text(u'SMR-тайлбар', )

	contractor_type = fields.Selection([
			('internal', u'Дотооддоо засварлах'),
			('external', u'Гадны гүйцэтгэгчээр'),],
			string=u'Perform by', default='internal',
			states={'reopen': [('readonly', True)],'analysing': [('readonly', True)],'waiting_part': [('readonly', True)],
			'ready': [('readonly', True)], 'done': [('readonly', True)],'closed': [('readonly', True)]}
		)
	partner_id = fields.Many2one('res.partner', u'Гүйцэтгэх харилцагч', copy=False,
		states={'done': [('readonly', True)],'closed': [('readonly', True)]}
		)
	payment_type = fields.Selection([
			('cash', u'Cash'),
			('bank', u'Bank'),],
			string=u'Төлбөрийн хэлбэр',
			states={'reopen': [('readonly', True)],'analysing': [('readonly', True)],'waiting_part': [('readonly', True)],
				'ready': [('readonly', True)], 'done': [('readonly', True)],'closed': [('readonly', True)]}
		)
	# Нэхэмжлэл
	invoice_id = fields.Many2one('account.move', string=u'Холбоотой нэхэмжлэх', readonly=True, )
	invoice_ids = fields.Many2many('account.move', string='Хамааралтай Нэхэмжлэл')
	invoice_count = fields.Integer(string='Нэхэмжлэх тоо', compute='_compute_invoice_count')
	invoice_date = fields.Date('Invoice created date')

	# Сэлбэг материалууд зарлага хийх
	required_part_line = fields.One2many('required.part.line', 'parent_id', string=u'Шаардлагатай сэлбэг материал зарлагадах',
		states={'ready': [('readonly', True)],'done': [('readonly', True)],'closed': [('readonly', True)]},
		help=u"Бараа зарлагадах мэдээлэл")

	# Сэлбэг материалууд ХА хийх
	required_part_line_2 = fields.One2many('required.part.line', 'parent_id_2', string=u'Шаардлагатай сэлбэг материал ХА',
		states={'closed': [('readonly', True)]},
		help=u"Бараа материал худалдан авах мэдээлэл")
	po_description = fields.Text(string=u'Худалдан авалттай холбоотой мэдээлэл', help=u"Худалдан авалттай холбоотой мэдээлэл",
		states={'closed': [('readonly', True)]})

	# Хэрэглэсэн сэлбэг материалууд
	wo_move_lines = fields.One2many('stock.move', 'maintenance_workorder_id', string=u'Хэрэглэсэн сэлбэг материал',
		readonly=True, help=u"Засварын ажилд хэрэглэгдсэн сэлбэг материал")

	# Компонент эд анги
	repair_component_id = fields.Many2one('technic.component.part', string=u'Засварлах компонент',
		domain=[('state','=','inactive')],
		states={'reopen': [('readonly', True)],'analysing': [('readonly', True)],'waiting_part': [('readonly', True)],
			'ready': [('readonly', True)], 'done': [('readonly', True)],'closed': [('readonly', True)]})
	component_maintenance_type = fields.Selection([
		('exchange','Exchange'),
		('overhaul','Overhaul'),
		('reseal','Reseal')], string=u'Компонент засварын төрөл', )

	component_repair_type = fields.Selection(
			[('remove', u'Салгах'),
			 ('install', u'Угсрах'),], string=u'Компонент угсрах, салгах',
		states={'ready': [('readonly', True)],'done': [('readonly', True)],'closed': [('readonly', True)]} )
	remove_component_id = fields.Many2one('technic.component.part', string=u'Салгах компонент',
		states={'ready': [('readonly', True)],'done': [('readonly', True)],'closed': [('readonly', True)]})
	install_component_id = fields.Many2one('technic.component.part', string=u'Угсрах компонент',
		states={'ready': [('readonly', True)],'done': [('readonly', True)],'closed': [('readonly', True)]})
	is_field_test = fields.Boolean(string='Field Test', default=False,
		states={'ready': [('readonly', True)],'done': [('readonly', True)],'closed': [('readonly', True)]})
	remove_component_ids = fields.Many2many('technic.component.part','remove_comp_from_tech','technic_id','component_id', string=u'Салгах компонент',
		states={'ready': [('readonly', True)],'done': [('readonly', True)],'closed': [('readonly', True)]})
	install_component_ids = fields.Many2many('technic.component.part','install_comp_to_tech','technic_id','component_id', string=u'Угсрах компонент',
		states={'ready': [('readonly', True)],'done': [('readonly', True)],'closed': [('readonly', True)]})

	# Ашигласан багаж
	use_equipment_line = fields.One2many('use.equipment.line', 'parent_id', string=u'Хэрэглэсэн багаж хэрэгсэл',
		states={'draft': [('readonly', True)],'done': [('readonly', True)],'closed': [('readonly', True)]})

	expense_picking_id = fields.Many2one('stock.picking', string=u'Зарлага хийсэн хөдөлгөөн', readonly=True, copy=False,)
	expense_state = fields.Selection(related="expense_picking_id.state", string=u'Зарлагын төлөв',
		readonly=True, tracking=True, help=u"Зарлагын төлөв")
	# po_request_id = fields.Many2one('purchase.request', string=u'Худалдан авалтын хүсэлт', readonly=True, copy=False,)
	pr_count = fields.Integer(compute='_pr_count', string='Худалдан авалтын хүсэлтийн тоо', default=0)
	po_request_ids = fields.Many2many('purchase.request', string=u'Худалдан авалтын хүсэлтүүд', readonly=True)

	# Гүйцэтгэл
	performance_description = fields.Text(string=u'Performance description', tracking=True,
		states={'closed': [('readonly', True)]})

	employee_timesheet_lines = fields.One2many('maintenance.employee.timesheet.line', 'parent_id', string=u'Employee timesheet',
		states={'draft': [('readonly', True)],'closed': [('readonly', True)]},)

	# Ажилтаны цагийг хялбараар оруулах
	temp_date_start = fields.Datetime(string=u'Эхлэх цаг', copy=False,
		help="Ажилтны цагийг олноор нь хялбар оруулах үед ашиглана")
	temp_date_end = fields.Datetime(string=u'Дуусах цаг', copy=False,
		help="Ажилтны цагийг олноор нь хялбар оруулах үед ашиглана")

	def update_worked_man_hours(self):
		query = """
			select round(sum(l.spend_time)::integer,0),round(w.worked_man_hours::integer,0),w.id from maintenance_workorder w
			left join maintenance_employee_timesheet_line l on l.parent_id=w.id
			group by w.worked_man_hours,w.id
			having round(sum(l.spend_time)::integer,0)!=round(w.worked_man_hours::integer,0)
		"""
		self.env.cr.execute(query)
		wo_numbers = self.env.cr.dictfetchall()
		for item in wo_numbers:
			self.env['maintenance.workorder'].browse(item['id'])._compute_worked_manhours()

	def set_employee_time(self):
		if self.temp_date_start and self.temp_date_end:
			for ll in self.employee_timesheet_lines:
				if not ll.date_start:
					ll.date_start = self.temp_date_start
				if not ll.date_end:
					ll.date_end = self.temp_date_end
			# Засварын ажлыг оруулах
			reason = self.env['maintenance.delay.reason'].search([('is_maintenance_reason','=',True)], limit=1)
			if reason:
				timelines = self.env['maintenance.work.timesheet.line'].search([
					('delay_reason_id','=',reason.id),
					('parent_id','=',self.id),])
				if not timelines:
					vals = {
						'parent_id': self.id,
						'delay_reason_id': reason.id,
						'date_start': self.temp_date_start,
						'date_end': self.temp_date_end,
					}
					self.env['maintenance.work.timesheet.line'].create(vals)

	work_timesheet_lines = fields.One2many('maintenance.work.timesheet.line', 'parent_id', string=u'Timesheet',
		states={'draft': [('readonly', True)],'closed': [('readonly', True)]},)
	next_work_description = fields.Text(u'Хойшид хийгдэх ажил',
		states={'closed': [('readonly', True)]})
	ref_workorder_id = fields.Many2one('maintenance.workorder', string='Холбоотой WO', readonly=True, )
	next_work_state = fields.Selection([
			('pending', u'Хийгдээгүй'),
			('cancelled', u'Цуцалсан, хийхгүй'),
			('wo_created', u'Ажил үүсгэсэн'),],
			default='pending', string=u'Хойшид хийгдэх ажлын төлөв')

	state = fields.Selection([
			('draft', u'Draft'),
			('open', u'Open'),
			('reopen', u'Reopen'),
			('analysing', u'Analysing'),
			('waiting_part', u'Waiting for parts'),
			('ordered_part', u'Ordered for parts'),
			('waiting_labour', u'Waiting labour'),
			('ready', u'Ready'),
			('processing', u'Processing'),
			('done', u'Done'),
			('closed', u'Closed'),
			('cancelled', u'Cancelled'),],
			default='draft', string=u'State', tracking=True)

	# Туршлагын санд нэмсэн эсэх
	is_experience_info = fields.Boolean(string=u'Туршлагын санд нэхэм эсэх', default=False, readonly=True, )
	attachment_ids = fields.Many2many('ir.attachment', 'wo_attachment_rel', 'wo_id', 'attachment_id', string=u'Хавсралтууд', )

	inspection_id = fields.Many2one('technic.inspection', u'Техникийн үзлэг', readonly=True, )
	call_id = fields.Many2one('maintenance.call', string="Дуудлага")

	is_depend_technic = fields.Boolean(string=u'Техникийн төлөвт нөлөөлөх эсэх', default=True, readonly=True,
		states={'draft': [('readonly', False)],'open': [('readonly', False)]})

	def _pr_count(self):
		for rec in self:
			rec.pr_count = len(rec.po_request_ids)

	def all_methods_compute(self):
		for item in self.search([]):
			item._methods_compute()
	# Зарлагын дүнгүүд + PM
	@api.depends('wo_move_lines','wo_move_lines.state')
	def _methods_compute(self):
		for obj in self:
			tot = 0
			for line in obj.wo_move_lines.filtered(lambda r: r.state!='cancel'):
				tot_am = line.price_unit * line.product_qty
				if line.location_id.usage!='internal':
					tot_am = -1*tot_am
				tot += tot_am
			obj.total_expense_amount = tot
	total_expense_amount = fields.Float(compute=_methods_compute,
		store=True, string=u'Нийт зарлага')

	# PM ийн материал ороогүй зарлага буюу Батлах дүн
	total_no_pm_amount = fields.Float(string=u'Батлах дүн', readonly=True, default=0)
	total_invoice_amount = fields.Float(string=u'Нэхэмжлэл дүн', readonly=True, compute='compute_invoice_amount')
	# PO зардал
	@api.depends('required_part_line_2')
	def _methods_compute_2(self):
		for obj in self:
			tot = 0
			for line in obj.required_part_line_2:
				tot += line.amount
			obj.total_po_amount = tot
	total_po_amount = fields.Float(compute=_methods_compute_2, store=True, string=u'Нийт худалдан авах')

	@api.depends('required_part_line','required_part_line.price_unit', 'required_part_line.qty')
	def compute_invoice_amount(self):
		for item in self:
			material_cost = sum(item.required_part_line.filtered(lambda r: r.product_id.type == 'product').mapped('product_id.standard_price'))
			mamhour_cost = sum(item.required_part_line.filtered(lambda r: r.product_id.type == 'service').mapped('product_id.lst_price'))
			item.total_invoice_amount = material_cost + mamhour_cost

	# Нийт сэлбэгийн зардал + PO
	@api.depends('total_po_amount','total_expense_amount')
	def _methods_compute_3(self):
		# Нийт тоог олгох
		for obj in self:
			obj.total_amount_spare = obj.total_po_amount + obj.total_expense_amount
	total_amount_spare = fields.Float(compute=_methods_compute_3, store=True,
		string=u'Сэлбэг материал нийт',
		help=u'Засварт шаардлагатай нийт сэлбэг материалын дүн')

	# Ажилчдын зардал
	@api.depends('employee_timesheet_lines')
	def _methods_compute_employee_expense(self):
		for obj in self:
			tot = 0
			for line in obj.employee_timesheet_lines:
				tot += line.spend_time * 5000
			obj.total_employee_expense_amount = tot
	total_employee_expense_amount = fields.Float(compute=_methods_compute_employee_expense,
		store=True, string=u'Ажилчдын зардал')

	warning_messages = fields.Html('Анхааруулага', compute='_compute_wc_messages')

	# Constraint
	_sql_constraints = [('wo_name_uniq', 'unique(name)','Name must be unique!')]

	# ==================================== Over rided --------------------------
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError((u'Ноорог төлөвтэй бичлэгийг устгаж болно!'))
			if self.env['stock.picking'].search([('maintenance_workorder_id','=',s.id),('state','!=','cancel')]):
				raise UserError((u'Холбоотой зарлага байна устгах боломжгүй!'))
		return super(MaintenanceWorkOrder, self).unlink()

	# ===================================== Custom methods ------------------------------
	# Төлөвлөсөн цагийн мөр үүсгэх
	def _create_planned_time_line(self, planned):
		temp = [(0,0,{
					'planned_date': self.date_required,
					'planned_time': planned,
			})]
		self.planned_time_line = temp

	def set_to_date(self):
		con = dict(self._context)
		con['wo_id'] = self.id
		con['shift'] = self.shift
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'workorder.change.date',
			'view_mode': 'form',
			'context': con,
			'target': 'new',
		}

	def action_to_cancel(self):
		if self.state == 'draft':
			self.state = 'cancelled'
		else:
			raise UserError((u'%s ажил эхэлсэн байна!' % self.name))

	def action_to_return(self):
		if not self.performance_description:
			raise UserError((u'Гүйцэтгэлтэй холбоотой мэдээллийг оруулна уу!'))
		self.state = 'cancelled'

	def action_to_draft(self):
		not_done = self.wo_move_lines.filtered(lambda l: l.state != 'cancel')
		if not_done:
			raise UserError((u'WO цуцлах боломжгүй, цуцлах шаардлагатай бол зарлагын баримтыг эхлээд цуцлуулна уу!'))
		self.state = 'draft'

	# def _set_wo_sequence(self):
	# 	temp = '1'
	# 	wos = self.env['maintenance.workorder'].search([
	# 		('date_required','=',self.date_required),
	# 		('name','!=',False)], order='name desc')
	# 	if wos:
	# 		print(wos)
	# 		_logger.info(u'-***********-NEW WO NUMBER--************* %d \n' % wos[0].id)
	# 		_logger.info(u'-***********-TOTAL WO NUMBER of %s --************* %d \n' % (self.date_required, len(wos)))
	# 		if wos:
	# 			i = 0
	# 			for item in wos.mapped('name'):
	# 				if datetime.strftime(self.date_required, '%y%m%d') in item:
	# 					i += 1
	# 			temp = str(i + 1)
	# 	date_required = datetime.strftime(self.date_required,'%Y-%m-%d')
	# 	number = 'WO'+date_required[2:4]+date_required[5:7]+date_required[8:]+'-'+ temp.zfill(3)
	# 	return number

	def _set_wo_sequence(self):
		temp = '1'
		n = 0
		date = datetime.strftime(self.date_required,'%y%m%d')
		query = """SELECT max(w.name) FROM maintenance_workorder as w WHERE name like '%{0}%'""".format(date)
		self.env.cr.execute(query)
		wo_number = self.env.cr.dictfetchall()
		if not wo_number[0]['max'] is None:
			n = int(wo_number[0]['max'][9:])
		temp = str(n + 1)
		_logger.info(u'-***********-NEW WO ID & NUMBER--*************mining*** %d & %s \n' % (self.id, temp))
		date_required = datetime.strftime(self.date_required,'%Y-%m-%d')
		number = 'WO'+date_required[2:4]+date_required[5:7]+date_required[8:]+'-'+ temp.zfill(3)
		return number

	def action_to_open(self):
		if not self.name:
			# self.name = self.env['ir.sequence'].next_by_code('maintenance.workorder')
			self.name = self._set_wo_sequence()
		# Хэрэв HOSE repair бол зөв урсгалыг хайх
		# байхгүй бол default урсгалаар явна
		if self.maintenance_type == 'hose_repair':
			flow = self.env['dynamic.flow'].sudo().search([
				('company_id','=',self.company_id.id or self.env.user.company_id.id),
				('model_id.model','=','maintenance.workorder'),
				('description','=','hose')], limit=1)
			if flow:
				self.flow_id = flow.id
				self.flow_line_id = self.flow_find().id
				self.flow_line_next_id = self.flow_find()._get_next_flow_line()
		# Хэрэв дугуйн ажил байгаад тусдаа урсгалтай бол олох
		elif self.maintenance_type == 'tire_service':
			flow = self.env['dynamic.flow'].sudo().search([
				('company_id','=',self.company_id.id or self.env.user.company_id.id),
				('model_id.model','=','maintenance.workorder'),
				('description','=','tire')], limit=1)
			if flow:
				self.flow_id = flow.id
				self.flow_line_id = self.flow_find().id
				self.flow_line_next_id = self.flow_find()._get_next_flow_line()
		elif not self.flow_id:
			flow = self.env['dynamic.flow'].sudo().search([
				('company_id','=',self.company_id.id or self.env.user.company_id.id),
				('model_id.model','=','maintenance.workorder')], order='sequence', limit=1)
			if flow:
				self.flow_id = flow.id
				self.flow_line_id = self.flow_find().id
				self.flow_line_next_id = self.flow_find()._get_next_flow_line()

		# Хэрэв гараар үүсгэсэн PM бол
		# материалыг нь үүсгэх
		if self.maintenance_type == 'pm_service' and self.maintenance_type_id and self.pm_priority and not self.plan_id:
			# PM материал өмнө нь үүссэн бол
			# Дахиж үүсгэхгүй байх шалгах
			# if not self.required_part_line.filtered(lambda l: l.is_pm_material == True):
			pm_config = self.env['maintenance.pm.material.config'].search([
				('maintenance_type_id','=',self.maintenance_type_id.id),
				('priority','=',self.pm_priority),
				('technic_setting_id','=',self.technic_id.technic_setting_id.id)], limit=1)
			if pm_config:
				for line in pm_config.pm_material_line:
					vline = {
						'product_id': line.material_id.id,
						'qty': line.qty,
						'parent_id': self.id,
						'is_pm_material': True,
						'src_warehouse_id': line.warehouse_id.id
					}
					self.env['required.part.line'].create(vline)
				# Үлдэгдлийг шалгах
				self.check_product_qty()

		self.state = 'open'
		self.date_open = datetime.now()
		self.cancel_flow()
		# # Chat илгээх
		# res_model = self.env['ir.model.data'].search([
		# 		('module','=','mw_technic_maintenance'),
		# 		('name','=','group_maintenance_planner')])
		# group = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
		# partners = []
		# for receiver in group.users:
		# 	if receiver.partner_id:
		# 		if self.env.user.partner_id.id != receiver.partner_id.id:
		# 			partners.append(receiver.partner_id)
		# html = u"<span style='font-size:10pt; font-weight:bold; color:red;'>" + self.name +u' дугаартай ажил нээгдлээ!</span>'
		# self.env.user.send_chat(html, partners)

	def action_to_back(self):
		today = datetime.now() - timedelta(days=90)
		if self.date_required.strftime("%Y-%m-%d") < today.strftime("%Y-%m-%d"):
			raise UserError((u'3 сараас өмнөх WO буцаах боломжгүй!'))
		if self.state == 'closed':
			self.state = 'done'
		else:
			self.state = 'processing'

	def action_force_close(self):
		if not self.performance_description:
			raise UserError((u'Гүйцэтгэлтэй холбоотой мэдээллийг оруулна уу!'))
		self.state = 'done'

	def action_to_start(self):
		# Гүйцэтгэх ажилтныг шалгах
		# if self.contractor_type == 'internal':
		# 	if not self.employee_timesheet_lines:
		# 		raise UserError(_(u'Ажил гүйцэтгэх ажилтныг томилно уу!'))

		# Төлөвлөсөн цагийг шалгах
		if not self.planned_time_line:
			raise UserError((u'Төлөвлөсөн цагийг оруулна уу!'))

		# Хэрэв PM үйлчилгээ бол дагалдах
		# Үзлэгийн хуудсыг үүсгэх
		if self.maintenance_type == 'pm_service' and self.pm_priority:
			conf = self.env['maintenance.pm.material.config'].search([
				('priority','=',self.pm_priority),
				('technic_setting_id','=',self.technic_id.technic_setting_id.id)], limit=1)
			if conf and conf.inspection_setting_id:
					vals = {
						'branch_id': self.branch_id.id,
						'technic_id': self.technic_id.id,
						'date_inspection': self.date_required,
						'workorder_id': self.id,
						'shift': self.shift,
						'km_value': 0,
						'odometer_value': self.start_odometer,
						'inspection_type': 'pm',
					}
					inpection_id = self.env['technic.inspection'].create(vals)
					ctx = dict(self._context or {})
					ctx['inspection_id'] = conf.inspection_setting_id.id
					inpection_id.with_context(ctx).action_to_open()
					self.inspection_id = inpection_id.id

					# Хавсралт үүсгэх
					if conf.inspection_setting_id.attachment_id:
						values = {
							'name': u'PM-ийн checklist',
							'res_model':'maintenance.workorder',
							'res_id': self.id,
							'type':'binary',
							'datas': conf.inspection_setting_id.attachment_id,
						}
						attach_id = self.env['ir.attachment'].sudo().create(values)

		# Техникийн төлөв солих
		if self.technic_id:
			if self.technic_id.state not in ['draft','parking']:
				if self.is_depend_technic:
					self.technic_id.state = 'repairing'

		# Компонентийн төлөв солих
		if self.repair_component_id:
			self.repair_component_id.state = 'repairing'
		if self.install_component_id:
			self.install_component_id.state = 'repairing'

		for item in self.remove_component_ids:
			item.state = 'repairing'
		for item in self.install_component_ids:
			item.state = 'repairing'

		self.state = 'processing'
		self.date_start = datetime.now()
		if not self.validator_id:
			self.validator_id = self.env.user.id

		# # Chat илгээх
		# Сэлбэгтэй хол ЧАТ илгээх
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data']._xmlid_lookup('mw_technic_maintenance.action_maintenance_workorder')[2]
		if self.required_part_line:
			# LINK бэлдэх
			# res_model = self.env['ir.model.data'].search([
			# 		('module','=','mw_technic_maintenance'),
			# 		('name','in',['group_maintenance_master','group_maintenance_supervisor'])])
			# groups = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
			partners = []
			for receiver in self.flow_line_next_id.user_ids:
				if receiver.partner_id:
					if self.env.user.partner_id.id != receiver.partner_id.id:
						partners.append(receiver.partner_id)
			html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=maintenance.workorder&action=%s>%s</a></b>, дугаартай ажил эхэллээ. Сэлбэгийг батлана уу(START)"""% (base_url,self.id,action_id,self.name)
			# self.env.user.send_chat(html, partners)

	def action_to_waiting_part(self):
		self.state = 'waiting_part'

	def action_to_ready(self):
		# Дууссан байхад READY рүү ордоггүй болгох
		if self.state == 'closed':
			raise UserError((u'Хаагдсан WO ажлыг засах боломжгүй!\nЗасварынханд хандана уу!'))
		# MOVE шалгах
		not_done = self.wo_move_lines.filtered(lambda l: l.state not in ['done','cancel'])
		if not_done:
			raise UserError((u'Сэлбэгийн зарлагын баримт дуусаагүй байна!'))
		self.state = 'processing'
		if self.technic_id:
			if self.technic_id.state not in ['draft','parking']:
				if self.is_depend_technic:
					self.technic_id.state = 'repairing'

	# Зарлагадаж авсан сэлбэгийг хэрэглэсэн эсэхийг шалгах
	def check_used_part_lines(self):
		return
		# not_used = self.wo_move_lines.filtered(lambda l: l.is_used == False and l.state == 'done')
		# if not_used:
		# 	raise UserError(_(u'Зарлагадаж авсан сэлбэгийг хэрэглэсэн эсэхийг тэмдэглэнэ үү!'))
		# return

	def action_to_done(self):
		if self.required_part_line:
			not_ordered = self.required_part_line.filtered(lambda l: l.is_ordered == False and l.product_id.type == 'product')
			if not_ordered:
				raise UserError((u'Сэлбэгийн зарлагын баримт үүсээгүй байна!'))

		if self.required_part_line_2:
			if not self.po_request_ids:
				raise UserError((u'Худалдан авалтын баримт үүсээгүй байна!'))
			# elif self.po_request_id and self.po_request_id.state not in ['purchase','internal','cancel']:
			# 	raise UserError(_(u'Худалдан авалтын баримт дуусаагүй байна!'))

		not_done = self.wo_move_lines.filtered(lambda l: l.state not in ['done','cancel'])
		if not_done:
			raise UserError((u'Сэлбэгийн зарлагын баримт дуусаагүй байна!'))
		# Сэлбэгийг хэрэглэсэн эсэхийг шалгах
		self.check_used_part_lines()

		if self.maintenance_type == 'pm_service' and not self.pm_priority:
			raise UserError((u'PM ийн дугаарыг зөв оруулна уу!'))

		# Техникийн засвар бол
		if self.maintenance_type not in ['other_repair','daily_works','component_repair']:
			# Сүүлд хийгдсэн PM, гүйлт шалгах
			if self.maintenance_type == 'pm_service' and self.maintenance_type_id.is_pm:
				if self.technic_id:
					self.technic_id.last_pm_odometer = self.finish_odometer
					self.technic_id.last_pm_id = self.maintenance_type_id.id
					self.technic_id.last_pm_priority = self.pm_priority
					self.technic_id.last_pm_date = self.date_required

			# Техникийн төлөв солих
			if self.technic_id:
				if self.technic_id.state not in ['draft','parking']:
					if self.is_depend_technic:
						self._technic_to_work()

			# # Компонент салгаж байгаа бол
			# if self.remove_component_ids:
			# 	wos = self.env['maintenance.workorder'].search([
			# 		('state','in',['processing','waiting_part','ready']),
			# 		'|','|','|',('repair_component_id','=',self.repair_component_id.id),('remove_component_ids','in',[self.repair_component_id.id]),
			# 		('install_component_ids','in',[self.repair_component_id.id]),('install_component_id','=',self.repair_component_id.id)])
			# 	if not wos:
			# 		self.repair_component_id.state = 'new'
			# # Компонент засварлаж байгаа бол
			# if self.repair_component_id:
			# 	wos = self.env['maintenance.workorder'].search([
			# 		('state','in',['processing','waiting_part','ready']),
			# 		'|','|','|',('repair_component_id','=',self.repair_component_id.id),('remove_component_ids','in',[self.repair_component_id.id]),
			# 		('install_component_ids','in',[self.repair_component_id.id]),('install_component_id','=',self.repair_component_id.id)])
			# 	if not wos:
			# 		self.repair_component_id.state = 'inactive'
			# # Компонент угсраж байгаа бол
			# if self.install_component_id:
			# 	wos = self.env['maintenance.workorder'].search([
			# 		('state','in',['processing','waiting_part','ready']),
			# 		'|','|','|',('repair_component_id','=',self.repair_component_id.id),('remove_component_ids','in',[self.repair_component_id.id]),
			# 		('install_component_ids','in',[self.repair_component_id.id]),('install_component_id','=',self.repair_component_id.id)])
			# 	if not wos:
			# 		self.repair_component_id.state = 'using'
			# # Компонентууд угсарж байгаа бол
			# if self.install_component_ids:
			# 	wos = self.env['maintenance.workorder'].search([
			# 		('state','in',['processing','waiting_part','ready']),
			# 		'|','|','|',('repair_component_id','=',self.repair_component_id.id),('remove_component_ids','in',[self.repair_component_id.id]),
			# 		('install_component_ids','in',[self.repair_component_id.id]),('install_component_id','=',self.repair_component_id.id)])
			# 	if not wos:
			# 		self.repair_component_id.state = 'using'

			# Компонент эд анги угсрах, салгах
			if self.component_repair_type == 'remove':
				# Компонент салгаж авах бол
				if self.remove_component_ids:
					for rem in self.remove_component_ids:
						# Одоогийн мэдээлэл шинэчлэх

						rem.current_technic_id = False
						rem.state = 'inactive'
						rem.set_odometer = rem.total_odometer
						rem.date_of_set = False
						# Ашиглалтын түүх оруулах
						vals = {
							'parent_id': rem.id,
							'date': self.date_required,
							'technic_id': self.technic_id.id,
							'technic_odometer': self.technic_id.total_odometer,
							'component_odometer': rem.total_odometer,
							'description': 'Removed from '+self.technic_id.name+'. '+self.name +': '+self.description,
						}
						self.env['component.used.history'].sudo().create(vals)
				# Салгачаад дахиад өөр эд анги угсрах бол
				if self.install_component_ids:
					for ins in self.install_component_ids:
					# Одоогийн мэдээлэл шинэчлэх
						ins.current_technic_id = self.technic_id.id
						ins.state = 'using'
						ins.is_field_test = self.is_field_test
						ins.set_odometer = ins.total_odometer
						ins.date_of_set = self.date_required
						# Ашиглалтын түүх оруулах
						vals = {
							'parent_id': ins.id,
							'date': self.date_required,
							'technic_id': self.technic_id.id,
							'technic_odometer': self.technic_id.total_odometer,
							'component_odometer': ins.total_odometer,
							'description': 'Installed to '+self.technic_id.name+'. '+self.name +': '+self.description,
						}
						self.env['component.used.history'].sudo().create(vals)

			elif self.component_repair_type == 'install':
				print('starting#####################')
				# Компонент угсрах авах бол
				if self.install_component_id:
					for ins in self.install_component_id:
						# Одоогийн мэдээлэл шинэчлэх
						ins.current_technic_id = self.technic_id.id
						ins.state = 'using'
						ins.is_field_test = self.is_field_test
						ins.set_odometer = ins.total_odometer
						ins.date_of_set = self.date_required
						# Ашиглалтын түүх оруулах
						vals = {
							'parent_id': ins.id,
							'date': self.date_required,
							'technic_id': self.technic_id.id,
							'technic_odometer': self.technic_id.total_odometer,
							'component_odometer': ins.total_odometer,
							'description': 'Installed to '+self.technic_id.name+'. '+self.name +': '+self.description,
						}
						self.env['component.used.history'].sudo().create(vals)

		# Компонентийн засвар
		if self.repair_component_id and self.maintenance_type == 'component_repair':
			# Одоогийн мэдээлэл шинэчлэх
			component = self.repair_component_id
			component.state = 'inactive'
			component.last_odometer = component.total_odometer
			# Ашиглалтын түүх оруулах
			vals = {
				'parent_id': component.id,
				'date': self.date_required,
				'technic_id': self.technic_id.id,
				'technic_odometer': self.technic_id.total_odometer,
				'component_odometer': component.total_odometer,
				'description': u'Засварласан. '+self.name +': '+self.description,
			}
			self.env['component.used.history'].sudo().create(vals)
			# Их засвар бол мото цагийн түүхийг тэглэх
			# if self.component_maintenance_type in ['overhaul','exchange']:
			# Засвар хийсэн л бол тэглэх
			self.repair_component_id._new_start_odometer(self.repair_component_id.id)
			self.repair_component_id._set_auto_fields()
			self.repair_component_id.last_date = self.date_required
			self.repair_component_id.last_maintenance = self.component_maintenance_type
			# Засвар хийсэн LINE оруулах
			vals = {
				'parent_id': self.repair_component_id.id,
				'date': self.date_required,
				'technic_id': self.technic_id.id,
				'technic_odometer': self.technic_id.total_odometer,
				'increasing_odometer': 0,
				'depreciation_percent': 0,
				'user_id': self.env.user.id,
				'shift': self.shift,
				'is_wo_line': True,
			}
			self.env['component.depreciation.line'].sudo().create(vals)

		# Хэрэв төлөвлөгөө байгаа бол
		# Төлөвлөгөөг дуусгах
		if self.plan_id:
			self.plan_id.action_to_done()

		# Холбоотой дуудлага байвал дуугах
		# call = self.env['maintenance.call'].sudo().search([
		# 	('workorder_id','=',self.id),
		# 	('state','in',['open','to_wo','to_expense'])], limit=1)
		call = self.env['maintenance.call'].sudo().search([('workorder_id','=',self.id)], limit=1)
		if call:
			if call.filtered(lambda r: r.state in ['open','to_wo','to_expense','closed']):
				if not call.sudo().date_end:
					call.sudo().date_end = self.employee_timesheet_lines.sorted(key='date_end', reverse=True).mapped('date_end')[0] if self.employee_timesheet_lines else False
				call.sudo().performance_description = self.performance_description
				call.sudo().action_to_close()
			else:
				raise Warning(('Дуудлагын төлөв буруу байна. Дуудлага дээр төлөв болон мэдээллээ шалгана уу!'))

		self.state = 'done'
		self.date_done = datetime.now()

		# # Chat илгээх
		# res_model = self.env['ir.model.data'].search([
		# 		('module','=','mw_technic_maintenance'),
		# 		('name','in',['group_maintenance_planner','group_maintenance_clerk'])])
		# groups = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
		# partners = []
		# for group in groups:
		# 	for receiver in group.users:
		# 		if receiver.partner_id:
		# 			if self.env.user.partner_id.id != receiver.partner_id.id:
		# 				partners.append(receiver.partner_id)
		# html = u"<span style='font-size:10pt; font-weight:bold; color:red;'>" + self.name +u' дугаартай ажил дууслаа!</span>'
		# self.env.user.send_chat(html,partners)

	# Workorder дуусахад давхар ажил байна уу шалгах, байвал техникийн төлвийг солихгүй
	def _technic_to_work(self):
		wos = self.env['maintenance.workorder'].search([
			('technic_id','=',self.technic_id.id),('id','!=',self.id),
			('state','in',['processing','waiting_part','ready'])])
		if not wos:
			self.technic_id.state = 'working'

	# Ахлах мэргэжилтэн, Инженер, УУ хянасан эсэх ==========================
	def checked_by_superintendent(self):
		if self.state not in ['done','closed']:
			raise UserError((u'Та дууссаны дараа хянасан товчоо дарна уу!'))
		# Ахлах, Засварын менежер эсэхийг шалгах =====
		res_model = self.env['ir.model.data'].search([
				('module','=','mw_technic_maintenance'),
				('name','in',['group_maintenance_superintendent'])])
		groups = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
		for group in groups:
			if self.env.user.id in group.users.ids:
				self.senior_user_id = self.env.user.id
				self.date_senior = datetime.now()

		# Тохиргоон дээрээс USER шалгах ===================
		flow_lines = self.env['dynamic.flow.line'].search([
			('flow_id.model_id.model','=','maintenance.workorder'),
			('state_type','in',['engineer','chief'])])
		for fl in flow_lines:
			if fl.state_type == 'engineer':
				if self.env.user.id in fl.user_ids.ids:
					self.engineer_user_id = self.env.user.id
					self.date_engineer = datetime.now()
			if fl.state_type == 'chief':
				if self.env.user.id in fl.user_ids.ids:
					self.chief_user_id = self.env.user.id
					self.date_chief = datetime.now()
		self.is_checked = True
		self.is_checked_user = self.env.user.id

	# Шөнийн зардал хянаагүй бол
	# Ажлыг хаахгүй байх, заавал хянах ёстой болно
	# 11.28 нд ахлах мэргэжилтэн буюу Засварын менежер хянадаг болгосон
	def _check_night_expenses(self):
		if self.total_no_pm_amount > 5000000 and not self.engineer_user_id and not self.chief_user_id and not self.senior_user_id:
			raise UserError((u'Менежер, Инженер болон Удирдлагаар хянуулна уу!\nДараа нь хаана уу!'))
		return True

	def action_to_close(self):
		# Хянасан эсэхийг шалгах
		self._check_night_expenses()
		# Техникийн засвар бол
		if self.maintenance_type not in ['other_repair','daily_works','component_repair','other_repair2','other_repair3','other_repair4']:
			# Гүйлтийг шалгах
			if self.start_odometer <= 0 or self.finish_odometer <= 0 or self.start_odometer > self.finish_odometer:
				raise UserError((u'Техникийн эхлэх, дуусах гүйлтийг шалгана уу!'))
			if not self.is_checked :
				raise UserError((u'Хянасан уу!'))
			# Сүүлд хийгдсэн PM, гүйлт шалгах
			if self.maintenance_type == 'pm_service' and self.maintenance_type_id.is_pm:
				self.technic_id.last_pm_odometer = self.finish_odometer
				self.technic_id.last_pm_id = self.maintenance_type_id.id
				self.technic_id.last_pm_priority = self.pm_priority
				self.technic_id.last_pm_date = self.date_required

		# Засварчдын ажлын цагийг шалгах
		if not self.employee_timesheet_lines and self.contractor_type == 'internal':
			raise UserError((u'Засварчны цагийг оруулна уу! WO'))
		else:
			for line in self.employee_timesheet_lines:
				if not line.date_start or not line.date_end:
					raise UserError((u'Засварчны эхэлсэн, дууссан цагийг оруулна уу!'))

		# Засварын цагийг шалгах
		if not self.work_timesheet_lines:
			raise UserError((u'Засварын цагийг оруулна уу!'))

		# Үнэлгээ шалгах
		if not self.workorder_rate or self.workorder_rate == '0':
			raise UserError((u'Та засварын ажлыг үнэлнэ үү!'))
		# if not self.workorder_rate_description_id:
		# 	raise UserError(_(u'Үнэлгээний тайлбарыг сонгоно уу!'))

		self.state = 'closed'
		self.date_closed = datetime.now()
		self.close_user_id = self.env.user.id

	# Сэлбэг батлах урсгал - ==================================================
	# =========================================================================
	def _get_dynamic_flow_line_id(self):
		return self.flow_find().id

	def _get_dynamic_flow_next_line_id(self):
		return self.flow_find()._get_next_flow_line()

	def _get_default_flow_id(self):
		branch_id = self.branch_id or self.env.user.branch_id
		search_domain = []
		search_domain.append(('model_id.model','=','maintenance.workorder'))
		search_domain.append(('company_id','=',self.company_id.id))
		search_domain.extend(['|',('branch_ids','in',[branch_id.id]),('branch_ids','in',[])])
		print('search_domain', search_domain)
		return self.env['dynamic.flow'].sudo().search(search_domain, order='sequence', limit=1).id

	flow_id = fields.Many2one('dynamic.flow', string='Урсгалын тохиргоо', tracking=True,
		default=_get_default_flow_id, copy=False,
		domain="[('model_id.model', '=', 'maintenance.workorder')]")

	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
		default=_get_dynamic_flow_line_id, copy=False,
		domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'maintenance.workorder')]")
	flow_line_next_id = fields.Many2one('dynamic.flow.line', string='Request line next',
		default=_get_dynamic_flow_next_line_id, copy=False)

	history_flow_ids = fields.One2many('dynamic.flow.history','workorder_id', string='Histroy')

	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='State', store=True)
	state_type = fields.Char(string='State type', compute='_compute_state_type', store=True)

	@api.depends('flow_line_id.stage_id')
	def _compute_flow_line_id_stage_id(self):
		for item in self:
			item.stage_id = item.flow_line_id.stage_id

	@api.depends('flow_line_id')
	def _compute_state_type(self):
		for item in self:
			item.state_type = item.flow_line_id.state_type

	def flow_find(self, domain=[], order='sequence'):
		search_domain = []
		if self.flow_id:
			search_domain.append(('flow_id','=',self.flow_id.id))
		else:
			# search_domain.append(('model_id.model','=','maintenance.workorder'))
			# search_domain.append(('company_id','=',self.env.user.company_id.id))
			# flow_id = self.env['dynamic.flow'].sudo().search(search_domain, order='sequence', limit=1).id
			# search_domain.append(('flow_id.model_id.model','=','maintenance.workorder'))
			search_domain.append(('flow_id.model_id.model','=','maintenance.workorder'))
			order = 'flow_id, sequence'
		search_domain.append(('flow_id.company_id','=',self.company_id.id or self.env.user.company_id.id))
		search_domain.extend(['|',('flow_id.branch_ids','in',[self.branch_id.id]),('flow_id.branch_ids','in',[])])
		print('search_domain', search_domain)
		return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1)

	@api.onchange('company_id','branch_id')
	def _onchange_company_id(self):
		flow_id = self.env['dynamic.flow'].search([('model_id.model','=','maintenance.workorder'),('company_id','=',self.company_id.id)], limit=1)
		self.write({'flow_id': flow_id.id})
		self.write({'flow_line_id': self.flow_find().id})
		self.write({'flow_line_next_id': self.flow_find()._get_next_flow_line()})
		# self.required_part_line._compute_account()
		# call_id = self.env['maintenance.call'].search([('name','=', self.origin)])
		# call_id.write({'branch_id': wo.branch_id.id for wo in self})

	@api.onchange('flow_id','company_id','branch_id')
	def _onchange_flow_id(self):
		if not self.flow_id:
			self.write({'flow_line_id': False}) 
			self.write({'flow_line_next_id': False})
			print('itd Falseeeeeeeeeeee')
		self.write({'flow_id': self._get_default_flow_id()})
		if self.flow_id:
			self.write({'flow_line_id': self.flow_find().id}) 
			self.write({'flow_line_next_id': self.flow_find()._get_next_flow_line()}) 
			_logger.info(self.flow_id, self.flow_line_id, self.flow_line_next_id, self.flow_find())
			print('on the workkkkkkkkkk')
		else:
			search_domain = []
			search_domain.append(('model_id.model','=','maintenance.workorder'))
			search_domain.append(('company_id','=',self.company_id.id))
			self.write({'flow_id': self.env['dynamic.flow'].sudo().search(search_domain, order='sequence', limit=1).id})
			self.write({'flow_line_id': self.flow_find().id}) 
			self.write({'flow_line_next_id': self.flow_find()._get_next_flow_line()})
			print('workinggggggggggggg')

	# Validators and Dates
	parts_user_id = fields.Many2one('res.users', u'Мастер', readonly=True, copy=False,)
	date_parts = fields.Datetime(u'Мастерын огноо', readonly=True, copy=False,)

	senior_user_id = fields.Many2one('res.users', u'Senior name', readonly=True, copy=False,)
	date_senior = fields.Datetime(u'Senior date', readonly=True, copy=False,)

	engineer_user_id = fields.Many2one('res.users', u'Engineer name', readonly=True, copy=False,)
	date_engineer = fields.Datetime(u'Engineer date', readonly=True, copy=False,)

	chief_user_id = fields.Many2one('res.users', u'Chief name', readonly=True, copy=False,)
	date_chief = fields.Datetime(u'Chief date', readonly=True, copy=False,)

	# Өгөгдсөн огнооноос Ээлжийг олж авах
	def _get_shift_by_datetime(self, now):
		# print '===dates===', now.strftime("%Y-%m-%d 06:30"), now.strftime("%Y-%m-%d %H:%M"), now.strftime("%Y-%m-%d 18:30")
		if now.strftime("%Y-%m-%d 06:00") < now.strftime("%Y-%m-%d %H:%M") and now.strftime("%Y-%m-%d %H:%M") < now.strftime("%Y-%m-%d 18:30"):
			return 'day'
		else:
			return 'night'

	# Warranty chat ilgeeh
	# @api.onchange('state')
	# def onchange_warranty(self):
	# 	print('onchange----')
	# 	for item in self:
	# 		if item.state == 'ordered_part':
	# 			self.send_warranty_notf()

	def send_warranty_notf(self):
		# LINK бэлдэх
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data']._xmlid_lookup('mw_technic_maintenance.action_maintenance_workorder')[2]
		if self.flow_line_id.state_type == 'draft' and self.is_warrenty == True:
			res_model = self.env['ir.model.data'].search([
					('module','=','mw_technic_maintenance'),
					('name','in',['group_maintenance_warranty_email_user'])])
			groups = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
			print('SEND BATS', groups)
			partners = []
			for group in groups:
				print('SEND to THESE HEREOS', group.users)
				for receiver in group.users:
					if receiver.partner_id:
						if self.env.user.partner_id.id != receiver.partner_id.id:
							partners.append(receiver.partner_id)
							# MSG илгээх
			html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=maintenance.workorder&action=%s>%s</a></b>, дугаартай <b>Warranty</b> ажил эхэллээ."""% (base_url,self.id,action_id,self.name)
			# self.env.user.send_chat(html,partners,True,'Warranty WO эхэллээ')
			self.env.user.send_emails(partners=partners, subject='Warranty WO эхэллээ', body=html, attachment_ids=False)

	# Click BUTTON -------------
	def action_next_stage(self):
		if self.state not in ['ordered_part','processing','waiting_part']:
			return
		if not self.warehouse_id:
			wh_ids = self.required_part_line.filtered(lambda l: not l.is_ordered).mapped('src_warehouse_id')
			if not wh_ids:
				raise UserError((u'Сэлбэгийн зарлага хийх агуулахыг сонгоно уу!!'))
		if not self.required_part_line:
			raise UserError((u'Сэлбэг, материалын мэдээллийг оруулна уу!'))
		# Хэрэв захиалах сэлбэг байхгүй бол үйлдэл хийхгүй
		if not self.required_part_line.filtered(lambda l: not l.is_ordered):
			return

		# Хийх гэж байгаа зарлагын нийт дүнг олох
		# PM материалын дүнг тооцохгүй
		confirm_amount = 0
		# Warrenty биш бол дүн тооцно
		# Warrenty бол дүнг тооцохгүй цааш явна. Дүнг 0 гэж үзнэ
		if not self.is_warrenty:
			for ll in self.required_part_line:
				if not ll.is_ordered and not ll.is_pm_material:
					confirm_amount += ll.product_id.standard_price * ll.qty
		# Урсгал шалгах
		day_night = 'all_shift'
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		print('======', next_flow_line_id.name)
		_logger.info(u'-***********-Part confirm--************* %d %s %d %s \n' % (confirm_amount, day_night, next_flow_line_id.id, next_flow_line_id.state_type))
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data']._xmlid_lookup('mw_technic_maintenance.action_maintenance_workorder')[2]
		if next_flow_line_id and next_flow_line_id._get_check_ok_flow(False, False, self.env.user):
			# Мастер руу мэдэгдэх
			if next_flow_line_id.state_type == 'sent':
				self.flow_line_id = next_flow_line_id
				self.flow_line_next_id = next_flow_line_id._get_next_flow_line()
				self.chief_user_id = self.env.user.id
				self.date_chief = datetime.now()
				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'workorder_id', self)
				# Дараагийн шатны хүн рүү МСЖ илгээх
				# if self.flow_line_next_id:
				# 	send_users = self.flow_line_next_id._get_flow_users()
				# 	if send_users:
				# 		html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=maintenance.workorder&action=%s>%s</a></b>, дугаартай ажлыг батлана уу(send)"""% (base_url,self.id,action_id,self.name)
				# 		if next_flow_line_id.is_mail:
				# 			self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлана уу')
				# 		else:
				# 			self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлана уу')
				# 		self.flow_line_id.send_chat(html, send_users.mapped('partner_id'))
				return
			elif next_flow_line_id.state_type == 'parts_user':
				self.flow_line_id = next_flow_line_id
				self.flow_line_next_id = next_flow_line_id._get_next_flow_line()
				self.chief_user_id = self.env.user.id
				self.date_chief = datetime.now()
				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'workorder_id', self)
				# Дараагийн шатны хүн рүү МСЖ илгээх
				# if self.flow_line_next_id:
				# 	send_users = self.flow_line_next_id._get_flow_users()
				# 	if send_users:
				# 		html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=maintenance.workorder&action=%s>%s</a></b>, дугаартай ажлыг батлана уу(Сэлбэгийн ажилтан)"""% (base_url,self.id,action_id,self.name)
				# 		if next_flow_line_id.is_mail:
				# 			self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлана уу')
				# 		else:
				# 			self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлана уу')
				# 		self.flow_line_id.send_chat(html, send_users.mapped('partner_id'))
				return
			# Мастер батлах бол
			elif next_flow_line_id.state_type == 'master':
				# Дүн шалгах
				if confirm_amount <= next_flow_line_id.amount_price_max:
					self.create_expense_for_parts()
					send_users = self.create_uid
					if send_users:
						html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=maintenance.workorder&action=%s>%s</a></b>, дугаартай ажлын сэлбэг батлагдаж дууслаа"""% (base_url,self.id,action_id,self.name)
						# self.flow_line_id.send_chat(html, send_users.mapped('partner_id'))
						if next_flow_line_id.is_mail:
							# self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлагдаж дууслаа')
							self.env.user.send_emails(partners=send_users.mapped('partner_id'), subject='WO Батлагдаж дууслаа', body=html, attachment_ids=False)
						else:
							# self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлагдаж дууслаа')
							self.env.user.send_emails(partners=send_users.mapped('partner_id'), subject='WO Батлагдаж дууслаа', body=html, attachment_ids=False)
					# Шинээр урсгал эхлүүлэх
					self.total_no_pm_amount = confirm_amount
					self.flow_line_id = self.flow_find().id
					self.flow_line_next_id = self.flow_find()._get_next_flow_line()
					return
				else:
					# Limit ээс их бол батлах дүнг SET хийнэ
					self.total_no_pm_amount = confirm_amount
					self.flow_line_id = next_flow_line_id
					self.flow_line_next_id = next_flow_line_id._get_next_flow_line()
					# Холбогдох хүмүүсрүү МСЖ илгээх
					send_users = self.flow_line_next_id._get_flow_users()
					if send_users:
						html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=maintenance.workorder&action=%s>%s</a></b>, дугаартай ажлын сэлбэгийг батлана уу"""% (base_url,self.id,action_id,self.name)
						# self.flow_line_id.send_chat(html, send_users.mapped('partner_id'))
						if next_flow_line_id.is_mail:
							self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлана уу')
						else:
							self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлана уу')
					self.parts_user_id = self.env.user.id
					self.date_parts = datetime.now()
					self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'workorder_id', self)
					return
			# Уурхайн удирдлага хянах, батлах
			elif next_flow_line_id.state_type == 'chief':
				self.flow_line_id = next_flow_line_id
				self.flow_line_next_id = next_flow_line_id._get_next_flow_line()
				self.chief_user_id = self.env.user.id
				self.date_chief = datetime.now()
				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'workorder_id', self)
				# Дараагийн шатны хүн рүү МСЖ илгээх
				# send_users = self.flow_line_next_id._get_flow_users()
				# if send_users:
				# 	html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=maintenance.workorder&action=%s>%s</a></b>, дугаартай ажлыг батлана уу(удирдлага хянасан)"""% (base_url,self.id,action_id,self.name)
				# 	# self.flow_line_id.send_chat(html, send_users.mapped('partner_id'))
				# 	if next_flow_line_id.is_mail:
				# 		self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлана уу')
				# 	else:
				# 		self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлана уу')
				return
			# Засварын ахлах, менежер батлах
			elif next_flow_line_id.state_type == 'senior':
				self.senior_user_id = self.env.user.id
				self.date_senior = datetime.now()
				self.create_expense_for_parts()
				send_users = self.create_uid
				if send_users:
					html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=maintenance.workorder&action=%s>%s</a></b>, дугаартай ажлын сэлбэг батлагдаж дууслаа"""% (base_url,self.id,action_id,self.name)
					# self.flow_line_id.send_chat(html, send_users.mapped('partner_id'))
					if next_flow_line_id.is_mail:
						# self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлагдаж дууслаа')
						self.env.user.send_emails(partners=send_users.mapped('partner_id'), subject='WO Батлагдаж дууслаа', body=html, attachment_ids=False)
					else:
						# self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлагдаж дууслаа')
						self.env.user.send_emails(partners=send_users.mapped('partner_id'), subject='WO Батлагдаж дууслаа', body=html, attachment_ids=False)
				# Шинээр урсгал эхлүүлэх
				self.flow_line_id = self.flow_find().id
				self.flow_line_next_id = self.flow_find()._get_next_flow_line()
				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'workorder_id', self)
				# Дараагийн шатны хүн рүү МСЖ илгээх
				# partners = []
				# _logger.info(next_flow_line_id)
				# _logger.info(next_flow_line_id._get_next_flow_line())
				# _logger.info(next_flow_line_id._get_next_flow_line()._get_flow_users(False,False,False))
				# if next_flow_line_id._get_next_flow_line():
				# 	for receiver in next_flow_line_id._get_next_flow_line()._get_flow_users(False,False,False):
				# 		if receiver.partner_id:
				# 			if self.env.user.partner_id.id != receiver.partner_id.id:
				# 				partners.append(receiver.partner_id)
				# html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=maintenance.workorder&action=%s>%s</a></b>, дугаартай ажил дээр (%d)төг-ийн сэлбэг тавигдлаа"""% (base_url,self.id,action_id,self.name, self.total_no_pm_amount)
				# # self.env.user.send_chat(html,partners)
				# if next_flow_line_id.is_mail:
				# 	self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлана уу')
				# else:
				# 	self.env.user.send_chat(html, send_users.mapped('partner_id'), True, 'WO Батлана уу')
				return
		else:
			raise UserError('Та батлах хэрэглэгч биш байна. %s' % (next_flow_line_id.stage_id.name))

	# Сэлбэгийн урсгалыг цуцлах
	def cancel_flow(self):
		self.flow_line_id = self.flow_find().id
		self.flow_line_next_id = self.flow_find()._get_next_flow_line()
		self.state_type = 'draft'
		self.env['dynamic.flow.history'].create_history(self.flow_line_id, 'workorder_id', self)
	# =========================================================================
	# Үлдэгдэл шалгах
	def check_product_qty(self):
		for line in self.required_part_line:
			quant_obj = self.env['stock.quant']
			domain = [('product_id','=',line.product_id.id),('location_id.usage','=','internal')]
			# Агуулах сонгосон бол агуулахаас хайх
			if self.warehouse_id:
				domain.append(('location_id.set_warehouse_id','=',self.warehouse_id.id))
			quant_ids = quant_obj.sudo().search(domain)
			qty = 0
			qty = sum(quant_ids.mapped('quantity'))
			line.qty_available = qty
			# Хөрвөсөн кодтой барааны үлдэгдэл
			domains = [('product_id','!=',line.product_id.id),
						 ('product_id.product_tmpl_id','=', line.product_id.product_tmpl_id.id),
						 ('location_id.usage','=', 'internal')]
			if line.parent_id.warehouse_id:
				domains.append(('location_id.set_warehouse_id','=', line.parent_id.warehouse_id.id))

			quant_template_ids = quant_obj.sudo().search(domains)
			qty = 0
			qty = sum(quant_template_ids.mapped('quantity'))
			line.qty_convert_available = qty

			# Хамгийн сүүлд зарлага хийсэн огноо
			if self.technic_id:
				move = self.env['stock.move'].search([
					('technic_id','=',self.technic_id.id),
					('state','=','done'),
					('picking_id.picking_type_id.code','=','outgoing'),
					('product_id','=',line.product_id.id)], limit=1, order='date desc')
				if move:
					line.last_expense_date = move.date
				else:
					line.last_expense_date = u'Өмнө нь гараагүй'

	# Сэлбэг зарлага үүсгэх - Шинэ
	# Олон Picking тэй үүсгэх
	# PM ийн материалыг заасан агуулахаас үүсгэх
	def get_part_line(self):
		return self.required_part_line.filtered(lambda r: r.product_id.type!='service')
	
	def create_expense_for_parts(self):
		req_part_line = self.get_part_line()
		if req_part_line:
			# Гарах байрлалыг олох
			dest_loc = self.env['stock.location'].sudo().search(
							[('usage','=','customer')], limit=1)
			if not dest_loc:
				raise UserError((u'Зарлагадах байрлал олдсонгүй!'))

			pickings = {}
			for line in req_part_line:
				if not line.is_ordered:
					# Агуулах олох
					temp_warehouse = line.src_warehouse_id if line.src_warehouse_id else self.warehouse_id
					if not temp_warehouse:
						raise UserError((u'Сэлбэгийн зарлага хийх агуулахыг сонгоно уу!'))

					# Picking шалгах
					t_name = ''
					if temp_warehouse.id not in pickings:
						if self.technic_id:
							t_name = self.technic_id.name
						picking = self.env['stock.picking'].create(
							{'picking_type_id': temp_warehouse.out_type_id.id,
							 'state': 'draft',
							 'move_type': 'one',
							 'partner_id': False,
# 							 'min_date': datetime.now(),
							 'location_id': temp_warehouse.lot_stock_id.id,
							 'location_dest_id': dest_loc.id,
							 'origin': self.name +', '+t_name+': '+self.description,
							 'maintenance_workorder_id': self.id,
							})
						pickings[ temp_warehouse.id ] = picking
					product = line.product_id
					# TTJV-ийн warrenty-г болиулсан
					# if line.is_warrenty:
					# 	warrenty_product = self.env['product.product'].search([
					# 		('default_code','=',line.product_id.default_code+'WAR')], limit=1)
					# 	if warrenty_product:
					# 		product = warrenty_product
					# 	else:
					# 		raise UserError(_(u'Warrenty бараа олдсонгүй!'))
					# MOVE үүсгэх
					sp_id = pickings[temp_warehouse.id]
					vals = {
						'name': self.technic_id.name or '-',
						'origin': self.name,
						'picking_id': sp_id.id,
						'product_id': product.id,
						'product_uom': product.uom_id.id,
						'product_uom_qty': line.qty,
						'location_id': temp_warehouse.lot_stock_id.id,
						'location_dest_id': dest_loc.id,
						'state': 'draft',
					}
					line_id = self.env['stock.move'].create(vals)
					line.is_ordered = True
					line.move_id = line_id.id

			# Picking batlax
			con = dict(self._context)
			con['from_code'] = True
			# print(aaa)
			for key in pickings:
				sp_id = pickings[key]
				print('con)_0-0-00-0---0-0-0-00-0-0-00--00-0-0-0-0-',con)
				sp_id.with_context(con).action_confirm()
			self.state = 'waiting_part'
			self.parts_user_id = self.env.user.id
			self.date_parts = datetime.now()
			self.warehouse_id = False
		else:
			raise UserError((u'Сэлбэг, материалын мэдээллийг оруулна уу!'))

	def view_prs(self):
		self.ensure_one()
		action = self.env.ref('mw_purchase_request.action_purchase_request_view').read()[0]
		prs = self.mapped('po_request_ids')
		action['domain'] = [('id', 'in', self.po_request_ids.ids)]
		action['context'] = dict(self._context, default_purchase_return_id=self.id, create=False)
		return action

	def set_pr_ids(self):
		wos = self.env['maintenance.workorder'].sudo().search([('id','!=',False)])
		print('####',len(wos))
		for wo in wos:
			wo.po_request_ids = [(4,wo.po_request_id.id)]

	# Сэлбэг Худалдан авалтын хүсэлт үүсгэх
	def create_po_request_for_parts(self):
		if self.required_part_line_2.filtered(lambda l: not l.is_ordered):
			req_id = False
			emp = self.env['hr.employee'].search([('user_id','=',self.env.user.id)], limit=1)
			desc = self.name +', : '+self.description+'\n'+self.po_description
			if self.technic_id:
				self.name +', '+ self.technic_id.name +': '+self.description+'\n'+self.po_description
			# Bayasaa nemev
			search_domain = [('model_id.model','=','purchase.request'),('branch_ids','in',[self.branch_id.id])]
			flow_id = self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1)
			flow_line_id = self.env['dynamic.flow.line'].search([('flow_id','=',flow_id.id)], order='sequence', limit=1)
			req_id = self.env['purchase.request'].create(
				{'employee_id': emp.id if emp else False,
				 'desc': desc,
				 'flow_id': flow_id.id,
				 'flow_line_id': flow_line_id.id,
				 'maintenance_workorder_id': self.id,
				 'branch_id': self.branch_id.id,
				})
			ordered_products = []
			if req_id:
				self.po_request_ids = [(4,req_id.id)]
				for line in self.required_part_line_2.filtered(lambda l: not l.is_ordered):
					vals = {
						'request_id': req_id.id,
						'product_id': line.product_id.id,
						'technic_id': self.technic_id.id,
						'uom_id': line.uom_id.id,
						'qty': line.qty,
						'price_unit': line.price_unit,
					}
					line_id = self.env['purchase.request.line'].create(vals)
					line.is_ordered = True
					ordered_products.append(line.product_id.name)

				self.state = 'ordered_part'
				self.send_warranty_notf()
				self.message_post(body=u"%s, Захиалсан сэлбэг: %s" %(req_id.name, ','.join(ordered_products)))
		else:
			raise UserError((u'Сэлбэг, материалын мэдээллийг оруулна уу!'))

	# Сэлбэг хүлээнгээ ажиллаж байгаа
	def working_ordered_part(self):
		if self.technic_id:
			self.technic_id.action_to_working()
		self.state = 'ordered_part'
		self.send_warranty_notf()

	def stopping_ordered_part(self):
		if self.technic_id:
			self.technic_id.action_to_stop()
		self.state = 'ordered_part'
		self.send_warranty_notf()

	# Ажилтан хүлээж зогсох
	def stopping_waiting_labour(self):
		self.state = 'waiting_labour'

	# Get timesheet
	# Засварын шалтгаан
	def get_delay_reasons(self, ids):
		obj = self.env['maintenance.workorder'].search([('id','=',ids)])
		headers = [u'№',u'Код',u'Шалтгааны нэр',u'Эхэлсэн цаг',u'Дууссан цаг',u'Зарцуулсан цаг']
		datas = []
		i = 1
		if obj.work_timesheet_lines:
			for line in obj.work_timesheet_lines:
				st = line.date_start + timedelta(hours=self._get_tz()) if line.date_start else '_'
				et = line.date_end + timedelta(hours=self._get_tz()) if line.date_end else '_'
				spend_time = str(round(line.spend_time,2))
				temp = [str(i),line.delay_reason_id.code,line.delay_reason_id.name,st,et,spend_time]
				datas.append(temp)
				i += 1
		else:
			for line in self.env['maintenance.delay.reason'].search([], order='name'):
				temp = [str(i),line.code,line.name,'','','']
				datas.append(temp)
				i += 1
		res = {'header': headers, 'data':datas}
		# Тоолуур
		obj.print_count = obj.print_count+1
		_logger.info(u'-***********-WO--*************---get_delay_reasons--%s---\n'%(res))
		return res

	def get_company_logo(self, ids):
		report_id = self.browse(ids)
		if report_id:
			if report_id.company_id and not report_id.company_id.logo_web:
				raise UserError((u'Компаний мэдээлэл дээр логогоо сонгоно уу!'))
			image_buf = report_id.company_id.logo_web.decode('utf-8')
		image_str = '';
		if len(image_buf)>10:
			image_str = '<img alt="Embedded Image" width="200" src="data:image/png;base64,%s" />'%(image_buf)
		return image_str

	# Засварчдын мэдээлэл
	def get_employee_lines(self, ids):
		headers = [u'№',u'Код',u'Ажилтны нэр', u'Эхэлсэн цаг',u'Дууссан цаг',u'Зарцуулсан цаг']
		datas = []
		obj = self.env['maintenance.workorder'].search([('id','=',ids)])
		i = 1
		if obj.employee_timesheet_lines:
			for line in obj.employee_timesheet_lines:
				st = line.date_start + timedelta(hours=self._get_tz()) if line.date_start else ''
				et = line.date_end + timedelta(hours=self._get_tz()) if line.date_end else ''
				spend_time = str(round(line.spend_time or 0,2))
				temp = [str(i),str(line.employee_id.identification_id or ''), (line.employee_id.name or '')+'\n',st,et,str(spend_time)]
				datas.append(temp)
				i += 1
		else:
			temp = ['| \n','| \n','| \n','| \n','| \n','| \n']
			datas.append(temp)
			datas.append(temp)
			datas.append(temp)
			datas.append(temp)
			if obj.maintenance_type == 'pm_service':
				datas.append(temp)
				datas.append(temp)

		res = {'header': headers, 'data':datas}
		_logger.info(u'-***********-WO--*************---get_employee_lines--%s---\n'%(res))
		return res

	def _get_tz(self):
		now = datetime.now(pytz.timezone(self.env.context.get('tz')))
		tz = now.utcoffset().total_seconds()/60/60
		return tz

	# Хэрэглэсэн сэлбэг материал
	def get_used_parts(self, ids):
		headers = [u'Num',u'Parts name',u'Parts number',u'Qty',u'☑☒']
		datas = []
		obj = self.env['maintenance.workorder'].search([('id','=',ids)])
		i = 1
		if obj.wo_move_lines:
			for line in obj.wo_move_lines:
				_logger.info(u'-***********-WO--*************---get_used_parts--%s %s %f ---\n'%(line.product_id.name, line.product_id.default_code,line.product_uom_qty))
				temp = [str(i), (line.product_id.name), (line.product_id.default_code),str(line.product_uom_qty),'']
				datas.append(temp)
				i += 1
		else:
			temp = ['| \n','| \n','| \n','| \n','| \n']
			datas.append(temp)
			datas.append(temp)
			datas.append(temp)
			datas.append(temp)
			datas.append(temp)
		res = {'header': headers, 'data':datas}
		_logger.info(u'-***********-WO--*************---get_used_parts--%s---\n'%(res))
		return res

	# Захиалсан сэлбэг материал
	def get_ordered_parts(self, ids):
		headers = [u'Дд',u'Parts name',u'Parts number',u'Qty']
		datas = []
		obj = self.env['maintenance.workorder'].search([('id','=',ids)])
		i = 1
		if obj.required_part_line_2:
			for line in obj.required_part_line_2:
				temp = [str(i),str(line.product_id.name), line.product_id.default_code,str(line.qty)]
				datas.append(temp)
				i += 1
		else:
			temp = ['| \n','| \n','| \n','| \n']
			datas.append(temp)
			datas.append(temp)
			datas.append(temp)
			datas.append(temp)
			datas.append(temp)

		res = {'header': headers, 'data':datas}
		_logger.info(u'-***********-WO--*************---get_ordered_parts--%s---\n'%(res))
		return res

	def action_to_print(self):
		if self.state not in ['draft','']:
			model_id = self.env['ir.model'].search([('model','=','maintenance.workorder')], limit=1)
			template = self.env['pdf.template.generator'].search([
				('model_id','=',model_id.id),
				('name','=','timesheet')], limit=1)
			if template:
				res = template.print_template(self.id)
				return res
			else:
				raise UserError((u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

	# Timesheet дата бэлдэх
	def get_timesheet_datas(self, wo_id, context=None):
		datas = {}
		obj = self.env['maintenance.workorder'].browse(wo_id)
		categ_names = []
		color_names = []
		series = []
		idx = 1
		for line in obj.work_timesheet_lines:
			categ_names.append(str(idx)+'. '+line.delay_reason_id.name)
			color_names.append(line.delay_reason_id.color)
			if line.date_start and line.date_end:
				temp = {
					'low': self._unix_time_millis(line.date_start),
					'high': self._unix_time_millis(line.date_end),
					'info': round(line.spend_time,2)}
				series.append(temp)
			idx += 1

		datas['timesheet_categories'] = categ_names
		datas['timesheet_colors'] = color_names
		datas['timesheet_data'] = series
		return datas

	def _unix_time_millis(self, dt):
		epoch = datetime.utcfromtimestamp(0)
		date_start = dt
		date_start += timedelta(hours=8)
		return (date_start - epoch).total_seconds() * 1000.0

	# Туршлагын санд оруулах
	def create_experience_info(self):
		if self.state not in ['done','closed']:
			raise UserError((u'Засварын ажил дууссаны дараа санд оруулна уу!'))
		vals = {
			'damaged_type_id': self.damaged_type_id.id,
			'damaged_reason_id': self.damaged_reason_id.id,
			'description': self.description,
			'performance_description': self.performance_description,
			'workorder_id': self.id,
			# 'warehouse_id': self.user_warehouse_id.id,
		}
		experience_id = self.env['maintenance.experience.library'].create(vals)
		self.is_experience_info = True

	# Холбоотой ажил үүсгэх, хойшид хийгдэх ажил
	def create_ref_workorder(self):
		if self.ref_workorder_id:
			raise UserError((u'Already Workorder created!'))

		# if self.next_work_description:
		# Сүүлд өөрчилсөн
		# WO үүсгэх
		vals = {
			'branch_id': self.branch_id.id,
			'date_required': datetime.now(),
			'maintenance_type': self.maintenance_type,
			'maintenance_type_id': self.maintenance_type_id.id,
			'pm_priority': self.pm_priority,
			'origin': self.name,
			'technic_id': self.technic_id.id,
			'description': self.next_work_description or '...',
			'damaged_reason_id': self.damaged_reason_id.id,
			'damaged_type_id': self.damaged_type_id.id,
			'start_odometer': 0,
			'planned_time': 0,
			'contractor_type': self.contractor_type,
			'origin': self.name,
			'shift': self.shift,
		}
		wo_id = self.env['maintenance.workorder'].create(vals)
		self.ref_workorder_id = wo_id.id
		self.next_work_state = 'wo_created'

	@api.depends('required_part_line','required_part_line.product_id','required_part_line.qty')
	def _compute_wc_messages(self):
		for item in self:
			message = []
			product_ids = item.required_part_line.mapped('product_id').ids
			if item.id and product_ids and item.branch_id and item.technic_id:
				if len(product_ids)>1:
					p_ids = str(tuple(product_ids))
				elif len(product_ids)==1:
					p_ids = "("+str(product_ids[0])+")"
				sql_query = """SELECT rpl.product_id,wo.date_required as date,wo.validator_id,sum(rpl.qty) as qty,wo.name, wo.technic_id
						FROM stock_move sm
						left join required_part_line rpl on (rpl.move_id=sm.id)
						left join maintenance_workorder wo on (wo.id=rpl.parent_id)
						left join product_product pp on (rpl.product_id=pp.id)
						left join product_template pt on (pt.id=pp.product_tmpl_id)
						WHERE rpl.product_id in %s and wo.id!=%s and wo.state not in ('closed','cancelled') and wo.branch_id=%s
						and wo.company_id=%s and wo.date_required<='%s' and pt.type!='service' and wo.technic_id=%s
						group by 1,2,3,5,6
				"""% (p_ids,item.id, item.branch_id.id, item.company_id.id, item.date, item.technic_id.id)
				self.env.cr.execute(sql_query)
				query_result = self.env.cr.dictfetchall()
				for qr in query_result:
					val = u"""<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"""%(self.env['product.product'].browse(qr['product_id']).display_name,qr['date'],self.env['res.users'].browse(qr['validator_id']).name,qr['qty'],qr['name'], self.env['technic.equipment'].browse(qr['technic_id']).name)
					message.append(val)
					print(val)

			if message==[]:
				message = False
			else:
				message = u'<table style="width: 100%;"><tr><td colspan="4" style="text-align: center;">ЭНЭ СЭЛБЭГ ЭНЭ ТЕХНИК ДЭЭР АШИГЛАГДСАН БАЙНА!</td></tr><tr style="width: 40%;"><td>Бараа</td><td style="width: 15%;">Огноо</td><td style="width: 20%;">Ажилтан</td><td style="width: 10%;">Тоо Хэмжээ</td><td style="width: 15%;">Дугаар</td></tr>'+u''.join(message)+u'</table>'
			item.warning_messages = message

	# def create_quot(self):
	# 	obj =  self.env['quotation.order']
	# 	obj_line =  self.env['quotation.order.line']
	# 	# if self.job_id:
	# 	#     raise UserError('WO үүссэн байна %s'%(self.display_name))
	# 	# for obj in self:
	# 	quot_id = obj.create({
	# 		'partner_id': self.partner_id.id,
	# 		'currency_id': self.currency_id.id or self.company_id.currency_id.id,
	# 		'technic_id': self.technic_id.id,
	# 		'comment': self.description or self.display_name,
	# 		'date_order': self.date_order or datetime.now(),
	# 		'job_id': self.id,
	# 		'job_type_id': self.job_type_id.id,
	# 		'assigned_department_id': self.assigned_department_id.id,
	# 		'order_type_id': self.order_type_id.id,
	# 		'work_center_settings_id' : self.work_center_id.id,
	# 	})
	# 	# self.write({'job_id': workorder_id.id})
	# 	for order in self.order_line:
	# 		part_line_id = obj_line.create({
	# 			'name': order.name or order.product_id.display_name,
	# 			'product_id': order.product_id.id,
	# 			'price_unit': order.price_unit,
	# 			'order_id': quot_id.id,
	# 			'discount': order.discount,
	# 			'product_uom_qty': order.product_uom_qty,
	# 			'tax_id': [(6, 0, order.tax_id.ids)],
	# 		})
	# 	return quot_id

	def view_invoice(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_out_invoice_type').read()[0]
		action['domain'] = [('id','in',self.invoice_ids.ids)]
		return action

	@api.depends('invoice_ids')
	def _compute_invoice_count(self):
		for item in self:
			item.invoice_count = len(item.invoice_ids)

	def create_add_timesheet(self):
		self.required_part_line.filtered(lambda r: r.timesheet_id)
		# sheets = self.employee_timesheet_lines.filtered(lambda r: not r.order_lines)
		for item in self:
			query = "select sum(guitsetgel_time), product_id from maintenance_employee_timesheet_line where product_id is not null and parent_id = {0} group by product_id".format(item.id)
			self.env.cr.execute(query)
			result = self.env.cr.dictfetchall()
			print(result)
			for row in result:
				product_id = self.env['product.product'].sudo().search([('id', '=', row['product_id'])], limit=1)
				timesheet_ids = self.env['maintenance.employee.timesheet.line'].sudo().search([('parent_id','=', item.id),('product_id','=',product_id.id)])
				vals = {}
				vals['product_id'] = row['product_id']
				vals['qty'] = row['sum']
				vals['parent_id'] = item.id
				# print(timesheet_ids.ids)
				# vals['timesheet_ids'] = [0,0,timesheet_ids.ids]
				line_id = self.env['required.part.line'].create(vals)
				# line_id.write({'timesheet_ids': timesheet_ids.ids})

	def _get_material_lines(self):
		lines = []
		for line in self.wo_move_lines.filtered(lambda r: r.state=='done'):
			accounts = line.product_id.product_tmpl_id.get_product_accounts()
			qty_inv = line.product_uom_qty
			if qty_inv>0:
				lines.append(
					(0, 0, {
						'product_id': line.product_id.id,
						'name' : line.name,
						'account_id': accounts['income'].id,
						'quantity': qty_inv,
						'product_uom_id': line.product_uom.id or line.product_id.uom_id.id,
						'price_unit': line.price_unit,
						'tax_ids': line.product_id.taxes_id.filtered(lambda r: r.company_id.id == line.maintenance_workorder_id.company_id.id).ids,
						# 'purchase_line_id': line.id,
						# 'analytic_account_id':line.account_analytic_id and line.account_analytic_id.id or False
					})
				)
		return lines
		
	def _get_manhour_lines(self):
		lines = []
		for line in self.required_part_line.filtered(lambda r: r.type=='service'):
			accounts = line.product_id.product_tmpl_id.get_product_accounts()
			qty_inv = line.qty
			if qty_inv>0:
				lines.append(
					(0, 0, {
						'product_id': line.product_id.id,
						'name' : line.product_id.name,
						'account_id': accounts['income'].id,
						'quantity': qty_inv,
						'product_uom_id': line.uom_id.id or line.product_id.uom_id.id,
						'price_unit': line.price_unit,
						'tax_ids': line.product_id.taxes_id.filtered(lambda r: r.company_id.id == line.parent_id.company_id.id).ids,
						# 'purchase_line_id': line.id,
						# 'analytic_account_id':line.account_analytic_id and line.account_analytic_id.id or False
					})
				)
		return lines
	def create_invoice(self):
		# dotood bolo warranty dr nehemjleh uusgehgui
		self.ensure_one()
		if not self.env.user.has_group('mw_technic_maintenance.group_maintenance_invoice_user'):
			raise Warning(('Танд WO-с Нэхэмжлэл үүсгэх эрх байхгүй байна.! Систем админд хандана уу!'))
		invoice_line_ids = []
		origin = self.display_name
		if not self.invoice_ids.filtered(lambda r: r.state !='cancel'):
			self.create_add_timesheet()
			# Сэлбэг материал оноох
			invoice_line_ids += self._get_material_lines()
			# Хүн цаг оноох
			invoice_line_ids += self._get_manhour_lines()
			self.invoice_date = fields.date.today()
			if invoice_line_ids:
				journal = self.env['account.journal'].search([('type','=','sale')], limit=1)
				invoice = self.env['account.move'].create({
					'ref': origin,
					'move_type': 'out_invoice',
					'company_id': self.company_id.id,
					'partner_id': self.technic_id.partner_id.id if self.technic_id.partner_id else False,
					'journal_id': journal.id or False,
					'currency_id': self.company_id.currency_id.id,
					'invoice_line_ids': invoice_line_ids,
					'invoice_date': fields.date.today(),
					'date': self.invoice_date,
					'workorder_ids': [self.id],
				})
				# invoice.action_post()
				# self.invoice_ids = (4, invoice.id)
				self.write({'invoice_ids': [(4,invoice.id)]})
				# print(gg)

	def _get_daily_status(self, technic, date):
		log = self.env['maintenance.workorder'].search([
			('state','in',['done','closed']),
			('date_required','<=', date),
			('technic_id','=',technic.id)], order='date_required desc', limit=1)
		if log:
			return [log.description, log.performance_description]
		else:
			return False
		
	@api.onchange('warehouse_id')
	def onchange_warehouse(self):
		for item in self:
			[line.onchange_qty() for line in item.required_part_line]

	def set_all_wo_cost(self):
		wos = self.env['maintenance.workorder'].search([])
		for item in wos:
			for line in item.required_part_line:
				line.price_unit = line.product_id.standard_price

	def operator_to_partner(self):
		wos = self.env['maintenance.workorder'].search([('operator_id','!=',False)])
		for item in wos:
			item.operator_partner_id = item.operator_id.partner_id.id if item.operator_id.partner_id else False

	def print_wo(self):
		model_id = self.env['ir.model'].sudo().search([('model','=','maintenance.workorder')], limit=1)
		template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','default')], limit=1)

		if template:
			res = template.sudo().print_template(self.id)
			_logger.info('res technic.inspection: {0}'.format(res))
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

class RequiredPartLine(models.Model):
	_name = 'required.part.line'
	_description = 'Required Part Line'

	# Columns
	parent_id = fields.Many2one('maintenance.workorder', string='Parent ID', ondelete='cascade')
	parent_id_2 = fields.Many2one('maintenance.workorder', string='Parent ID2', ondelete='cascade')

	product_id = fields.Many2one('product.product', string=u'Бараа', required=True, )
	uom_id = fields.Many2one(related='product_id.uom_id', string=u'Хэмжих нэгж', store=True, readonly=True, )
	categ_id = fields.Many2one(related='product_id.categ_id', string=u'Ангилал', store=True, readonly=True, )
	qty = fields.Float(string=u'Тоо хэмжээ', required=True, default=1,)
	qty_available = fields.Float(string=u'Үлдэгдэл', default=0, )
	qty_convert_available = fields.Float(string=u'Хөрвөсөн үлдэгдэл', default=0,
		help=u'Хөрвөсөн кодтой сэлбэгийн үлдэгдлийг харуулна')
	price_unit = fields.Float(string=u'Нэгж өртөг', required=True, default=0,)
	product_cost = fields.Float(related="product_id.standard_price", readonly=True, digits=(16,2) , store=True)
	is_ordered = fields.Boolean(string=u'Захиалсан эсэх', default=False, readonly=True, )
	is_pm_material = fields.Boolean(string=u'PM материал', default=False, readonly=True, )
	move_id = fields.Many2one('stock.move', string=u'Move ID', readonly=True, )

	src_warehouse_id = fields.Many2one('stock.warehouse', u'Default агуулах')
	is_warrenty = fields.Boolean(string=u'Баталгаат эсэх', default=False)
	request_id = fields.Many2one('purchase.request', 'PR', readonly=True)
	type = fields.Selection(related='product_id.type', string='Барааны төрөл')
	timesheet_id = fields.Many2one('maintenance.employee.timesheet.line', string='Ажилтан', domain="[('parent_id','=',parent_id)]")
	account_id = fields.Many2one('account.move', string="Зардалын данс")

	last_expense_date = fields.Char(string=u'Сүүлд зарлагадсан', )
	# available_warehouse_ids = fields.One2many(string=u'Үлдэгдэлтэй агуулахууд')

	def unlink(self):
		for s in self:
			if s.is_ordered:
				raise UserError((u'Захиалсан сэлбэгийг устгаж болохгүй!'))
		return super(RequiredPartLine, self).unlink()

	@api.depends('qty','price_unit')
	def _methods_compute(self):
		for obj in self:
			obj.amount = obj.qty * obj.price_unit

	amount = fields.Float(compute=_methods_compute, store=True, string=u'Дүн')

	# @api.depends('product_id')
	# def _compute_account(self):
	# 	for item in self:
	# 		accounts_data = item.product_id.product_tmpl_id.get_product_expense_accounts(technic=item.parent_id.technic_id,branch_id=item.parent_id.branch_id)
	# 		item.account_id = accounts_data['expense_account'] if accounts_data['expense_account'] else False
	# 		analytic_account_id = accounts_data['account_analytic_id']
	# 		analytic_distribution = accounts_data['analytic_distribution']

	# Сэлбэгийн үлдэгдэл шалгах
	@api.onchange('product_id','src_warehouse_id','parent_id.warehouse_id')
	def onchange_qty(self):
		self.ensure_one()
		if self.product_id:
			quant_obj = self.env['stock.quant']
			domain = [('product_id','=',self.product_id.id),('location_id.usage','=','internal'),'|',('company_id','=',self.parent_id.company_id.id),('company_id','=',False)]
			# Агуулах сонгосон бол агуулахаас хайх
			if self.src_warehouse_id:
				domain.append(('location_id.set_warehouse_id','=',self.src_warehouse_id.id))
			elif self.parent_id.warehouse_id:
				domain.append(('location_id.set_warehouse_id','=',self.parent_id.warehouse_id.id))
			quant_ids = quant_obj.sudo().search(domain)
			qty = 0
			qty = sum(quant_ids.mapped('quantity'))
			self.qty_available = qty
			# Хөрвөсөн кодтой барааны үлдэгдэл
			domains = [('product_id','!=',self.product_id.id),
						 ('product_id.product_tmpl_id','=', self.product_id.product_tmpl_id.id),
						 ('location_id.usage','=', 'internal')]
			if self.parent_id.warehouse_id:
				domains.append(('location_id.set_warehouse_id','=', self.parent_id.warehouse_id.id))

			quant_template_ids = quant_obj.sudo().search(domains)
			qty = 0
			qty = sum(quant_template_ids.mapped('quantity'))
			self.qty_convert_available = qty
			
			self.price_unit = self.product_id.standard_price

			# Хамгийн сүүлд зарлага хийсэн огноо
			if self.parent_id.technic_id:
				move = self.env['stock.move'].search([
					('technic_id','=',self.parent_id.technic_id.id),
					('state','=','done'),
					('picking_id.picking_type_id.code','=','outgoing'),
					('product_id','=',self.product_id.id)], limit=1, order='date desc')
				if move:
					self.last_expense_date = move.date
				else:
					self.last_expense_date = u'Өмнө нь гараагүй'

	def action_open_quants(self):
		domain = [('product_id', 'in', self.ids)]
		hide_location = not self.user_has_groups('stock.group_stock_multi_locations')
		hide_lot = all([product.tracking == 'none' for product in self])
		self = self.with_context(hide_location=hide_location, hide_lot=hide_lot)

		# If user have rights to write on quant, we define the view as editable.
		if self.user_has_groups('stock.group_stock_manager'):
			self = self.with_context(inventory_mode=True)
			# Set default location id if multilocations is inactive
			if not self.user_has_groups('stock.group_stock_multi_locations'):
				user_company = self.env.company
				warehouse = self.env['stock.warehouse'].search(
					[('company_id', '=', user_company.id)], limit=1
				)
				if warehouse:
					self = self.with_context(default_location_id=warehouse.lot_stock_id.id)
		# Set default product id if quants concern only one product
		if len(self) == 1:
			self = self.with_context(
				default_product_id=self.id,
				single_product=True
			)
		else:
			self = self.with_context(product_tmpl_ids=self.product_tmpl_id.ids)
		ctx = dict(self.env.context)
		ctx.update({'no_at_date': True, 'search_default_on_hand': True})
		return self.env['stock.quant'].with_context(ctx)._get_quants_action(domain)

class MaintenanceWorkTimesheetLine(models.Model):
	_name = 'maintenance.work.timesheet.line'
	_description = 'Maintenance Work Timesheet Line'

	# Columns
	parent_id = fields.Many2one('maintenance.workorder', 'Parent ID', ondelete='cascade')

	delay_reason_id = fields.Many2one('maintenance.delay.reason', u'Ажлын нэр', required=True, )
	date_start = fields.Datetime(string=u'Эхлэсэн цаг', required=True, copy=False,)
	date_end = fields.Datetime(string=u'Дууссан цаг', required=True, copy=False,)

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
					raise UserError((u'Цагийг зөв оруулна уу! /Зогсолт/'))
			obj.spend_time = time

	spend_time = fields.Float(compute=_compute_time, store=True, string=u'Зарцуулсан цаг')

class MaintenanceEmployeeTimesheetLine(models.Model):
	_name = 'maintenance.employee.timesheet.line'
	_description = 'Maintenance Employee Timesheet Line'

	# Columns
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id)
	parent_id = fields.Many2one('maintenance.workorder', string='Parent ID', ondelete='cascade')
	parent_id_2 = fields.Many2one('maintenance.call', string='Parent Call ID', ondelete='cascade')
	#gkk technic inspection tsag burtgel
	parent_id_3 = fields.Many2one('technic.inspection', string='Parent ID', ondelete='cascade')

	employee_id = fields.Many2one('hr.employee', string=u'Засварчин')
	emp_partner_id = fields.Many2one('res.partner', string=u'Засварчин')
	job_id = fields.Many2one('hr.job', 'Албан тушаал')
	other_employee_ids = fields.Many2many('hr.employee', string=u'Нэмэлт засварчид')
	technic_id = fields.Many2one('technic.equipment', string='Техник')
	product_id = fields.Many2one('product.product', string=u'Labor product', domain="[('sale_ok','=',True),('type','=','service')]")
	part_lines = fields.One2many('required.part.line', 'timesheet_id', string='Order lines')

	date_start = fields.Datetime(string=u'Эхэлсэн цаг', copy=False,)
	date_end = fields.Datetime(string=u'Дууссан цаг', copy=False,)

	state = fields.Selection(related='parent_id.state', string=u'Төлөв', store=True, readonly=True, )

	state2 = fields.Selection(
		[('draft','Ноорог'),
		 ('confirmed','Батлагдсан')],
		string=u'Төлөв', readonly=True, default='draft')

	notes = fields.Char(string=u'Дэлгэрэнгүй')
	mechanic_cause = fields.Selection([('shift_swap','Ээлж солилцох'),
										('break_time','Цайны цаг'),
										('naryd','Наряд'),
										('tire','Дугуй'),
										('welding','Гагнуур'),
										('inspection','Үзлэг'),
										('lubrication','Тосолгоо'),
										('training','Сургалт'),
										('site_cleaning','Талбайн цэвэрлэгээ'),
										('other_work','Бусад ажил')], string=u"Засварчны ажлын шалтгаан")

	# @api.onchange('emp_partner_id')
	# def onchange_emp_partner_id(self):
	# 	if self.emp_partner_id:
	# 		self.job_id = self.emp_partner_id.job_id.id
	# 		self.emp_name_melen = self.emp_partner_id.last_name[:1]

	@api.depends('date_start','date_end')
	def _compute_time(self):
		for obj in self:
			time = 0
			o1 = 0
			o2 = 0
			if obj.date_start and obj.date_end:
				# Ажилласан цаг
				date = obj.date_start
				end_date = obj.date_end
				time = (end_date-date).total_seconds() / (60*60)
				# Зарцуулсан цаг + байх ёстой
				if time < 0:
					raise UserError((u'Цагийг зөв оруулна уу! /Засварчин/'))

			obj.spend_time = time
			obj.over_time = 0

	spend_time = fields.Float(compute=_compute_time, store=True, string=u'Зарцуулсан цаг')
	over_time = fields.Float(compute=_compute_time, store=True, string=u'Илүү цаг', default=0 )

	emp_other_creator_id = fields.Many2one('maintenance.employee.other.timesheet', 'Emp timesheet creator')

	def action_to_confirm(self):
		self.state2 = 'confirmed'

	guitsetgel_time = fields.Float(compute='_compute_time_guitsetgel', store=True, string=u'Гүйцэтгэлд тооцох цаг', readonly=False)
	@api.depends('date_start','date_end')
	def _compute_time_guitsetgel(self):
		for obj in self:
			time = 0
			if obj.date_start and obj.date_end:
				# Ажилласан цаг
				date = obj.date_start
				end_date = obj.date_end
				time = (end_date-date).total_seconds() / (60*60)
			obj.guitsetgel_time = time

# Засварт ашигласан багаж хэрэгсэл
class WoPlannedTimeLine(models.Model):
	_name = 'wo.planned.time.line'
	_description = 'Wo Planned Time Line'

	parent_id = fields.Many2one('maintenance.workorder', 'Parent ID', ondelete='cascade')
	planned_date = fields.Date(string=u'Төлөвлөсөн өдөр', required=True,)
	planned_time = fields.Float(string=u'Төлөвлөсөн цаг', default=0, required=True,)

# Засварт ашигласан багаж хэрэгсэл
class UseEquipmentLine(models.Model):
	_name = 'use.equipment.line'
	_description = 'Use equipment line'

	parent_id = fields.Many2one('maintenance.workorder', 'Parent ID', ondelete='cascade')
	user_id = fields.Many2one('res.users', string=u'Хүлээн авсан хэрэглэгч', readonly=True)
	# asset_id = fields.Many2one('account.asset.asset', string=u'Бараа', required=True,
	# 	domain=[('collateral_state','=','ready')],
	# 	)
	used_time = fields.Float(string=u'Хэрэглэсэн цаг', default=0, required=True,)
	# collateral_state = fields.Selection(related='asset_id.collateral_state', readonly=True, store=True)

	def receive_equipment(self):
		if self.parent_id.state != 'closed':
			if self.asset_id.collateral_state == 'in_shipping':
				self.asset_id.collateral_state = 'ready'
				self.user_id = self.env.user.id

	def lost_equipment(self):
		if self.parent_id.state != 'closed':
			if self.asset_id.collateral_state == 'in_shipping':
				self.asset_id.collateral_state = 'lost'
				self.user_id = self.env.user.id
				self.asset_id.set_to_close()

class MaintenanceEmployeeOtherTimesheet(models.Model):
	_name = 'maintenance.employee.other.timesheet'
	_description = 'Maintenance Employee Other Timesheet'

	employee_id = fields.Many2many('hr.employee', string=u'Засварчин', required=True, )
	technic_id = fields.Many2one('technic.equipment', string='Техник')
	technic_id = fields.Many2one('technic.equipment', string='Техник')
	damaged_reason_id = fields.Many2one('maintenance.damaged.reason', string=u'Эвдрэлийн шалтгаан', copy=False,
		states={'confirmed': [('readonly', True)]})
	damaged_type_id = fields.Many2one('maintenance.damaged.type', string=u'Эвдрэлийн төрөл', copy=False,
		states={'closed': [('readonly', True)]})
	date_start = fields.Datetime(string=u'Эхэлсэн цаг', copy=False,)
	date_end = fields.Datetime(string=u'Дууссан цаг', copy=False,)

	notes = fields.Char(string=u'Дэлгэрэнгүй')
	mechanic_cause = fields.Selection([('shift_swap','Ээлж солилцох'),
										('break_time','Цайны цаг'),
										('naryd','Наряд'),
										('tire','Дугуй'),
										('welding','Гагнуур'),
										('inspection','Үзлэг'),
										('lubrication','Тосолгоо'),
										('training','Сургалт'),
										('site_cleaning','Талбайн цэвэрлэгээ'),
										('other_work','Бусад ажил')], string=u"Засварчны ажлын шалтгаан")



	@api.depends('date_start','date_end')
	def _compute_time(self):
		for obj in self:
			time = 0
			o1 = 0
			o2 = 0
			if obj.date_start and obj.date_end:
				# Ажилласан цаг
				date = obj.date_start
				end_date = obj.date_end
				time = (end_date-date).total_seconds() / (60*60)
				# Зарцуулсан цаг + байх ёстой
				if time < 0:
					raise UserError((u'Цагийг зөв оруулна уу! /Засварчин бусад/'))

			obj.spend_time = time
			obj.over_time = 0

	spend_time = fields.Float(compute=_compute_time, store=True, string=u'Зарцуулсан цаг')
	over_time = fields.Float(compute=_compute_time, store=True, string=u'Илүү цаг', default=0 )

	emp_timesheet_line_id = fields.One2many('maintenance.employee.timesheet.line','emp_other_creator_id', string=u'Employee timesheet lines')

	state = fields.Selection(
		[('draft','Ноорог'),
		('confirmed','Батлагдсан')],
		string=u'Төлөв', readonly=True, default='draft')

	def action_to_confirm(self):
		self.state = 'confirmed'
		emp_obj = self.env['maintenance.employee.timesheet.line']
		for item in self.employee_id:
			vals = {
				'employee_id': item.id,
				'technic_id': self.technic_id.id,
				'date_start': self.date_start,
				'date_end': self.date_end,
				'state2': 'confirmed',
				'notes': self.notes,
				'mechanic_cause': self.mechanic_cause,
				'spend_time': self.spend_time,
				'over_time': self.over_time,
				'emp_other_creator_id': self.id,
			}
			emp_obj.create(vals)

	def see_employee_other_timesheet_line(self):
		action = self.env.ref('mw_technic_maintenance.action_maintenance_employee_timesheet_line').read()[0]
		action['domain'] = [('emp_other_creator_id','=', self.id)]
		action['context'] = []
		return action

	def print_other_timesheet(self):
		model_id = self.env['ir.model'].sudo().search([('model','=','maintenance.employee.other.timesheet')], limit=1)
		template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','default')], limit=1)

		if template:
			res = template.sudo().print_template(self.id)
			_logger.info('res technic.inspection: {0}'.format(res))
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

class account_move(models.Model):
	_inherit = 'account.move'

	# workorder_id = fields.Many2one('maintenance.workorder', string='Workorder ID', copy=False)
	workorder_ids = fields.Many2many('maintenance.workorder', string='Workorder IDs', copy=False)
	workorder_count = fields.Integer(string='Number of Workorder', compute="_compute_workorder_count")

	@api.depends('workorder_ids')
	def _compute_workorder_count(self):
		for item in self:
			item.workorder_count = len(item.workorder_ids)
			
	def view_workorder(self):
		self.ensure_one()
		action = self.env.ref('mw_technic_maintenance.action_maintenance_workorder').read()[0]
		action['domain'] = [('id','in',self.workorder_ids.ids)]
		return action
		
# class productProduct(models.Model):
# 	_inherit = 'product.product'

# 	def write(self, vals):
# 		# print('original',vals)
# 		if not self.user_has_groups('mw_technic_maintenance.group_maintenance_superintendent'):
# 			vals.pop('lst_price')
# 			# print('changed',vals)
# 		res = super(productProduct, self).write(vals)
# 		return res