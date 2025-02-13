# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

class DoneResUsers(models.Model):
    _inherit = 'res.users'
    
    # Columns
    done_warehouse_ids = fields.Many2many('stock.warehouse','done_user_warehouses_rel','user_id','warehouse_id',
        string='Warehouse',
    )

class DoneStockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    # Columns
    done_user_ids = fields.Many2many('res.users','done_user_warehouses_rel','warehouse_id','user_id',
        string='Done users',)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_check_algasah(self):
        return False

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def get_check_algasah(self):
        if self.picking_id:
            return self.picking_id.get_check_algasah()
        return False
    
    def _action_done(self):
        if not self.get_check_algasah():
            for item in self:
                location_id = False
                if item.location_id.usage=='internal' and item.location_dest_id.usage!='internal':
                    location_id = item.location_id
                elif item.location_id.usage!='internal' and item.location_dest_id.usage=='internal':
                    location_id = item.location_dest_id
                elif item.location_id.usage=='internal' and item.location_dest_id.usage=='internal':
                    location_id = item.location_dest_id
                if location_id:
                    wh_id = location_id.set_warehouse_id
                    if self.env.user.id not in wh_id.done_user_ids.ids:
                        join_name = ', '.join(wh_id.done_user_ids.mapped('name'))
                        raise UserError(u'Та "%s" Агуулахын батлах хэрэглэгч биш байна Админд хандана уу!!! \n Батлах хэрэглэгчид \n%s %s:\t%s'%(wh_id.name,join_name, wh_id.name, self.env.user.name))
        return super(StockMoveLine, self)._action_done()
