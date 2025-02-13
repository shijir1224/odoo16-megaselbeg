# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Stock lot expiry Notification',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Sale',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Stock lot expiry Notification',
    'description': "",
    'depends': ['stock','product_expiry','mw_stock','mw_send_chat'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/stock_view.xml',
        'views/stock_inventory_views.xml'
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
