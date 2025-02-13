# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools

# Гүйлгээний утга
class hr_employee(models.Model):
    _inherit = 'hr.employee'
    
    expense_line_ids = fields.One2many('stock.product.other.expense.line', 'employee_id', string='Зардалууд', groups='mw_stock_moves.group_stock_other_expence_user')
    total_expense = fields.Float('', compute='all_expense_cost', groups='mw_stock_moves.group_stock_other_expence_user')

    def get_all_cost(self, expense_line_ids):
        all_cost = sum(self.env['product.expense.report'].sudo().search(['|',('for_employee_id','=',self.id),('employee_id','=',self.id)]).mapped('amount_price_unit'))
        
        return all_cost

    @api.depends('expense_line_ids')
    def all_expense_cost(self):
        for item in self:
            item.total_expense = self.get_all_cost(item.expense_line_ids)
    
    def see_stock_move(self):
        action = self.env.ref('mw_stock_moves.product_expense_report_action').read()[0]
        action['domain'] = ['|',('for_employee_id','=', self.id),('employee_id','=',self.id)]
        action['context'] = {}
        return action