# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Sales Batch Return',
    'version': '1.0.1',
    'category': 'Sales',
    'sequence': 21,
    'summary': 'Бор-г бөөнөөр буцаах',
    'author': 'Managewall LLC',
    'website': 'http://managewall.mn',
    'description': "",
    'depends': [
        'mw_sale_stock',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/sale_return_views.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
