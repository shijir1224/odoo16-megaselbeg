# -*- coding: utf-8 -*-
{
    'name': 'MW Purchase Batch Return',
    'version': '1.0.1',
    'category': 'Inventory/Purchase',
    'sequence': 21,
    'summary': 'Changed to meet requirements of Mongolian Purchase',
    'author': 'Managewall LLC',
    'website': 'http://managewall.mn',
    'description': "ХА-г бөөнөөр буцаах",
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'depends': [
        'mw_purchase',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/purchase_return_views.xml'
    ],
}
