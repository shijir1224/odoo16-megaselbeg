# -*- coding: utf-8 -*-
{
    'name': 'MW Sale Pricelist',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Sales',
    'sequence': 21,
    'summary': 'Changed by Mongolian Sale Pricelist',
    'author': 'Managewall LLC',
    'website': 'http://managewall.mn',
    'description': "",
    'depends': [
        'sale','product','mw_dynamic_flow'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sale_pricelist_confirm_views.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}
