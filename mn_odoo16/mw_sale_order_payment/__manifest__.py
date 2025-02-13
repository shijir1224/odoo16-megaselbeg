# -*- coding: utf-8 -*-
{
    'name': 'SaleOrder payment',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Sale',
    'sequence': 23,
    'author': 'Managewall LLC',
    'summary': 'Payment on SaleOrder',
    'description': "Борлуулалтаас төлбөр төлдөг болгох",
    'depends': ['sale','sales_team'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sale_order_inherit_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'application': True,
    'auto_install': False,
}
