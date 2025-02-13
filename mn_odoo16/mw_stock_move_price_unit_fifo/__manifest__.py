# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MN Stock Move Price Unit',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Stock Price Unit',
    'description': "",
    'depends': ['stock','stock_account','mw_stock'],
    'data': [
        'security/security.xml',
        'views/stock_inv_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
