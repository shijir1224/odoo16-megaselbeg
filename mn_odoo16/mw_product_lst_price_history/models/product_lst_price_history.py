# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules, _
import odoo.addons.decimal_precision as dp

class ProductListPriceChangeLog(models.Model):
    _name = "product.list.price.change.log"
    _description = "List price change log"
    _rec_name = "product_id"

    product_id = fields.Many2one('product.product','Бараа', ondelete='cascade')
    product_tmpl_id = fields.Many2one('product.template', related='product_id.product_tmpl_id')
    list_price = fields.Float(
        'List price',
        digits=dp.get_precision('Product Price'),
        groups="base.group_user",
        )
    company_id = fields.Many2one('res.company', 'Company')

    _order = "create_date desc"

class ProductTemplate(models.Model):
    _inherit = "product.template"

    lst_price_change_log_ids = fields.One2many('product.list.price.change.log', 'product_tmpl_id',
                                               string='List price change log')

    def write(self, values):
        res = super(ProductTemplate, self).write(values)
        print (values)
        if 'list_price' in values:
            products = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
            if products:
                for prod in products:
                    prod.create_lst_price_change_log()
        return res

class ProductProduct(models.Model):
    _inherit = "product.product"

    lst_price_change_log_ids = fields.One2many('product.list.price.change.log', 'product_id', string='List price change log')

    def write(self, values):
        res = super(ProductProduct, self).write(values)
        if 'lst_price' in values:
            self.create_lst_price_change_log()
        return res

    @api.depends('lst_price')
    def create_lst_price_change_log(self):
        log_obj = self.env['product.list.price.change.log']
        for item in self:
            if len(item.lst_price_change_log_ids)>0:
                if abs(abs(item.lst_price)-abs(item.lst_price_change_log_ids[0].list_price))>0.0001:
                    log_obj.create({
                        'list_price': item.lst_price,
                        'product_id': item.id,
                        'company_id': self.env.user.company_id.id,
                        })
            else:
                log_obj.create({
                    'list_price': item.lst_price,
                    'product_id': item.id,
                    'company_id': self.env.user.company_id.id,
                    })
