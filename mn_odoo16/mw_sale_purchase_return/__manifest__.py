# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Sales Purchase Batch Return',
    'version': '1.0.1',
    'category': 'Sales',
    'sequence': 21,
    'summary': 'Борлуулалт болон ХА-н буцаалтыг холбогч',
    'author': 'Managewall LLC',
    'website': 'http://managewall.mn',
    'description': "",
    'depends': [
        'mw_sale_return',
        'mw_purchase_return',
        'inter_company_rules'
    ],
    'data': [
        'views/sale_return_views.xml',
        'views/purchase_return_views.xml'
    ],
    'qweb': [],
    'installable': True,
    'auto_install': True,
    'license': 'OPL-1',
}
