# -*- coding: utf-8 -*-

import time
import math

from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round
from odoo.tools import float_is_zero, float_compare
import datetime

# Шинжилгээний дансны тохируулга
# class AccountAnalyticAccount(models.Model):
#     _inherit = "account.analytic.account"
# 
#     warehouse_ids = fields.Many2many('stock.warehouse', string="Warehouse")
#     product_ids = fields.Many2many('product.template', string='Product templates')
# 
#     
#     def write(self, vals):
#         res = super(AccountAnalyticAccount, self).write(vals)
#         objs = self.env['account.analytic.account'].search([
#             ('warehouse_ids','in',self.warehouse_ids.ids),
#             ('product_ids','in',self.product_ids.ids)])
#         if len(objs) > 1:
#             raise UserError(('Агуулах, барааны мэдээлэл давхардсан байна!'))
#         return res



class AccountAccount(models.Model):
    _inherit = "account.account"
    _description = "Account "

    check_balance = fields.Boolean(string='Check balance?', copy=False, tracking=True)
    check_analytic = fields.Boolean(string='Заавал шинжилгээний данс сонгох?', copy=False, tracking=True)
    create_analytic = fields.Boolean(string='Шинжилгээний бичилт үүсгэх?', copy=False, tracking=True ,default=False)
    
class HrDepartment(models.Model):
    _inherit = "hr.department"
 
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic account", copy=False)


class ResUsers(models.Model):
    _inherit = 'res.users'
    _description = 'Res users'
    

    @api.depends('employee_ids')
    @api.depends_context('force_company')
    def _compute_company_employee(self):
        for user in self:
            user.employee_id = self.env['hr.employee'].search([('id', 'in', user.employee_ids.ids), ('company_id', '=', self.env.company.id)], limit=1)


    def _search_company_employee(self, operator, value):
        employees = self.env['hr.employee'].search([
            ('name', operator, value),
            '|',
            ('company_id', '=', self.env.company.id),
            ('company_id', '=', False)
        ], order='company_id ASC')
        return [('id', 'in', employees.mapped('user_id').ids)]    


    @api.depends('employee_id','department_id','employee_id.department_id','employee_id.department_id.analytic_account_id','department_id.analytic_account_id')
    def _compute_analytic_account(self):
        for user in self:
            analytic_account_id=False
            if user.employee_id:
                if user.employee_id.department_id and user.employee_id.department_id.analytic_account_id:
                    analytic_account_id=  user.employee_id.department_id.analytic_account_id.id
            elif user.department_id:
                if user.department_id and user.department_id.analytic_account_id:
                    analytic_account_id=  user.department_id.analytic_account_id.id
            user.analytic_account_id = analytic_account_id


    # Columns
    department_id = fields.Many2one(related='employee_id.department_id', readonly=False, related_sudo=False,store=True)
#     analytic_account_id = fields.Many2one(related='department_id.analytic_account_id', readonly=False, related_sudo=False,store=True)
    employee_id = fields.Many2one('hr.employee', string="Company employee",
        compute='_compute_company_employee', search='_search_company_employee', store=True)

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic account",
        compute='_compute_analytic_account', store=True)
