# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Stock Report Turnover',
    'version': '1.0.1',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Stock Account',
    'description': "",
    'depends': ['stock','mw_stock_product_report','point_of_sale','mw_stock_moves'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/stock_report_turnover_view.xml',
        'views/wizard_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
