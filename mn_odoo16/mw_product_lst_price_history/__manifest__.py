# -*- coding: utf-8 -*-

{
    'name': 'MW Product list price history',
    'license': 'LGPL-3',
    'version': '1.0',
    'sequence': 100,
    'category': 'Product',
    'author': 'Y Consulting, Nasaa',
    'description': """
        Product list price history """,
    'depends': ['mw_stock_account', 'product'],
    'data': [
            "security/ir.model.access.csv",
            "views/product_lst_price_history_view.xml"
             ],
    'installable': True,
    'application': False,
}
