# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MN accounting budget',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Accounting',
    'sequence': 20,
    'author': 'Daramaa Managewall LLC',
    'summary': 'Changed by Mongolian Accounting',
    'description': """мөнгөн төсөв модуль
                - Хэлтсийн төсөв бүртгэх импорт хийх
                    - Мөнгөн төсөвийн хяналт -- Хэлтсийн жилийн төсөв
                -  Нэгтгээд компаний жилийн төсөв
                    - Мөнгөн төсөвийн хяналт -- компаний жилийн төсөв
                - төсөв шилжүүлэх
                    """,
    'depends': ['account','branch','mw_account','mw_base','mw_hr',        
                "mw_dynamic_flow",
                "mw_account_payment_request",
                "date_range"
        ],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'views/account_budget_import_view.xml',
        'views/account_budget_config_view.xml',
        'views/account_budget_view.xml',
        'wizard/account_budget_change_view.xml',
        'views/account_budget_company_view.xml',
        ],
    # 'demo': [
    # ],

    'website': 'http://managewall.mn',
    "auto_install": False,
    "installable": True,
    'icon': '/mw_account_budget/static/img/budget.png',
}
