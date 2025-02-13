# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Mongolian Account Period',
    'version': '1.1',
    'license': 'LGPL-3',
    'depends': ['mw_account'],
    'author': 'Daramaa Managewall LLC',
    'website': 'http://managewall.mn',
    'summary': 'Changed by Mongolian Accounting',
    'description': """

    """,
    "depends" : [
        "account",
        "account_accountant",
        "mw_account",
        # "mw_dynamic_flow",
        # "base",
    ],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'wizard/account_period_close_view.xml',
        'views/account_period_view.xml',
        'views/account_fiscalyear_view.xml',
    ],
    'installable': True,
    'auto_install': False
}
