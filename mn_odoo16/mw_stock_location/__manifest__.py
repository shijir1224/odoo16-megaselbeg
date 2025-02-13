# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Stock Location',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Stock Confirmation',
    'description': "Location update best location",
    'depends': ['stock'],
    'data': [
        'views/stock_loc_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
