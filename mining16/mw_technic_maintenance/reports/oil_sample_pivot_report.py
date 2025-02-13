# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class OilSamplePivotReport(models.Model):
	_name = "oil.sample.pivot.report"
	_description = "Maintenance expense report"
	_auto = False
	_order = 'product_id'

	name = fields.Char(string=u'Нэр', readonly=True,  )
	branch_id = fields.Many2one('res.branch', u'Салбар', readonly=True,  )
	date_sample = fields.Date(u'Дээж авсан огноо', readonly=True, )
	date_sent = fields.Date(u'Илгээсэн огноо', readonly=True, )
	date_response = fields.Date(u'Хариу ирсэн огноо', readonly=True, )

	technic_id = fields.Many2one('technic.equipment', string=u'Техник', readonly=True,  )
	oil_type_id = fields.Many2one('product.product', string=u'Тосны төрөл', readonly=True, )
	damaged_type_id = fields.Many2one('maintenance.damaged.type', u'Дээж авсан систем', readonly=True, )

	response_type = fields.Selection([
		('no_action_required','No action required'),
		('monitor_compartment','Monitor compartment'),
		('action_required','Action required')], string=u'Хариуны төрөл', readonly=True, )
	response_description = fields.Char(string=u'Дээжний хариу', readonly=True, )
	action_description = fields.Char(string=u'Авсан арга хэмжээ', readonly=True, )

	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),], 
			string=u'Ээлж', readonly=True, )

	workorder_id = fields.Many2one('maintenance.workorder', string=u'Холбоотой WO', readonly=True, )

	state = fields.Selection([
		('draft', u'Ноорог'),
		('sent_sample', u'Дээж илгээсэн'),
		('received_response', u'Хариу ирсэн'),
		('closed', u'Хаагдсан'),], 
		default='draft', string=u'Төлөв', readonly=True, )
	
	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
				SELECT  
					oil.branch_id as branch_id,
					oil.id as id,
					oil.name as name,
					oil.date_sample as date_sample,
					oil.date_sent as date_sent,
					oil.date_response as date_response,
					oil.technic_id as technic_id,
					oil.oil_type_id as oil_type_id,
					oil.damaged_type_id as damaged_type_id,
					oil.response_type as response_type,
					oil.response_description as response_description,
					oil.action_description as action_description,
					oil.shift as shift,
					oil.workorder_id as workorder_id,
					oil.state
				FROM maintenance_oil_sample as oil
				WHERE oil.state != 'draft'
			)""" % self._table)

