# -*- coding: utf-8 -*-

{
    'name': 'Mission to Payment Request',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Purchase',
    'author': 'Managewall LLC',
    'description': """Томилолтоос төлбөрийн хүсэлт үүсгэх
                   """,
    'website': 'http://managewall.mn',
    'depends': ['mw_hr','mw_account_payment_request'],
    'data': [
        'security/security.xml',   
        'security/ir.model.access.csv', 
        'views/mission_to_payment_view.xml',
    ],
    'installable': True,
    'application': False,
    'qweb': ['static/xml/*.xml'],
}