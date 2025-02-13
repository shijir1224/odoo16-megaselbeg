# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models

class account_transaction_balance_view(models.Model):
    _inherit = "account.transaction.balance.view"
    _description = "Product both income expense report"

    technic_id = fields.Many2one('technic.equipment', u'Техник', readonly=True)
    # component_id = fields.Many2one('technic.component.part', u'Компонэнт', readonly=True)
    # analytic_account_id = fields.Many2one('account.analytic.account', u'Шинжилгээний данс', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'account_transaction_balance_view')
        self.env.cr.execute("""CREATE or REPLACE VIEW account_transaction_balance_view as 
                select min(l.id) as id, 
                sum(debit) as debit,
                sum(credit) as credit,
                sum(debit)-sum(credit) as net_move,
                l.account_id,
                l.date,
                l.move_id,
                l.partner_id,
                l.account_id as j,
                j.code_group_id,
                l.journal_id,
                l.branch_id,
                m.state,
                m.invoice_origin as origin,
                l.technic_id                
                from account_move_line l left join account_move m on l.move_id=m.id left join account_account j on l.account_id = j.id
                group by l.account_id,l.date,l.move_id,l.partner_id,l.journal_id,l.branch_id,m.state,m.invoice_origin,j.code_group_id, l.technic_id           
            """)
        



class AccountTransactionBalancePivot(models.Model):
    _inherit = "account.transaction.balance.pivot"
    
    technic_id = fields.Many2one('technic.equipment', u'Техник', readonly=True)
    

    def _select(self):
        select_str = super(AccountTransactionBalancePivot, self)._select()
        select_str += """
            ,technic_id
        """
        return select_str

    def _select2(self):
        select_str = super(AccountTransactionBalancePivot, self)._select2()
        select_str += """
            ,aml.technic_id
        """
        return select_str

    def _select3(self):
        select_str = super(AccountTransactionBalancePivot, self)._select3()
        select_str += """
                ,aml.technic_id
        """
        return select_str
