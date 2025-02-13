# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MN Stock picking print with Barcode',
    'version': '1.0.1',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Stock Confirmation',
    'description': """Location update best location 
        Гараар баркод хэвлэх""",
    'depends': ['mw_stock'],
    'data': [
        'views/stock_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
