# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Mongolian Account Ebarimt',
    'version': '1.1',
    'license': 'LGPL-3',
    'depends': ['mw_account'],
    'author': 'Daramaa Managewall LLC',
    'website': 'http://managewall.mn',
    'summary': 'Changed by Mongolian Accounting',
    'description': """

    """,
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'views/account_ebarimt_view.xml',
    ],
    'installable': True,
    'auto_install': False
}
