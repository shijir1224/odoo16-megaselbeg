# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Mining account product',
    'version' : '1.0',
    'license': 'LGPL-3',
    'summary': 'Account product',
    'sequence': 40,
    'description': """
Stock & Product accounts
====================
    """,
    'category': 'Accounting, product, warehouse',
    'website': 'https://www.managewall.mn',
    'depends' : ['account','purchase','stock_account', 'product', 'mw_base','branch','mw_technic_maintenance','mw_stock_moves',
                'mw_analytic_account',
                 'mw_stock_account','mw_account_financial_report'],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'views/product_account_view.xml',
        'views/account_move_view.xml',
        'views/account_analytic_line_views.xml',
        'report/account_transaction_balance_view.xml',
        'report/analytic_move_report_view.xml'
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
