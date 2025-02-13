# -*- coding: utf-8 -*-

{
    'name': 'Stock moves',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Stock',
    'website': 'http://managewall.mn',
    'author': 'Managewall Amaraa',
    'description': """
        Internal move request, Other incoming, Other expense moves """,
    'depends': ['stock','mw_base', 'mw_stock_account',
                'mw_stock_moves','mw_hr','mw_factory_equipment','mw_product_warehouse_account'],
                # easy_pdf_creator
    'summary': '',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/stock_product_out_view.xml',
        'views/hr_view.xml',
        # 'report/product_expense_report_view.xml',
        'views/menu_view.xml',
    ],
    'installable': True,
    'application': False,
}
