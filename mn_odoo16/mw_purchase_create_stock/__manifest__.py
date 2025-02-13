# -*- coding: utf-8 -*-

{
    'name': 'MW Purchase create stock',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Purchase',
    'website': 'http://manangewall.mn',
    'author': 'Managewall LLC',
    'description': """
        Product request to purchase order""",
    'depends': ['purchase','stock','mw_product'],
    'summary': '',
    'data': [
            "security/ir.model.access.csv",
            "views/purchase_create_stock_view.xml",
            "views/menu_item.xml",
    ],
    'installable': True,
    'application': False,
}
