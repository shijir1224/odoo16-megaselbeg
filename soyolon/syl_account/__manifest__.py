# -*- coding: utf-8 -*-

{
    'name': 'Soyolon Account',
    'version': '1.0',
    'sequence': 10,
    'category': 'Account',
    'author': 'Managewall LLC',
    'description': """
        Соёолон санхүүгийн модуль
        """,
    'depends': ['mw_account','account','account_asset','mw_asset'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_view.xml',
        'views/partner_view.xml',
        'views/account_asset_view.xml',
        'wizard/account_vat_report_view.xml',
        'wizard/account_vat_sale_report_view.xml',
    ],
    'installable': True,
    'application': False,
    'qweb': [],
}
