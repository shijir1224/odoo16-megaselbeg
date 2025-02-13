# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Stock quant each price',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Technic',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Барааны үлдэгдэлийн тайлан дээр нэгж үнэ нэмэгдсэн',
    'description': "",
    'depends': ['stock','mw_stock_account', 'mw_purchase_report'],
    'data': [
        'security/security.xml',
        # 'security/ir.model.access.csv',
        'views/stock_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
