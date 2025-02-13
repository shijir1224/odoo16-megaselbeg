# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models



class account_transaction_balance_pivot(models.Model):
    _inherit = "account.transaction.balance.pivot"

    brand_id = fields.Many2one('product.brand',)
    

    def _select(self):
        select_str = super(account_transaction_balance_pivot, self)._select()
        select_str += """
            ,brand_id
        """
        return select_str

    def _select2(self):
        select_str = super(account_transaction_balance_pivot, self)._select2()
        select_str += """
            ,aml.brand_id
        """
        return select_str

    def _select3(self):
        select_str = super(account_transaction_balance_pivot, self)._select3()
        select_str += """
             ,aml.brand_id
        """
        return select_str
           
    # def _from(self):
    #     from_str = super(account_transaction_balance_pivot, self)._from()
    #     from_str +=  """
    #          ,aml.brand_id
    #     """
    #     return from_str
    #
    # def _from2(self):
    #     from_str = super(account_transaction_balance_pivot, self)._from2()
    #     from_str +=  """
    #          ,aml.brand_id
    #     """
    #     return from_str
                    
        
