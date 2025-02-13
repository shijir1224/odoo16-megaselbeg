# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Product Auto Coding',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Product category',
    'sequence': 21,
    'author': 'Munkhbat Managewall LLC',
    'summary': '',
    'description': "Product auto coding",
    'depends': [
        'mw_product'
    ],
    'data': [
        
        'views/product_auto_code_view.xml',
        
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
