# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time

class PartnerSpecialProductPlan(models.Model):
	_name = 'partner.special.product.plan'
	_description = 'Partner Special Product Plan'
	_order = 'date_start desc, salesman_id'

	# Columns
	date = fields.Datetime(u'Created date', readonly=True, default=fields.Datetime.now(), copy=False)
	name = fields.Char(u'Description', copy=True, required=True, 
		states={'confirmed': [('readonly', True)]})

	crm_team_id = fields.Many2one('crm.team', string='Суваг', states={'confirmed': [('readonly', True)]}, )
	salesman_id = fields.Many2one('res.users', u'Salesman', copy=False, 
		states={'confirmed': [('readonly', True)]})

	partner_category_ids = fields.Many2many('res.partner.category', string=u'Харилцагчийн ангилал', copy=False,
		states={'confirmed': [('readonly', True)]})

	partner_ids = fields.Many2many('res.partner', string=u'Харилцагчид', copy=False,
		states={'confirmed': [('readonly', True)]})

	line_ids = fields.One2many('partner.special.product.plan.line','parent_id', 
		string=u'Бараанууд', copy=True, 
		states={'confirmed': [('readonly', True)]}, required=True,)

	date_start = fields.Date('Start date', copy=True, required=True,
		states={'confirmed': [('readonly', True)]}, )
	date_end = fields.Date('End date', copy=True, required=True,
		states={'confirmed': [('readonly', True)]}, )

	state = fields.Selection([
			('draft', 'Draft'), 
			('confirmed', 'Confirmed'),
		], default='draft', required=True, string='State', 
		states={'confirmed': [('readonly', True)]})

	must_sale = fields.Selection([
			('yes', 'Yes'), 
			('no', 'No'),
		], default='no', required=True, string='Заавал борлуулах')

	# ----------- OVERRIDED ====================
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('In order to delete a record, it must be draft first!'))
		return super(PartnerSpecialProductPlan, self).unlink()
	# --------- CUSTOM ===========================
	def action_to_draft(self):
		self.state = 'draft'

	def action_to_confirm(self):
		if not self.partner_ids and not self.partner_category_ids:
			raise UserError(_(u'Харилцагчид эсвэл Харилцагчийн ангилал сонгоно уу!'))

		if not self.line_ids:
			raise UserError(_(u'Барааг оруулна уу!'))

		self.state = 'confirmed'

class PartnerSpecialProductPlanLine(models.Model):
	_name = 'partner.special.product.plan.line'
	_description = 'Partner Special Product Plan Line'
	_order = 'product_id'

	parent_id = fields.Many2one('partner.special.product.plan', string=u'Parent', ondelete='cascade')
	product_id = fields.Many2one('product.product', string=u'Бараа', copy=True, required=True,)
	qty = fields.Integer(string=u'Тоо ширхэг', default=0, required=True,)

