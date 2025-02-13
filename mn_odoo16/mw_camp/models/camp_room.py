# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api
from odoo.exceptions import UserError, ValidationError
import datetime

    
class CampRoom(models.Model):
    _name = 'camp.room'
    _description='Camp Room'
    
    name = fields.Char(string='Нэр')
    price_unit = fields.Float(string='Өрөөний Дүн')
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    block_id = fields.Many2one('camp.block' , string='Block', store=True , index=True)
    
class CampBlock(models.Model):
    _name = 'camp.block'
    _description='Camp Room'
    
    name = fields.Char(string='name')
    
class CampDepartment(models.Model):
    _name = 'camp.department'
    _description='Camp Department'
    
    name = fields.Char(string='name')
    
class ResPartner(models.Model):
    _inherit ='res.partner'
    
    camp_department_id = fields.Many2one('camp.department' , string='Camp Department' , store=True , index=True)
    gender = fields.Selection([('female','Эмэгтэй'),('male','Эрэгтэй')] , string='Хүйс' , store=True)
    

class CampRoomtype(models.Model):
    _name = 'camp.room.type'
    _description='Camp Room Type'
    
    name = fields.Char(string='Нэр')
    price_unit = fields.Float(string='Өрөөний Дүн')
    revenue_account_id = fields.Many2one('account.account' , string='Орлогын данс', store=True,index=True)