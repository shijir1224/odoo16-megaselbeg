# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MN Stock Lot FIFO DATE',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Stock Confirmation Date-eer erembleh',
    'description': "",
    'depends': ['stock','product_expiry'],
    'data': [
        'views/stock_lot_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
