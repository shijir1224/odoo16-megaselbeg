# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import time

class MaintenanceDemsInfo(models.Model):
	_name = 'maintenance.dems.info'
	_description = 'maintenance.dems.info'
	_order = 'date_receive desc'
	_inherit = ['mail.thread']

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,
		states={'received':[('readonly', True)],'closed':[('readonly', True)]})

	name = fields.Char(string=u'Дугаар', copy=False, required=True,
		states={'received':[('readonly', True)],'closed':[('readonly', True)]} )
	date = fields.Datetime(u'Үүссэн огноо', default=datetime.now(), readonly=True)
	date_receive = fields.Date(string=u'Мэдээ ирсэн огноо', required=True, 
		states={'received':[('readonly', True)],'closed':[('readonly', True)]})
	description = fields.Text(string=u'Ирсэн мэдээлэл', required=True,
		states={'received':[('readonly', True)], 'closed':[('readonly', True)]})
	technic_id = fields.Many2one('technic.equipment', string=u'Техник', copy=True, required=True,
		help=u"Choose the technic", domain=[('state','in',['stopped','repairing','working'])],
		states={'received':[('readonly', True)], 'closed':[('readonly', True)]})
	technic_odometer = fields.Float(string='Техникийн гүйлт', required=True,
		states={'received':[('readonly', True)], 'closed':[('readonly', True)]})	

	damaged_type_id = fields.Many2one('maintenance.damaged.type', string=u'Систем', copy=False,
		states={'received':[('readonly', True)], 'closed':[('readonly', True)]})
	
	user_id = fields.Many2one('res.users', string=u'Клерк', default=_get_user, readonly=True)
	validator_id = fields.Many2one('res.users', string=u'Баталсан', readonly=True, copy=False,)

	# response_type = fields.Selection([
	# 	('no_action_required','No action required'),
	# 	('monitor_compartment','Monitor compartment'),
	# 	('action_required','Action required')], string='Response type',
	# 	states={'received':[('readonly', True)],
	# 			'closed':[('readonly', True)]})

	action_description = fields.Text(string=u'Авсан арга хэмжээ', 
		states={'closed':[('readonly', True)]})
	workorder_id = fields.Many2one('maintenance.workorder', string=u'Холбоотой WO', readonly=True, )
	date_close = fields.Datetime(string=u'Хаасан огноо', readonly=True, copy=False,)
	
	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),], 
			string=u'Ээлж', required=True,
			states={'received':[('readonly', True)],'closed':[('readonly', True)]})
	state = fields.Selection([
		('draft', u'Ноорог'),
		('received', u'Мэдээ ирсэн'),
		('closed', u'Хаагдсан'),], 
		default='draft', string=u'Төлөв', tracking=True)

	# ===================================== OVERRIDED methods ==========================
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй бичлэгийг устгаж болно!'))
		return super(MaintenanceDemsInfo, self).unlink()

	# ===================================== Custom methods ------------------------------
	def action_to_draft(self):
		self.state = 'draft'

	def action_to_receive(self):
		self.state = 'received'

	def action_create_workorder(self):
		if self.workorder_id:
			raise UserError(_(u'WO үүссэн байна!'))
		# WO үүсгэх
		vals = {
			'date_required': datetime.now(),
			'maintenance_type': 'not_planned',
			'origin': self.name,
			'branch_id': self.branch_id.id,
			'technic_id': self.technic_id.id,
			'description': self.description,
			'start_odometer': self.technic_id.total_odometer,
			'contractor_type': 'internal',
		}
		wo_id = self.env['maintenance.workorder'].create(vals)
		self.workorder_id = wo_id.id
		self.validator_id = self.env.user.id

	def action_to_close(self):
		if not self.action_description:
			raise UserError(_(u'Авсан арга хэмжээг оруулна уу!'))
		self.date_close = datetime.now()
		self.state = 'closed'
