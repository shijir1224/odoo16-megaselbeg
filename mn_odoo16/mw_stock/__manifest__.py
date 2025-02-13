# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Stock',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed to meet standards of Mongolia',
    'description': "",
    'depends': ['mw_base', 'stock', 'mw_dynamic_flow'],
    'data': [
        'security/mw_stock_security.xml',
        'security/ir.model.access.csv',
        'views/data.xml',
        'views/stock_move_view.xml',
        'views/stock_inventory_view.xml',
        'views/stock_view.xml',
        'views/stock_move_line_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_scrap_view.xml',
        'views/stock_quant_view.xml',
        'views/stock_quant_report_view.xml',
        'views/stock_location_view.xml',
        'views/stock_move_lock_view.xml',
        'views/product_view.xml',
        'wizard/stock_inventory_print_view.xml',
    ],
    'qweb': [],
    'assets': {
        'web.assets_backend': [
            'mw_stock/static/lib/JsBarcode',
        ],
    },
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
