# -*- coding: utf-8 -*-
{
    'name': 'MW HR Allowance',
    'version': '16.0.1.0',
    'license': 'LGPL-3',
    'category': 'MW Human resourse',
    'sequence': 21,
    'author': 'Managewall LLC',
    'depends': ['hr', 'mw_hr','mw_account_payment_request'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_allowance_view.xml',
        'wizard/allowance_view.xml',
        # 'views/menu.xml'
    ],
    'website': 'http://managewall.mn',
    'installable': True,


}
