# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Asset Management',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Accounting/Accounting',
    'sequence': 20,
    'author': 'Duulga Managewall LLC',
    'summary': 'Changed by Mongolian Account Asset',
    'description': """Үндсэн хөрөнгийн модуль
                - Хөрөнгийн хөдөлгөөн
                - Хөрөнгийн дахин үнэлгээ
                - Хөрөнгийн капиталжуулалт
                - Хөрөнгийн борлуулалт
                - Хөрөнгийн акт
                - Хөрөнгийн тооллого
                - Хөрөнгийн тайлан
                    - Дэлгэрэнгүй тайлан
                    - Элэгдлийн тайлан
                    - Товчоо тайлан
                    - Эд хариуцагчийн карт
                    - Баримтын жагсаалт /Пивот/
                    """,
    'depends': ['account', 'account_asset','mw_dynamic_flow', 'branch', 'hr','report_xlsx','analytic'],
    'data': [
        'security/asset_security.xml',
        'security/ir.model.access.csv',
        'views/account_asset_view.xml',
        'views/account_asset_act_view.xml',
        'views/account_asset_capital_view.xml',
        'views/account_asset_continue.xml',
        'views/account_asset_history_view.xml',
        'views/account_asset_move_view.xml',
        'views/account_asset_revaluation_view.xml',
        'views/account_asset_sell_view.xml',
        'views/account_asset_update.xml',
        'views/account_asset_inventory_views.xml',
        'views/account_asset_type.xml',
        'data/data_account_standard_report.xml',
        'wizard/account_asset_standard_report_view.xml',
        'wizard/account_asset_validate.xml',
        'wizard/asset_depreciation_confirmation_wizard_views.xml',
        'report/report_account_standard_report.xml',
        'views/menuitem_view.xml',

    ],
    'website': 'http://managewall.mn',
    'installable': True,
    'icon': '/mw_base/static/src/img/managewall.png',
}
