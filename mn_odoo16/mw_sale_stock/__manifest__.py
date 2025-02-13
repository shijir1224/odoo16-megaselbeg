# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Sale Stock',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Sales',
    'sequence': 21,
    'summary': 'Changed by Mongolian Sale Stock',
    'author': 'Managewall LLC',
    'website': 'http://managewall.mn',
    'description': "",
    'depends': [
        'mw_base',
        'sale_stock'
    ],
    'data': [
        'security/security.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml'
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}
