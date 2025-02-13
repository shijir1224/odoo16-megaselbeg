# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Stock Quant view Main UOM',
    'version': '1.0.1',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Stock quant_main_uom',
    'description': "Өөр дээр тохируулсан агуулах дээр ",
    'depends': ['mw_stock','mw_stock_product_report'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/stock_quant_main_uom_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
