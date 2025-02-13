# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Accounting purchase rate',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Accounting',
    'sequence': 20,
    'author': 'Daramaa Managewall LLC',
    'summary': 'Changed by Mongolian Accounting',
    'description': "",
    'depends': ['account', 'mw_account', 'mw_purchase', 'mw_purchase_expense_custom'],
    'data': [
#         'security/account_security.xml',
#         'security/ir.model.access.csv',
        'views/account_view.xml',
        ],
    # 'demo': [
    # ],

    'website': 'http://managewall.mn',
    'installable': True,
    # 'auto_install': False,
    'qweb': [''],
}
