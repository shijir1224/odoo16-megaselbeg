# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MN Stock  Confirm',
    'version': '1.0.1',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Stock Confirmation',
    'description': "",
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/done_warehouse_view.xml',
        'views/stock_pick_view.xml',
        'wizard/many_done_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
