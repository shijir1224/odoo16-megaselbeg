# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Sale ebarimt',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Sale',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Sale with ebarimt',
    'description': "",
    'depends': ['base','sale','sale_stock','mw_base_ebarimt'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
       # 'data/ebarimt_aimag_district.xml',
        'views/ebarimt_config_view.xml',
        'views/sale_order_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
