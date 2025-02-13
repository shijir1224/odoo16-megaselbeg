from odoo.models import Model, TransientModel
from odoo import fields

class ResCompany(Model):
	_inherit = 'res.company'
	purchase_down_payment_product_id = fields.Many2one('product.product', string='Down payment product')

class ResConfig(TransientModel):
	_inherit = 'res.config.settings'

	purchase_down_payment_product_id = fields.Many2one(related='company_id.purchase_down_payment_product_id',
													   readonly=False, string='Down payment product')
