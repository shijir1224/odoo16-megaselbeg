# -*- coding: utf-8 -*-

{
    'name': 'MW Sale Invoice',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Sale',
    'website': 'http://managewall.mn',
    'author': 'Managewall LLC',
    'description': """
        Main managewall Sale stock""",
    'depends': [
        'sale_stock',
    ],
    'summary': '',
    'data': [
        "views/sale_invoice.xml",
    ],
    'installable': True,
    'application': False,
}
