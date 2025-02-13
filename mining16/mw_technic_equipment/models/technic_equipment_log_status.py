# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections

class TechnicEquipmentLogStatus(models.Model):
	_name = 'technic.equipment.log.status'
	_description = 'Technic equipment log status'
	_order = 'date_time desc, report_order, program_code'
	_rec_name = 'technic_id'

	@api.model
	def _get_user(self):
		return self.env.user.id

	@api.model
	def _get_current_technic(self):
		if self._context.get('technic_id'):
			return self._context.get('technic_id')
		return False

	date_time = fields.Datetime(string=u'Эхэлсэн цаг', required=True, default=fields.Datetime.now, 
		states={'confirmed':[('readonly', True)]})
	technic_id = fields.Many2one('technic.equipment', string=u'Техник', required=True,
		states={'confirmed':[('readonly', True)]}, default=_get_current_technic)
	report_order = fields.Char(related='technic_id.report_order', string=u'Sort',
		store=True, readonly=True, ) 
	program_code = fields.Char(related='technic_id.program_code', string=u'Sort 2', readonly=True, store=True)
	odometer = fields.Float(string=u'Гүйлт', required=True, help="Тухайн үедийн гүйлт",
		states={'confirmed':[('readonly', True)]})
	work_time = fields.Float(string=u'Ажилласан цаг', default=0, 
		states={'confirmed':[('readonly', True)]})

	is_last = fields.Boolean(string=u'Сүүлийнх эсэх', default=False)

	state = fields.Selection([
			('draft','Ноорог'),
			('confirmed','Батлагдсан')], string='Төлөв', 
		readonly=True, default='draft', )

	status_type = fields.Selection([
			('waiting_for_spare','Сэлбэг хүлээж зогссон'),
			('waiting_for_tire','Дугуй хүлээж зогссон'),
			('working','Ажиллаж байгаа'),
			('repairing','Засварт орсон'),
			('inspection','Үзлэг хийж байгаа'),
			('parking','Паркласан')], string='Status', required=True,
		states={'confirmed':[('readonly', True)]})

	note = fields.Text(string='Дэлгэрэнгүй тайлбар', required=True,
		states={'confirmed':[('readonly', True)]})
	user_id = fields.Many2one('res.users', string=u'Бүртгэсэн', readonly=True, 
		default=_get_user)
	before_id = fields.Many2one('technic.equipment.log.status', string=u'Өмнөх бүртгэл', readonly=True, )
	
	spend_time = fields.Float(string='Зарцуулсан цаг', compute='_compute_spend_time', store=True, readonly=True, digits=(16,2))
	@api.depends('date_time','odometer','technic_id','state')
	def _compute_spend_time(self):
		for obj in self:
			domains = []
			if obj.technic_id and obj.state == 'confirmed':
				domains = [('technic_id','=',obj.technic_id.id),('date_time','<',obj.date_time),('state','=','confirmed')]
			if domains and isinstance(obj.id, int):
				ll = self.env['technic.equipment.log.status'].sudo().search(domains, order='date_time desc', limit=1)
				if ll:
					secs = (obj.date_time-ll.date_time).total_seconds()
					obj.spend_time = secs/3600
					if not obj.before_id:
						obj.before_id = ll.id
				else:
					obj.spend_time = 0
			else:
				obj.spend_time = 0

	# =================== OVERRIDED ================
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('Ноороглох ёстой!'))
		return super(TechnicEquipmentLogStatus, self).unlink()

	# =================== CUSTOM methods ===========
	def action_to_draft(self):
		self.state = 'draft'

	def action_to_confirm(self):
		if self.status_type == 'parking':
			self.technic_id.state = 'parking'
		elif self.status_type == 'waiting_for_spare':
			self.technic_id.state = 'stopped'
		elif self.status_type == 'waiting_for_tire':
			self.technic_id.state = 'stopped'
		elif self.status_type == 'working':
			self.technic_id.state = 'working'
		elif self.status_type in ['repairing','inspection']:
			self.technic_id.state = 'repairing'
		self.technic_id.status_note = self.note if self.status_type != 'working' else ''
		self.state = 'confirmed'
		self.user_id = self.env.user.id
		# Сүүлийн бүртгэл эсэхийг шалгах
		domains = [('technic_id','=',self.technic_id.id),('date_time','>=',self.date_time),('state','=','confirmed')]
		ll = self.env['technic.equipment.log.status'].sudo().search(domains, order='date_time desc', limit=1)
		if ll:
			ll.is_last = True
		# Өмнөх бүртгэлийг SET хийх
		if self.before_id:
			domains = [('technic_id','=',self.technic_id.id),('date_time','<',self.date_time),('state','=','confirmed')]
			ll = self.env['technic.equipment.log.status'].sudo().search(domains, order='date_time desc', limit=1)
			if ll:
				ll.is_last = False
				self.before_id = ll.id

	@api.onchange('technic_id')
	def onchange_technic_id(self):
		if self.technic_id:
			self.odometer = self.technic_id.total_odometer if self.technic_id.odometer_unit == 'motoh' else self.technic_id.total_km
	
	@api.onchange('status_type')
	def onchange_status_type(self):
		if self.status_type:
			if self.status_type == 'waiting_for_spare':
				self.note = 'Сэлбэг хүлээж зогссон'
			elif self.status_type == 'waiting_for_tire':
				self.note = 'Дугуй хүлээж зогссон'
			elif self.status_type == 'working':
				self.note = 'Ажиллаж байгаа'
			elif self.status_type == 'repairing':
				self.note = 'Засварт орсон'
			elif self.status_type == 'inspection':
				self.note = 'Үзлэг хийж байгаа'
			elif self.status_type == 'parking':
				self.note = 'Паркласан'

	# Техник дээрх сүүлийн статус авах
	def _get_last_log_status(self, technic):
		log = self.env['technic.equipment.log.status'].search([
			('state','=','confirmed'),
			('technic_id','=',technic.id)], order='date_time desc', limit=1)
		if log:
			return [log.status_type, log.note]
		else:
			return False
	def _get_last_log(self, technic):
		log = self.env['technic.equipment.log.status'].search([
			('state','=','confirmed'),
			('technic_id','=',technic.id)], order='date_time desc', limit=1)
		if log:
			return log
		else:
			return False