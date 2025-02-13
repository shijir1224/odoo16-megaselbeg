# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class CampOrderReport(models.Model):
    _name = "camp.order.report"
    _description = "camp.order.report"
    _auto = False
    _order = 'name'

    
    name = fields.Char(string='Дугаар' , readonly=True)
    date = fields.Date(string='Огноо' , readonly=True)
    partner_id = fields.Many2one('res.partner' , string='Харилцагч' , index=True, readonly=True)
    is_payment = fields.Boolean(string='Төлбөртэй эсэх',  readonly=True)
    payment_type = fields.Selection([('default','Үндсэн'),('nondefault','Гараар')] , string='Төлбөрийн төрөл' , readonly=True)
    company_id = fields.Many2one('res.company' , string='Компани' , readonly=True)
    order_line = fields.One2many('camp.order.line','parent_id', string='Order line' ,)
    partners_id = fields.Many2one('res.partner' , readonly=1)
    
    room_id = fields.Many2one('camp.room' , string='Өрөө'  , index=True)
    room_type_id = fields.Many2one('camp.room.type' , string='Өрөөний төрөл', index=True)
    block_id = fields.Many2one('camp.block' , string='Блок'  , index=True) 
    line_date = fields.Date(string='Огноо' , readonly=True)
    partner_id = fields.Many2one('res.partner' , string='Partner'  , index=True)
    department_id = fields.Many2one('camp.department' , index=True)
    invoice_id = fields.Many2one('account.move' , string='Нэхэмжлэл'  , index=True)
    amount = fields.Float(string='Нийт нэгж үнэ',readonly=True)
    
    line_payment_type = fields.Selection([('default','Үндсэн'),('nondefault','Гараар')] , string='Төлбөрийн төрөл' , readonly=True )
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT
                co.id as id,
                co.name as name,
                co.date as date,
                co.partner_id as partner_id,
                co.is_payment as is_payment,
                co.payment_type as payment_type,
                co.company_id as company_id,
				co.invoice_id as invoice_id,
                col.partner_id as partners_id,
                col.room_id as room_id,
                col.room_type_id as room_type_id,
                col.block_id as block_id,
                col.date as line_date,
                col.amount as amount,
                col.payment_type as line_payment_type
            FROM camp_order_line as col
            LEFT JOIN camp_order as co on (co.id = col.parent_id)
            LEFT JOIN account_move as am on (co.invoice_id = am.id)
            LEFT JOIN camp_room as cr on (col.room_id = cr.id)
			where state_type='done'
        )""" % self._table)
