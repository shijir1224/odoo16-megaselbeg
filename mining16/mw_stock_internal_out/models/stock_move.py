from odoo.models import Model
from odoo import fields
from odoo.exceptions import UserError, ValidationError

class StockMove(Model):
    _inherit = 'stock.move'


    interout_line_id = fields.Many2one('stock.product.interout.line', string='Шаардах мөр', readonly=True)

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
                                       credit_account_id, svl_id, description):
        
        self.ensure_one()
        # 
        rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value,
                                                                     debit_account_id, credit_account_id,svl_id, description)
        if self.picking_id.interout_id and self.interout_line_id:
            account_id = False
            analytic_distribution = False
            partner_id =False
            if self.picking_id.interout_id:
                if self.interout_line_id and self.interout_line_id.account_id :
                    account_id = self.interout_line_id.account_id.id
                elif self.picking_id.interout_id.account_id:
                    account_id = self.picking_id.interout_id.account_id.id
                if self.interout_line_id and self.interout_line_id.analytic_distribution:
                    analytic_distribution = self.interout_line_id.analytic_distribution
                if self.interout_line_id and self.interout_line_id.res_partner_id:
                    partner_id = self.interout_line_id.res_partner_id.id
                    rslt['debit_line_vals']['partner_id'] = partner_id
                    rslt['credit_line_vals']['partner_id'] = partner_id
            if self.picking_id.interout_id.department_id and self.picking_id.interout_id.department_id.branch_id:
                rslt['debit_line_vals']['branch_id'] = self.picking_id.interout_id.department_id.branch_id.id
                rslt['credit_line_vals']['branch_id'] = self.picking_id.interout_id.department_id.branch_id.id
            # print ('analytic_distribution3 ',analytic_distribution)
            if analytic_distribution:
                rslt['debit_line_vals']['analytic_distribution'] = analytic_distribution
                rslt['credit_line_vals']['analytic_distribution'] = analytic_distribution
            if not account_id:
                raise UserError(u'данс сонгүүгүй байна {}'.format(self.picking_id.interout_id.product_id.name))
            if account_id:
                if self._is_out():
                    rslt['debit_line_vals']['account_id'] = account_id
                    # rslt['debit_line_vals']['analytic_distribution'] = analytic_distribution
                else:
                    rslt['credit_line_vals']['account_id'] = account_id
                    # rslt['credit_line_vals']['analytic_distribution'] = analytic_distribution
        return rslt

class StockPicking(Model):
    _inherit = 'stock.picking'


    stock_expense_accountant = fields.Many2one('res.users', string="Шаардах батласан нягтлан")
