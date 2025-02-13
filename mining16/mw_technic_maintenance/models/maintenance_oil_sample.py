# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import time

class MaintenanceOilSample(models.Model):
	_name = 'maintenance.oil.sample'
	_description = 'maintenance.oil.sample'
	_order = 'date_sample desc'
	_inherit = ['mail.thread']

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,
		states={'sent_sample':[('readonly',True)],'received_response':[('readonly', True)],
				'closed':[('readonly', True)]})
	company_id = fields.Many2one('res.company', string=u'Компани', required=True, default=lambda self: self.env.user.company_id)

	name = fields.Char(string=u'Дугаар', readonly=True, copy=False )
	date = fields.Datetime(string=u'Үүсгэсэн огноо', default=datetime.now(), readonly=True)
	date_sample = fields.Date(string=u'Дээж авсан огноо', required=True,
		states={'sent_sample':[('readonly',True)],'received_response':[('readonly', True)],
				'closed':[('readonly', True)]})
	date_sent = fields.Date(string=u'Илгээсэн огноо',
		states={'sent_sample':[('readonly',True)],'received_response':[('readonly', True)],
				'closed':[('readonly', True)]})
	description = fields.Text(string=u'Тайлбар',
		states={'sent_sample':[('readonly',True)],'received_response':[('readonly', True)],
				'closed':[('readonly', True)]})
	technic_id = fields.Many2one('technic.equipment', string=u'Техник', copy=True, required=True,
	 	help=u"Choose the technic", domain=[('state','in',['stopped','repairing','working'])],
	 	states={'sent_sample':[('readonly',True)],'received_response':[('readonly', True)],
	 			'closed':[('readonly', True)]})
	technic_odometer = fields.Float(string='Техникийн мото/цаг', required=True,
		states={'sent_sample':[('readonly',True)],'received_response':[('readonly', True)],
				'closed':[('readonly', True)]})
	damaged_type_id = fields.Many2one('maintenance.damaged.type', string=u'Дээж авсан систем', copy=False,
		states={'sent_sample':[('readonly',True)],'received_response':[('readonly', True)],
				'closed':[('readonly', True)]},
		domain="[('is_oil_sample','=',True)]")
	oil_type_id = fields.Many2one('product.product', string=u'Тосны төрөл', copy=False,
		states={'sent_sample':[('readonly',True)],'received_response':[('readonly', True)],
				'closed':[('readonly', True)]})

	user_id = fields.Many2one('res.users', string=u'Клерк', default=_get_user, readonly=True)
	validator_id = fields.Many2one('res.users', string=u'Баталсан', readonly=True, copy=False,)

	response_type = fields.Selection([
		('no_action_required','No action required'),
		('monitor_compartment','Monitor compartment'),
		('action_required','Action required')], string='Хариуны төрөл',
		states={'received_response':[('readonly', True)],
				'closed':[('readonly', True)]})

	response_id = fields.Char(string=u"Хариуны дугаар",
		states={'sent_sample':[('required',True)],'received_response':[('readonly', True)],'closed':[('readonly', True)]})
	response_description = fields.Text(string=u'Дээжний хариу',
		states={'received_response':[('readonly', True)],'closed':[('readonly', True)]})
	action_description = fields.Text(string=u'Авсан арга хэмжээ',
		states={'closed':[('readonly', True)]})
	workorder_id = fields.Many2one('maintenance.workorder', string=u'REF WO', readonly=True, )
	date_response = fields.Datetime(string=u'Хариу ирсэн огноо',
		states={'closed':[('readonly', True)]})
	date_close = fields.Datetime(string=u'Хаасан огноо', readonly=True, copy=False,)
	attachment = fields.Binary(string=u"Хавсралт",
		states={'sent_sample':[('readonly',True)],'closed':[('readonly', True)]})
	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),],
			string=u'Ээлж', required=True,
			states={'sent_sample':[('readonly',True)],'received_response':[('readonly', True)],
				'closed':[('readonly', True)]})
	state = fields.Selection([
		('draft', u'Ноорог'),
		('sent_sample', u'Дээж илгээсэн'),
		('received_response', u'Хариу ирсэн'),
		('closed', u'Хаагдсан'),],
		default='draft', string=u'Төлөв', tracking=True)

	
	customer_id = fields.Many2one('res.partner', string='Customer')
	mining_site = fields.Char('Mining site')
	machine_serial = fields.Char(related='technic_id.vin_number', string='Machine serial')
	fleet_number = fields.Char(related='technic_id.state_number', string='Fleet number')
	# machine_SMU = fields.Char(related='technic_id.program_code', string='Machine SMU')


	sample_date = fields.Date('Sample Date')
	sample_number = fields.Char('Sample Number')
	comportment_system = fields.Selection([
		('Engine','Engine'),
		('Engine_1','Engine 1'),
		('Engine_2','Engine 2'),
		('Splitter_box','Splitter box'),
		('Splitter_box_1','Splitter box 1'),
		('Splitter_box_2','Splitter box 2'),
		('Swing_box','Swing box'),
		('Rear_swing_box','Rear swing box'),
		('Front.swing.box','Front swing box'),
		('Rear.RH.swing.box','Rear RH swing box'),
		('Rear.LH.swing.box','Rear LH swing box'),
		('Front.RH.swing.box','Front RH swing box'),
		('Front.LH.swing.box','Front LH swing box'),
		('Final.drive','Final drive'),
		('Front.LH.final.drive','Front LH final drive'),
		('Front.RH.final.drive','Front RH final drive'),
		('Rear.LH.final.drive','Rear LH final drive'),
		('Rear.RH.final.drive','Rear RH final drive'),
		('LH.final.drive','LH final drive'),
		('RH.final.drive','RH final drive'),
		('Diffential','Diffential'),
		('Front.differential','Front differential'),
		('Rear.differential','Rear differential'),
		('Wheel.hub','Wheel hub'),
		('Front.LH.wheel.hub','Front LH wheel hub'),
		('Front.RH.wheel.hub','Front RH wheel hub'),
		('Axle','Axle'),
		('Front.axle','Front axle'),
		('Rear.axle','Rear axle'),
		('Hydraulic','Hydraulic'),
		('Steering','Steering'),
		('Transmission','Transmission'),
		('Transfer.gear','Transfer gear'),
		('Gear.box','Gear box'),
		('Coolant','Coolant'),
		('Fuel','Fuel'),
		('Lube.system','Lube system'),
		('Bearing.housing','Bearing housing'),
	], string="Comportment system",)
	component_hours = fields.Float('Component hours')
	oil_categ_id = fields.Many2one(related='oil_type_id.categ_id', string='Oil type')
	# oil_brand_id = fields.Many2one(related='oil_type_id.brand_id', string='Oil brand')
	oil_hours = fields.Float(string='Oil hours')
	response_type = fields.Selection([
		('no_action_required','No action required'),
		('monitor_compartment','Monitor compartment'),
		('action_required','Action required')], string='Хариуны төрөл',)
	comment = fields.Char('Comment')
	attach_file_ids = fields.Many2many('ir.attachment', string='Attach file')
	component_id = fields.Many2one('technic.component.part', string='Компонент', options="{'no_create': True}", required=True)
	component_serial= fields.Char(related='component_id.serial_number', string='Компонент сериал дугаар')
	component_part_number = fields.Char(related='component_id.real_part_number', string='Компонент эд ангийн дугаар')


	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй бичлэгийг устгаж болно!'))
		return super(MaintenanceOilSample, self).unlink()

	# ===================================== Custom methods ------------------------------
	def action_to_draft(self):
		self.state = 'draft'

	def action_to_send(self):
		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code('maintenance.oil.sample')
		self.state = 'sent_sample'
		if not self.date_sent:
			self.date_sent = datetime.now()

	def action_create_workorder(self):
		# WO үүсгэх
		vals = {
			'date_required': datetime.now(),
			'maintenance_type': 'not_planned',
			'origin': self.name,
			'branch_id': self.branch_id.id,
			 'technic_id': self.technic_id.id,
			'description': self.response_description,
			 'start_odometer': self.technic_id.total_odometer,
			'shift': self.shift,
			'contractor_type': 'internal',
		}
		wo_id = self.env['maintenance.workorder'].create(vals)
		self.workorder_id = wo_id.id
		self.validator_id = self.env.user.id

	def action_to_receive(self):
		if not self.response_type:
			raise UserError(_(u'Хариуны төрлийг сонгоно уу!'))
		if not self.date_response:
			self.date_response = datetime.now()
		self.state = 'received_response'

	def action_to_close(self):
		if not self.action_description and self.response_type in ['monitor_compartment','action_required']:
			raise UserError(_(u'Авсан арга хэмжээг оруулна уу!'))
		self.date_close = datetime.now()
		self.state = 'closed'

	def action_send_checker(self):
		partner_ids = []
		res_model = self.env['ir.model.data'].search([
				('module','=','mw_technic_maintenance'),
				('name','in',['group_sending_messages_from_oil_sample'])])
		groups = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data']._xmlid_lookup('mw_technic_maintenance.action_maintenance_oil_sample')[2]
		html = u'<b>Тосны бүртгэлийг Хянана уу</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&action=%s&model=maintenance.oil.sample&view_type=form>%s</a></b>, дугаартай Тосны бүртгэлийг Хянана уу"""% (base_url,self.id,action_id,self.name)					
		for group in groups:
			for receiver in group.users:
				if receiver.partner_id:
					partner_ids.append(receiver.partner_id)
		# self.env.user.send_chat(html, partner_ids, True, 'Тоосны дээжны хариу')
		self.env.user.send_emails(partners=partner_ids, subject='Тоосны дээжны хариу', body=html, attachment_ids=False)
