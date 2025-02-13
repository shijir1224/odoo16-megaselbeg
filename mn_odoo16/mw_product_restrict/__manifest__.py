# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Product Restrict',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Product',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Product Restrict',
    'description': "",
    'depends': ['mw_product','point_of_sale','mrp','purchase','sale'],
    'data': [
        'security/product_security.xml',
        'security/ir.model.access.csv'
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
