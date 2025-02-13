# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Managewall Account Report",
    'version': '16.1',
    'category': 'Accounting/Accounting',
    'sequence': 40,
    'summary': 'Manage financial and analytic accounting',
    'description': """Санхүүгийн  тайлангууд модуль
                - Тайлан тохируулах
                - Тайлан хэвлэх
                    """,
    'website': 'http://managewall.mn',
    'depends': ['account','mw_account', 'product_brand','mw_base', 'base', 'branch','account_financial_report', 'date_range'],
    'data': [
#         'data/account_data.xml',
#         'data/ir_cron.xml',

        'security/ir.model.access.csv',
        'security/account_security.xml',
        'report/account_cashflow_report_view.xml',
        'report/account_transaction_balance_view.xml',
        'report/account_report_view.xml',
        'report/account_vat_report_view.xml',
        'report/account_vat_sale_report_view.xml',
        'views/account_report_view.xml',
        'wizard/account_report_mw_view.xml',
        'wizard/account_balance_sheet_view.xml',
        'wizard/account_income_statement_view.xml',
        'wizard/account_equity_changes_view.xml',
        'wizard/account_transaction_balance_view_wizard_view.xml',
        'wizard/account_partner_ledger_view.xml',
        'wizard/account_partner_detail_view.xml',
        'wizard/account_partner_detail_cash_view.xml',
        'wizard/account_transaction_balance_view.xml',
        'wizard/account_partner_ledger_old_view.xml',
        'wizard/account_general_ledger_q_view.xml',
        'wizard/account_payable_account_detail_view.xml',
        'wizard/account_general_journal_view.xml'
        
    ],
    'demo': [
#         'data/account_data.xml'
             ],
    'installable': True,
    'application': True,
#     'post_init_hook': '_account_accountant_post_init',
#     'uninstall_hook': "uninstall_hook",
    'license': 'OEEL-1',
    'assets': {
        'web.assets_backend': [
        ],
        'web.qunit_suite_tests': [
        ],
    }
}
