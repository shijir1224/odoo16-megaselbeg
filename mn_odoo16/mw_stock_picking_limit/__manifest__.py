# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Stock Picking Type Limit',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Stock',
    'description': "Орлого болон зарлага Агуулах тойм дээр үүсгэхийг хаах",
    'depends': ['stock'],
    'data': [
        'views/stock_picking_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
