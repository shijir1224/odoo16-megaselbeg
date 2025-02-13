# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    technic_id = fields.Many2one('technic.equipment', 'Техник')
    component_id = fields.Many2one('technic.component.part', string=u'Component', )

    def _prepare_analytic_distribution_line(self, distribution, account_id, distribution_on_each_plan):
        """ technic_id
        """
        self.ensure_one()
        res = super(AccountMoveLine, self)._prepare_analytic_distribution_line(distribution=distribution, account_id=account_id, distribution_on_each_plan=distribution_on_each_plan)
        res.update({
            'technic_id':self.technic_id and self.technic_id.id or False
        })
        return res


    @api.depends('display_type', 'company_id','move_id.stock_warehouse_id')
    def _compute_account_id(self):
        super()._compute_account_id()
        for move in self.move_id:
            if move.stock_warehouse_id:
                if move.stock_warehouse_id.is_bbo and move.stock_warehouse_id.bo_account_id:
                    product_lines = self.filtered(lambda line: line.product_id and line.product_id.detailed_type=='product' and line.display_type == 'product' and line.move_id.is_invoice(True))
                    for line in product_lines:
                        if line.move_id.is_sale_document(include_receipts=True):
                            line.account_id = move.stock_warehouse_id.bo_account_id


class AccountMove(models.Model):
    _inherit = "account.move"

    stock_warehouse_id = fields.Many2one('stock.warehouse', string='Агуулах')
    
    def action_post(self):
        #inherit 
        for move in self:
            for line in move.line_ids:
                if line.statement_line_id and line.statement_line_id.technic_id and not line.technic_id:
                    line.technic_id= line.statement_line_id.technic_id.id
                _logger.info('line.analytic_distribution %s'%(line.analytic_distribution))
        res = super(AccountMove, self).action_post()
        return res
    
    
class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"
    
    technic_id = fields.Many2one('technic.equipment', 'Техник')
    component_id = fields.Many2one('technic.component.part', string=u'Component', )
    branch_id = fields.Many2one('res.branch', related='move_line_id.branch_id', string=u'Branch', store=True)


# class HrDepartment(models.Model):
#     _inherit = "hr.department"
# 
#     analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic account", copy=False)




class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    technic_id = fields.Many2one('technic.equipment', 'Техник')

    @api.model
    def _prepare_move_line_default_vals(self, counterpart_account_id=None):
        res = super(AccountBankStatementLine, self)._prepare_move_line_default_vals(counterpart_account_id)
        if self.technic_id:# and res[1]['account_id'] != self.account_id.id:
            res[1]['technic_id'] = self.technic_id.id
            res[0]['technic_id'] = self.technic_id.id
            
        return res
    

    def button_validate_line(self):
        ctx = dict(self._context, force_price_include=False)
        for st_line in self:
            if st_line.technic_id:
                lines=st_line.move_id.line_ids.filtered(lambda o: not o.technic_id)
                lines.write({'technic_id': st_line.technic_id.id})

        return super(AccountBankStatementLine, self).button_validate_line()
                    
    