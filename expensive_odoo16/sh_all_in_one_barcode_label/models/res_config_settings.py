# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    sh_stock_quantity_configuration = fields.Selection([('demand','Demand Quantity'),('done','Done Quantity')],string='Barcode Label Quantity Configuration')
    sh_sale_quantity_configuration = fields.Selection([('qty','Order Quantity'),('delivered','Delivered Quantity'),('invoiced','Invoiced Quantity')],string='Barcode Label Quantity Configuration ')
    sh_purchase_quantity_configuration = fields.Selection([('qty','Order Quantity'),('received','Received Quantity'),('billed','Billed Quantity')],string=' Barcode Label Quantity Configuration ')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sh_stock_quantity_configuration = fields.Selection([('demand','Demand Quantity'),('done','Done Quantity')],string='Barcode Label Quantity Configuration',related='company_id.sh_stock_quantity_configuration',readonly=False)
    sh_sale_quantity_configuration = fields.Selection([('qty','Order Quantity'),('delivered','Delivered Quantity'),('invoiced','Invoiced Quantity')],string='Barcode Label Quantity Configuration ',related='company_id.sh_sale_quantity_configuration',readonly=False)
    sh_purchase_quantity_configuration = fields.Selection([('qty','Order Quantity'),('received','Received Quantity'),('billed','Billed Quantity')],string=' Barcode Label Quantity Configuration ',related='company_id.sh_purchase_quantity_configuration',readonly=False)
