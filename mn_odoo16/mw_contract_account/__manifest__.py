# -*- coding: utf-8 -*-

{
    'name': 'MW Contract Account Purchase',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Account Purchase & Contract Management',
    'author': 'Managewall Nandinzaya',
    'description': """
        MW Purchase sccount contract """,
    'depends': ['account','mw_purchase','mw_contract'],
    'data': [ 
        'security/purchase_security.xml',
        'security/ir.model.access.csv',
        'views/contract_view.xml',
        'report/contract_payment_pivot_view.xml',
    ],
    'installable': True,
    'application': False,
    'qweb': ['static/xml/*.xml'],
}
