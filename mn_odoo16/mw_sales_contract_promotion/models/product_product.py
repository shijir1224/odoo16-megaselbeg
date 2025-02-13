# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, pycompat

class ProductTempale(models.Model):
	_inherit = "product.template"
	
	brand_id = fields.Many2one('product.brand', 'Brand')
	report_order = fields.Char(string='Report order')

class ProductBrand(models.Model):
	_inherit = "product.brand"
	_description = "product brand"
	
	name = fields.Char('Name')
	analytic_account_id = fields.Many2one('account.analytic.account',  string='Analytic Account', ondelete='set null')


# 	product_count = fields.Integer(
# 		'# Products', compute='_compute_product_count')

# 	def _compute_product_count(self):
# 		read_group_res = self.env['product.template'].read_group([('brand_id', 'in', self.ids)], ['brand_id'], ['brand_id'])
# 		group_data = dict((data['brand_id'][0], data['brand_id_count']) for data in read_group_res)
# 		
# 		for brand in self:
# 			product_count = group_data.get(brand.id, 0)
# 			brand.product_count = product_count	
