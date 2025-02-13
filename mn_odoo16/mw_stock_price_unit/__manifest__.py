# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Stock Price Unit Limit',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Stock Account',
    'description': "Барааны Өртөг Хязгаарлах",
    'depends': ['stock_account'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/stock_price_unit_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
