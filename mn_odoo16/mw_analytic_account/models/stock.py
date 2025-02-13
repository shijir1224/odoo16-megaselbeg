# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description):
        """ Overridden from stock_account 
        """
        self.ensure_one()

        rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description)
        if self.picking_id.other_expense_id:
            analytic=False
            account_id =False
            analytic_distribution=False
            #Буцаалт бол шаардах данс авахгүй
            is_return=True
            in_ret=self._is_returned(valued_type='out')
            if self._context.get('is_returned') and not in_ret:
                # print ('self._context ',self._context)
                is_return = False            
            if self.picking_id.other_expense_id and is_return:
                if self.picking_id.other_expense_id.account_analytic_id:
                    analytic = self.picking_id.other_expense_id.account_analytic_id.id
                if self.expense_line_id and self.expense_line_id.analytic_distribution:
                    analytic_distribution = self.expense_line_id.analytic_distribution
                elif self.picking_id.other_expense_id.analytic_distribution:
                    analytic_distribution=self.picking_id.other_expense_id.analytic_distribution
                elif self.picking_id.other_expense_id.department_id and self.picking_id.other_expense_id.department_id.analytic_account_id:
                    analytic = self.picking_id.other_expense_id.department_id.analytic_account_id.id
                if self.expense_line_id and self.expense_line_id.account_id :
                    account_id = self.expense_line_id.account_id.id
                elif self.picking_id.other_expense_id.account_id:
                    account_id=self.picking_id.other_expense_id.account_id.id
                # elif self.picking_id.other_expense_id.transaction_value_id and self.picking_id.other_expense_id.transaction_value_id.account_id:
                #     if self.expense_line_id and self.expense_line_id.account_id :
                #         account_id = self.expense_line_id.account_id.id
                #     else:
                #         account_id = self.picking_id.other_expense_id.transaction_value_id.account_id.id
#             elif self.picking_id.other_expense_id.emp_department_id and self.picking_id.other_expense_id.emp_department_id.account_analytic_id:
#                 analytic = self.picking_id.other_expense_id.emp_department_id.account_analytic_id
#             rslt['credit_line_vals']['analytic_account_id'] = analytic
            # print ('analytic_distribution11 ',analytic_distribution)
            # if analytic:
            #     rslt['debit_line_vals']['analytic_account_id'] = analytic
            #     rslt['credit_line_vals']['analytic_account_id'] = analytic
            if analytic_distribution:
                rslt['debit_line_vals']['analytic_distribution'] = analytic_distribution
                rslt['credit_line_vals']['analytic_distribution'] = analytic_distribution
            if account_id:
                rslt['debit_line_vals']['account_id'] = account_id
        return rslt
