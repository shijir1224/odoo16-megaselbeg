# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Stock Account',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Stock Account',
    'description': "",
    'depends': ['stock_account','mw_account','mw_stock','mw_analytic_account'],
    'data': [
        'security/mn_stock_security.xml',
        'security/ir.model.access.csv',
        'wizard/delete_first_balance_view.xml',
        'views/stock_account_view.xml',
        'views/stock_move_change_price_unit_view.xml',
        'views/stock_price_unit_change_log_view.xml',
        'views/stock_move_change_date_view.xml',
        'views/stock_quant_report_view.xml',
        'views/account_move.xml'
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
