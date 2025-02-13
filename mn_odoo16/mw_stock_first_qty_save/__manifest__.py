# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Stock Move First QTY Save',
    'version': '1.0.1',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Stock Account',
    'description': "",
    'depends': ['stock_account','mw_stock'],
    'data': [
        'views/stock_first_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
