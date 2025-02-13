# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

class stock_price_unit_limit(models.Model):
    _name = 'stock.price.unit.limit'
    _description = 'stock price unit limit'
    _order = 'create_date desc'

    limit_price_unit_min = fields.Float('Өртөгийн Хязгаар Доод')
    limit_price_unit_max = fields.Float('Өртөгийн Хязгаар Дээд')
    product_id = fields.Many2one('product.product', 'Бараа', copy=False)
    standard_price_mw = fields.Float(related='product_id.standard_price', readonly=True)
    list_price_mw = fields.Float(related='product_id.list_price', readonly=True)

    def import_no_price(self):
        p_ids = self.env['product.product'].search([
            ('cost_limit_ids','=',False),
            ('cost_method','=','average'),
            ('type','=','product'),
            ('list_price','<=',1)])
        for item in p_ids:
            dood = 0
            deed = 0
            if item.standard_price>0:
                dood = item.standard_price/2.5
                deed = item.standard_price*2.5
            self.create({
                'product_id': item.id,
                'limit_price_unit_min': dood,
                'limit_price_unit_max': deed,
                
            })
    _sql_constraints = [
        ('product_id_unique', 'UNIQUE(product_id)', 'Baraa davhardahgui')
    ]
class product_product(models.Model):
    _inherit = 'product.product'

    cost_limit_ids = fields.One2many('stock.price.unit.limit', 'product_id', string='Лимит')

    @api.constrains('standard_price')
    def check_standard_price_mw(self):
        for item in self:
            if item.cost_method in ('average'):
                limit_id = self.env['stock.price.unit.limit'].sudo().search([('product_id','=',item.id)], limit=1)
                deed = 0
                dood = 0
                if limit_id:
                    dood = limit_id.limit_price_unit_min
                    deed = limit_id.limit_price_unit_max
                # elif item.list_price>1:
                #     dood = item.list_price/10
                #     deed = item.list_price
                
                if deed>0 and dood>0 and (item.standard_price<dood or item.standard_price>deed):
                    desc = ''
                    if self.user_has_groups('mw_stock_price_unit.group_stock_view_price_unit_conf'):
                        desc = ' Deed %s Dood %s  New cost %s '%(deed,dood,item.standard_price)
                    raise UserError(u'Өртөг буруу болоод байна Систем Админд Ханадана уу %s  %s'%(item.display_name,desc))
                