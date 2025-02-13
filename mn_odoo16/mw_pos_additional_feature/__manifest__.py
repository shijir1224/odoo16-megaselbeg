# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW POS additional features',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Point of Sale',
    'sequence': 23,
    'author': 'Managewall LLC',
    'summary': 'v13 to upgrade v15',
    'description': "MW core POS additional features",
    'depends': [
        'point_of_sale'
    ],
    'data': [
        'views/pos_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
