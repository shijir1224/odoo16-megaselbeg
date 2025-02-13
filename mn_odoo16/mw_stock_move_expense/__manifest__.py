# -*- coding: utf-8 -*-

{
    'name': 'Stock move expense',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Stock',
    'website': 'http://managewall.mn',
    'author': 'Managewall Amaraa',
    'description': """
        Internal move request, Other incoming, Бараа материал шаардах зардал хуваах""",
    'depends': ['mw_stock_moves', 'mw_account_expense_allocation','product_brand'],
    'summary': '',
    'data': [
        'views/stock_product_expense_view.xml',
    ],
    'installable': True,
    'application': False,
}
