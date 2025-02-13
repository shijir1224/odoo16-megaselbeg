# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.account.models.account_move import PAYMENT_STATE_SELECTION
from odoo import tools
from functools import lru_cache


class MWAccountReport(models.Model):
    _name = "mw.account.report"
    _description = "MW account reports"
    _rec_name = 'move_id'
    _auto = False
    _order = 'date desc'

    # ==== Invoice fields ====
    move_id = fields.Many2one('account.move', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Open'),
        ('cancel', 'Cancelled')
        ], string='Invoice Status', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    account_id = fields.Many2one('account.account', string='Account', readonly=True)
    debit = fields.Float(string='Debit', readonly=True)
    credit = fields.Float(string='Credit', readonly=True)
    balance = fields.Float(string='Balance', readonly=True)
    amount_currency = fields.Float(string='Currency', readonly=True)
    
    account_type = fields.Char(string='Type', readonly=True)
    code = fields.Char(string='code', readonly=True)
    entry = fields.Char(string='entry', readonly=True)
    journal = fields.Char(string='journal', readonly=True)
    partner_name = fields.Char(string='partner_name', readonly=True)
    vat = fields.Char(string='vat', readonly=True)
    ref = fields.Char(string='ref', readonly=True)
    ref_label = fields.Char(string='ref_label', readonly=True)
    account_name = fields.Char(string='account_name', readonly=True)
    reconciled = fields.Boolean(string='reconciled', readonly=True)
    curr_name = fields.Char(string='Currency name', readonly=True)
    
    # @property
    # def _table_query(self):
    #     return '%s %s %s' % (self._select(), self._from(), self._where())


    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'mw_account_report')
        self.env.cr.execute("""CREATE or REPLACE VIEW mw_account_report as ( %s %s %s
                ) 
            """ % (self._select(), self._from(), self._where()
        ))
        
        

    @api.model
    def _select(self):
        return '''
            select aml.id,
                m.id as move_id,
                aml.debit,
                aml.credit,
                aml.balance,
                a.code,
                a.name as account_name,
                aml.date,
                aml.amount_currency,
                a.account_type,
                aml.partner_id,
                m.state,
                aml.currency_id,
                aml.journal_id,
                aml.product_id ,
                a.id as account_id,
                m.name as entry,
                j.name as journal,
                p.name as partner_name,
                p.vat as vat,
                p.ref as ref,
                aml.name as ref_label,
                aml.amount_residual_currency as total_bal_curr,
                aml.amount_currency as amount_curr,
                case when matching_number is not null then True else False end as reconciled,
                cur.name as curr_name
        '''

    @api.model
    def _from(self):
        return '''
            FROM  account_move_line aml 
                LEFT JOIN account_account a on aml.account_id=a.id 
                LEFT JOIN account_move m on aml.move_id=m.id
                LEFT JOIN account_journal j on aml.journal_id=j.id 
                LEFT JOIN res_partner p on aml.partner_id=p.id 
                LEFT JOIN res_currency cur on aml.currency_id=cur.id 
        '''.format(
            currency_table=self.env['res.currency']._get_query_currency_table({'multi_company': True, 'date': {'date_to': fields.Date.today()}}),
        )
        
        


    @api.model
    def _where(self):
        return '''
        '''


