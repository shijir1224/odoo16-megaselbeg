# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProductTemplate(models.Model):
	_inherit = 'product.product'
	
	is_consum = fields.Boolean('Is consumable?',default=False, tracking=True)

class ProductTemplate(models.Model):
	_inherit = 'product.template'
	
	is_consum = fields.Boolean('Is consumable?',default=False, tracking=True)
	is_depreciate = fields.Boolean('Depreciation',default=False, tracking=True)
	# register_on_card = fields.Boolean('Register On Card',default=False)