# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class power_product(models.Model):
    _name = 'power.product'
    _description = 'power product'
    _order = 'down_id, workorder_id'
    
    def _get_warehouse(self):
        if self._context.get('active_ids',False) and self._context.get('active_model','') =='power.workorder':
            eo_id = self.env['power.workorder'].browser(self._context['active_ids'][0])
            return eo_id.warehouse_config_id.warehouse_id if eo_id.warehouse_config_id else False
        return False

    down_id = fields.Many2one('power.down', 'Тасралтанд', ondelete='cascade', readonly=True)
    workorder_id = fields.Many2one('power.workorder', 'EO', ondelete='cascade', readonly=True)
    portable_id = fields.Many2one('power.portable', 'Экскаваторын зогсолтд', ondelete='cascade', readonly=True)
    product_id = fields.Many2one('product.product', 'Бараа', required=True)
    product_qty = fields.Float('Тоо хэмжээ', default=1)
    cost_unit = fields.Float('Өртөг', compute='_compute_cost', store=True, groups='mw_power.group_power_cost', compute_sudo=True, readonly=True)
    total_cost = fields.Float('Нийт Өртөг', compute='_compute_cost', store=True, groups='mw_power.group_power_cost', compute_sudo=True, readonly=True)
    available_qty = fields.Float('Үлдэгдэл', compute='_compute_available_qty')
    product_uom_id = fields.Many2one('uom.uom', related='product_id.uom_id', string='Хэмжих нэгж', readonly=True)
    stock_move_ids = fields.One2many('stock.move', 'power_product_id', string='Агуулахын Хөдөлгөөн', readonly=True)
    department_id = fields.Many2one('hr.department', string='Хэлтэс', readonly=True, compiute='_compute_department')
    date = fields.Date('Огноо', compute='_compute_date_object_id', store=True, readonly=True)
    state = fields.Selection([('state1','АШИГЛАЖ БАЙГАА'),('state2','БЭЛЭН БАЙДАЛ')], string='Төлөв', required=True)
    object_id = fields.Many2one('power.category', string='ОДОО БАЙГАА БАЙРШИЛ', required=True, compute='_compute_date_object_id', store=True, readonly=True)
    device_id = fields.Many2one('power.selection', string='ОДОО БАЙГАА БАЙРШИЛ Тоног төхөөрөмж', required=True, compute='_compute_date_object_id', store=True, readonly=True)
    # power_device_id = fields.Many2one('power.category', domain="[('main_type','in',['group','categ'])]", string='Тоног төхөөрөмж/Цахилгаан/')
    src_warehouse_id = fields.Many2one('stock.warehouse',string='Default Warehouse', default=_get_warehouse, required=True)
    # power_device_id = fields.Many2one('power.category', domain="[('main_type','in',['group','categ'])]", string='Тоног төхөөрөмж/asset_id = fields.Many2one('power.category', domain="[('main_type','=','asset'),('parent_id','child_of',power_device_id)]", string='Хөрөнгө')


    @api.depends('workorder_id','down_id')
    def _compute_date_object_id(self):
        for item in self:
            object_id = False
            device_id = False
            date = False
            if item.workorder_id:
                object_id = item.workorder_id.power_device_id.id or item.workorder_id.asset_id.id
                date = item.workorder_id.date
                device_id = item.workorder_id.device_id.id
            item.object_id = object_id
            item.date = date
            item.device_id = device_id

    @api.depends('product_id','product_qty')
    def _compute_cost(self):
        for item in self:
            # stock_move_ids.filtered(lambda r: r.)
            # stock
            item.sudo().cost_unit = item.product_id.standard_price
            item.sudo().total_cost = item.product_qty*item.sudo().cost_unit

    @api.depends('down_id','workorder_id')
    def _compute_department(self):
        for item in self:
            dep_id = False
            if item.workorder_id:
                dep_id = item.workorder_id.customer_department_id.hr_department_id.id
            elif item.down_id:
                if item.down_id.call_department_id:
                    dep_id = item.down_id.call_department_id.id
            if not dep_id:
                dep_id = item.create_uid.department_id.id
            item.department_id = dep_id 
            
    @api.depends('product_id')
    def _compute_available_qty(self, location_ids=False):
        for item in self:
            qty = 0
            if item.product_id:
                domain = [('product_id','=',item.product_id.id),('location_id.usage','=','internal')]
                if location_ids:
                    domain.append(('location_id','in',location_ids.ids))
                qty = sum(self.env['stock.quant'].search(domain).mapped('quantity'))
            item.available_qty = qty

    def unlink(self):
        for s in self:
            if s.stock_move_ids.filtered(lambda r: r.state not in ['cancel']):
                raise UserError('Агуулахын хөдөлгийн үүссэн байна')
        return super(power_product, self).unlink()

class power_product_report(models.Model):
    _name = "power.product.report"
    _auto = False
    _description = "power product report"
        
    date = fields.Date('Огноо', readonly=True)
    product_id = fields.Many2one('product.product','Бараа', readonly=True)
    product_uom_id = fields.Many2one('uom.uom','Хэмжих Нэгж', readonly=True)

    price_unit = fields.Float('Нэгж өртөг', readonly=True, groups="mw_power.group_power_cost", group_operator="avg")
    qty_done = fields.Float('Тоо Хэмжээ', readonly=True)
    sum_qty_done = fields.Float('Нийт Өртөг', readonly=True, groups="mw_power.group_power_cost")
    
    workorder_id = fields.Many2one('power.workorder', 'EO', readonly=True)
    device_type = fields.Selection([('power_device','Тоног төхөөрөмж/Цахилгаан/'),('device','Тоног төхөөрөмж')], string='Төрөл', readonly=True)
    power_device_id = fields.Many2one('power.category', readonly=True, string='Тоног төхөөрөмж/Цахилгаан/')
    device_id = fields.Many2one('power.selection', readonly=True, string='Тоног төхөөрөмж')
    asset_id = fields.Many2one('power.category', readonly=True, string='Хөрөнгө')
    level_id = fields.Many2one('power.selection', readonly=True, string='Хүчдлийн түвшин')
    work_type_id = fields.Many2one('power.selection', readonly=True,  string='Ажлын төрөл')

    def _union_all(self):
        return ''

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    sml.id,
                    sml.product_id,
                    (sml.date + interval '8 hour')::date as date,
                    case when sl.usage='internal' then abs(sm.price_unit) else -abs(sm.price_unit) end price_unit,
                    case when sl.usage='internal' then abs(sml.qty_done) else -abs(sml.qty_done) end qty_done,
                    case when sl.usage='internal' then abs(sml.qty_done)*abs(sm.price_unit) else -(abs(sml.qty_done)*abs(sm.price_unit)) end sum_qty_done,
                    sml.product_uom_id,
                    pp.workorder_id,
                    pw.device_type,
                    pw.power_device_id,
                    pw.device_id,
                    pw.asset_id,
                    pw.level_id,
                    pw.work_type_id
                    FROM stock_move_line AS sml
                    LEFT JOIN stock_move AS sm ON (sml.move_id=sm.id)
                    LEFT JOIN stock_picking AS sp ON (sp.id=sm.picking_id)
                    LEFT JOIN power_product AS pp ON (pp.id=sm.power_product_id)
                    LEFT JOIN power_workorder AS pw ON (pw.id=pp.workorder_id)
                    LEFT JOIN stock_location AS sl ON (sl.id=sml.location_id)
                WHERE sm.state='done' and sm.power_product_id is not null
            )
        """ % (self._table)
        )

class power_product_config(models.Model):
    _name = 'power.product.config'
    _description = 'power product config'
    
    product_id = fields.Many2one('product.product', 'Бараа', required=True)
    type = fields.Selection([('cabel','Кабель')])

    @api.constrains('product_id')
    def _validate_tarip(self):
        for item in self:
            if self.env['power.product.config'].search([('id','!=',item.id),('product_id','=',item.product_id.id)]):
                raise UserError(u'Бараа давхардахгүй {0}'.format(item.product_id.display_name))

class product_product(models.Model):
    _inherit = 'product.product'
    
    power_product_config_ids = fields.One2many('power.product.config','product_id', 'Power Product config')
    
