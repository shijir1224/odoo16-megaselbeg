# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools

class oil_fuel_norm(models.Model):
    _name = 'oil.fuel.norm'
    _description = 'Oil fuel norm'
    _order = 'create_date desc'

    technic_setting_id = fields.Many2one('technic.equipment.setting', string='Техникийн тохиргоо', ondelete='cascade')
    is_danger = fields.Boolean(string='Хэтэрч болохгүй', default=False)
    product_id = fields.Many2one('product.product', string='Бараа')
    categ_id = fields.Many2one('product.category', string='Барааны Ангилал')
    qty = fields.Float(string='Тоо хэмжээ')
    

class technic_equipment_setting(models.Model):
    _inherit = 'technic.equipment.setting'
    
    oil_fuel_norm_ids = fields.One2many('oil.fuel.norm', 'technic_setting_id', 'Тосны норм')
    fuel_norm = fields.Float(string='Түлшний норм', default=0)

class oil_report_product_categ(models.Model):
    _name = 'oil.report.product.categ'
    _description = 'Oil report product categ'
    
    product_categ_ids = fields.Many2many('product.category', 'oil_report_product_category_rel', 'oil_report_id', 'categ_id', string='Тосны тайланд орох Барааны Ангилал')
 