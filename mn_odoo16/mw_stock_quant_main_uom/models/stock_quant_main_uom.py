# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules
from odoo.osv import expression
import operator as py_operator

class uom_uom(models.Model):
    _inherit = "uom.uom"

    main_uom_id = fields.Many2one('uom.uom', string='Үндсэн Хэмжих Нэгж', compute='_compute_main_uom_id', store=True)
    
    @api.depends('category_id')
    def _compute_main_uom_id(self):
        Uom = self.env['uom.uom']
        for item in self:
            main_uom_id = Uom.search([('category_id','=',item.category_id.id),('uom_type','=','reference')], limit=1)
            item.main_uom_id = main_uom_id.id if main_uom_id else False

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    quantity_main_uom = fields.Float(
        'Үлдэгдэл Үндсэн Хэмжих Нэгжээр', compute='_compute_inventory_quantity_main_qty', groups='mw_stock_quant_main_uom.group_stock_by_quant_main_uom')
    
    @api.depends('quantity')
    def _compute_inventory_quantity_main_qty(self):
        if not self._is_inventory_mode():
            self.quantity_main_uom = 0
            return
        for quant in self:
            quant.quantity_main_uom = self.get_main_qty(quant.product_id, quant.quantity)
    def get_main_qty(self, product, qty):
        Uom = self.env['uom.uom']
        main_uom_id = False
        if product.uom_id.uom_type!='reference':
            main_uom_id = Uom.search([('category_id','=',product.uom_id.category_id.id),('uom_type','=','reference')], limit=1)
        if main_uom_id:
            qty = product.uom_id._compute_quantity(
                    qty,
                    main_uom_id,
                    round=False
                )
        return qty
        
class ProductProduct(models.Model):
    _inherit = 'product.product'

    qty_available_quant_main_uom = fields.Float(
        'Үлдэгдэл Үндсэн Хэмжих Нэгжээр', compute='_compute_quantities_quant_main_uom', 
        digits='Product Unit of Measure', 
        help="Үлдэгдэл Үндсэн Хэмжих нэгжээр")

    @api.depends('stock_quant_ids')
    def _compute_quantities_quant_main_uom(self):
        products = self.filtered(lambda p: p.type != 'service')
        for product in products:
            qty = sum(product.stock_quant_ids.filtered(lambda r: r.location_id.usage=='internal').mapped('quantity'))
            product.qty_available_quant_main_uom = self.env['stock.quant'].get_main_qty(product, qty)
        # Services need to be set with 0.0 for all quantities
        services = self - products
        services.qty_available_quant_main_uom = 0.0
     
class ProductTemplace(models.Model):
    _inherit = 'product.template'

    qty_available_quant_main_uom = fields.Float(
        'Үлдэгдэл Үндсэн Хэмжих Нэгжээр', compute='_compute_quantities_quant_main_uom',
        compute_sudo=False, digits='Product Unit of Measure')
    
    @api.depends_context('company_owned', 'force_company')
    def _compute_quantities_quant_main_uom(self):
        for template in self:
            qty_available_quant_main_uom = 0
            for p in template.product_variant_ids:
                qty_available_quant_main_uom += p.qty_available_quant_main_uom
                
            template.qty_available_quant_main_uom = qty_available_quant_main_uom

class StockQuantReport(models.Model):
    _inherit = "stock.quant.report"
    
    quantity_main_uom = fields.Float(string='Үндэгдэл үндсэн нэгжээр', groups='mw_stock_quant_main_uom.group_stock_by_quant_main_uom')

    def _select(self):
        select_str = super(StockQuantReport, self)._select()
        select_str += """
            ,sq.quantity / uom_quant.factor * uom_main.factor as quantity_main_uom
        """
        return select_str

    def _from(self):
        select_str = super(StockQuantReport, self)._from()
        select_str += """
            LEFT JOIN uom_uom uom_quant ON (uom_quant.id=pt.uom_id)
            LEFT JOIN uom_uom uom_main ON (uom_main.id=uom_quant.main_uom_id)
        """
        return select_str


