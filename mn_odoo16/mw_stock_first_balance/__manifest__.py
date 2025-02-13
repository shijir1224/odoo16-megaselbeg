# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MN Stock First Balance',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Stock First Balance',
    'description': "",
    'depends': ['mw_stock', 'stock_account'],
    'data': [
        'security/ir.model.access.csv',
        'views/first_balance_view.xml',
        'views/zarlaga_import_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
