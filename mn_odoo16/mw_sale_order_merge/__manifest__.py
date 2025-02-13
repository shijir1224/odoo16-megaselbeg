# -*- coding: utf-8 -*-
{
    'name': 'MW Sale Order Merge',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Sale order',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': ' Sale order merge',
    'description': "",
    'depends': [
        'mw_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_order_merge.xml',
        'data/ir_actions_server.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
