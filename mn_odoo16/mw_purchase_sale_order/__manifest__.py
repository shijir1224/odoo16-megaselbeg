# -*- coding: utf-8 -*-

{
    'name': 'MW Purchase Sale Order',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 32,
    'category': 'Purchase',
    'website': 'http://manangewall.mn',
    'author': 'Managewall LLC by Badaaam',
    'description': """
        Main managewall create purchase from sale order""",
    'depends': [
        'mw_purchase_partner_stock','sale',
    ],
    'summary': '',
    'data': [
        "security/ir.model.access.csv",
        "views/purchase_order_views.xml",
    ],
    'installable': True,
    'application': False,
}
