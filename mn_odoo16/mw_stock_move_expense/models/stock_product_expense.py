from odoo import api, models, fields


class StockProductOtherExpense(models.Model):
    _inherit = 'stock.product.other.expense'

    @api.onchange('account_analytic_id')
    def onchange_parent_account_analytic_id(self):
        for obj in self:
            obj.product_expense_line.onchange_parent_account_analytic_id()


class StockProductOtherExpenseLine(models.Model):
    _inherit = 'stock.product.other.expense.line'

    allocate_expense = fields.Boolean(string='Зардал хуваах')
    allocation_id = fields.Many2one('account.allocation.expense.conf', 'Зардал хуваах тохиргоо')
    account_analytic_id = fields.Many2one('account.analytic.account', u'Аналитик данс', copy=False, tracking=True)
    brand_id = fields.Many2one('product.brand', 'Брэнд')

    @api.depends('parent_id.account_analytic_id')
    def onchange_parent_account_analytic_id(self):
        for obj in self:
            obj.account_analytic_id = obj.parent_id.account_analytic_id