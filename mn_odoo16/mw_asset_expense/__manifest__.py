# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Account asset expense',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Accounting',
    'sequence': 20,
    'author': 'Daramaa Managewall LLC',
    'summary': 'Changed by Mongolian Accounting',
    'description': "Хөрөнгийн элэгдлийг олон зардлын дансад хувиарлан бичих.",
    'depends': ['account','mw_base','branch','base','mw_account_expense_allocation','mw_asset','mw_account_brand','account_asset'],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'views/account_asset_view.xml',
        ],
    'assets' : {
        'web.assets_backend': [
         ],
        },
    'website': 'http://managewall.mn',
    'installable': True,
    'qweb': [],
    'icon': '/mw_base/static/src/img/managewall.png',
}



