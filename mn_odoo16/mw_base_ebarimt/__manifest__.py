# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Managewall ebarimt 3.0",
    'version': '16.1',
    'category': 'accounting',
    'sequence': 40,
    'summary': 'Manage Ebarimt',
    'description': """Nбаримт модуль
                - 
                    """,
    'depends': ['mw_base',],
    'data': [
        'views/account_tax_views.xml',
        'data/tax_data.xml'
    ],
    'assets': {
        'web.assets_qweb': [
        ],
    },
    'qweb': [],
    'website': '',
    'installable': True,
    'auto_install': False,
}