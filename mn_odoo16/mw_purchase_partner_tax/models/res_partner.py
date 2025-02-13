# -*- coding: utf-8 -*-
from odoo import fields, models, api

class ResPartner(models.Model):
	_inherit = 'res.partner'

	po_taxes_id = fields.Many2many('account.tax','partner_po_taxes_rel','partner_id','tax_id',u'PO taxes', domain=[('type_tax_use','=','purchase')])

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	@api.onchange('partner_id')
	def change_po_part(self):
		if self.state=='draft' and self.partner_id.po_taxes_id:
			self.taxes_id = self.partner_id.po_taxes_id
		elif self.state=='draft':
			self.taxes_id = False

	@api.model
	def create(self, val):
		res = super(PurchaseOrder,self).create(val)
		for item in res:
			item.change_po_part()
		return res
