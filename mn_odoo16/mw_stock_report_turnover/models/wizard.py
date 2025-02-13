# -*- coding: utf-8 -*-

import time
from odoo import _, tools
from datetime import datetime, timedelta
from odoo import api, fields, models
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
import logging
_logger = logging.getLogger(__name__)

class stock_report_turnover_wizard(models.TransientModel):
    _name = "stock.report.turnover.wizard"  
    _description = "stock report turnover wizard"
    
    date_end = fields.Date(required=True, string=u'Огноо',default=fields.Date.context_today)
    product_tmpl_ids = fields.Many2many('product.template', string=u'Бараа/Template', help=u"Тайланд гарах бараануудыг сонгоно")
    warehouse_id = fields.Many2many('stock.warehouse', string=u'Агуулах',required=True, )
    location_ids = fields.Many2many('stock.location', string=u'Байрлал',)
    product_ids = fields.Many2many('product.product', string=u'Бараанууд', help=u"Тайланд гарах барааг сонгоно")
    categ_ids = fields.Many2many('product.category', string=u'Барааны ангилал', help=u"Тухайн сонгосон ангилал дахь бараануудыг тайланд гаргах")
    included_internal = fields.Boolean(string=u'Дотоод хөдөлгөөн оруулахгүй', default=False)
    move_type = fields.Selection([
            ('balance', u'Үлдэгдэл'),
        ], default='balance', string=u'Төрөл')
    move_state = fields.Selection([
            ('cancel', u'Бүгд'),
            ('assigned_done', u'Бэлэн болон Дууссан'), 
            ('confirmed', u'Бэлэн болохыг хүлээж байгаа'), 
            ('assigned', u'Бэлэн'),
            ('done', u'Дууссан'),
        ], default='done', string=u'Төлөв',)

    tz = fields.Integer(u'Цагийн бүсийн зөрүү', required=True, default=8)
    import_wh = fields.Boolean(u'Бүх агуулах ОРУУЛАХ/АРИЛГАХ', default=False)
    see_value = fields.Boolean(string=u'Өртөгтэй Харах', default=False, groups="mw_stock_product_report.group_stock_see_price_unit")
    no_category_total = fields.Boolean(string=u'Ангилалгүй гаргах', default=False)
    with_attribute = fields.Boolean(string=u'Аттрибуттай', default=False)
    
    @api.onchange('import_wh')
    def onchange_all_wh_import(self):
        if self.import_wh:
            self.warehouse_id = self.env['stock.warehouse'].search([])
        else:
            self.warehouse_id = False
    
    def get_tuple(self, obj, categ_is=False):
        if categ_is:
            obj = self.env['product.category'].search([('id','child_of',obj)]).ids
            
        if len(obj) > 1:
            return str(tuple(obj))
        else:
            return " ("+str(obj[0])+") "
    
    def get_domain(self, domain, donwload=False):
        domain_val = ''
        if self.move_type == 'balance':
            if self.product_ids:
                domain.append(('product_id','in',self.product_ids.ids))
            if self.product_tmpl_ids:
                domain.append(('product_tmpl_id','in',self.product_tmpl_ids.ids))
            if self.categ_ids:
                domain.append(('categ_id','child_of',self.categ_ids.ids))
            if self.move_state =='cancel':
                domain.append(('state','!=',self.move_state))
            elif self.move_state == 'assigned_done':
                domain.append(('state','in',['done','assigned']))
            else:
                domain.append(('state','=',self.move_state))
            if self.location_ids:
                domain.append(('location_id','in',self.location_ids.ids))
            elif self.warehouse_id:
                domain.append(('warehouse_id','in',self.warehouse_id.ids))
            domain.append(('date_expected','<=',self.date_end))
            if self.included_internal:
                domain.append(('transfer_type','!=','internal'))
        return domain

    def open_analyze_view(self):
        domain = []
        if self.move_type=='balance':
            action = self.env.ref('mw_stock_report_turnover.action_stock_report_turnover_report')
        vals = action.read()[0]
        vals['domain'] = self.get_domain(domain)
        return vals

    
    
