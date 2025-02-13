# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning,UserError
from odoo.tools import float_compare, float_is_zero, float_round
from calendar import monthrange
from odoo.tools import float_compare
from math import copysign

class accountAssetUpdate(models.TransientModel):
    _name = 'account.asset.update'
    _description = 'Account asset update'
    _inherit = 'analytic.mixin' 



    expense_account_id = fields.Many2one('account.account', string='Зардлын данс')
    owner_id = fields.Many2one('res.partner', string='Эзэмшигч', domain=[("employee", "=", True)])
    department_id = fields.Many2one('hr.department', string='Хэлтэс')
    asset_ids = fields.Many2many('account.asset', string='Хөрөнгүүд', default=lambda self: self.env.context.get('active_ids', []))
    location_id = fields.Many2one('account.asset.location', string="Байрлал")
    branch_id = fields.Many2one('res.branch', string='Салбар')
    prorata_date = fields.Date(string="Элэгдэж эхлэх огноо")
    method_number = fields.Integer(string="Нийт элэгдэх хугацаа")
    asset_type_id = fields.Many2one('account.asset.type', string="Хөрөнгийн төрөл")
    def change_button(self):
        for i in self.asset_ids:
            if self.expense_account_id:
                i.account_depreciation_expense_id = self.expense_account_id.id
            if self.owner_id:
                i.owner_id = self.owner_id.id
            if self.department_id:
                i.owner_department_id = self.department_id.id
            if self.analytic_distribution:
                i.analytic_distribution = self.analytic_distribution
            if self.location_id:
                i.location_id = self.location_id.id
            if self.branch_id:
                i.branch_id = self.branch_id.id
            if self.prorata_date:
                i.prorata_date = self.prorata_date
            if self.method_number:
                i.method_number = self.method_number
            if self.asset_type_id:
                i.asset_type_id = self.asset_type_id.id
    def done_button(self):
        for i in self.asset_ids:
            i.validate()
            
