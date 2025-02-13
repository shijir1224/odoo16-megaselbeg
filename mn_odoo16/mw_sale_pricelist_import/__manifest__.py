# -*- coding: utf-8 -*-
{
    'name': 'Sale pricelist import',
    'version': '2.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Sales Management',
    'author': 'Managewall LLC',
    'description': """
        Sale pricelist import """,
    'depends': ['sale','product','mw_sale_pricelist_confirm'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sale_pricelist_import_view.xml',
    ],
    'installable': True,
    'application': True,
}
