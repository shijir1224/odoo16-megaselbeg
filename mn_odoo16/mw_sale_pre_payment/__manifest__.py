# -*- coding: utf-8 -*-

{
    'name': 'MW Sale Pre Payment',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Sale',
    'website': 'http://managewall.mn',
    'author': 'Managewall LLC',
    'description': """
        Uridchilgaa tuldug module""",
    'depends': [
        'sale',
    ],
    'summary': '',
    'data': [
        "views/sale_pay.xml",
    ],
    'installable': True,
    'application': False,
}
