# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Managewall Account",
    'version': '16.1',
    'category': 'Accounting/Accounting',
    'sequence': 40,
    'summary': 'Manage financial and analytic accounting',
    'description': """Санхүүгийн модуль
                - Мөнгөн гүйлгээний төрөл
                    - Санхүү -- Тохиргоо -- Мөнгөн гүйлгээний төрөл -- Мөнгөн гүйлгээний төрөл цэс
                - Дансны төрөл
                    - Санхүү -- Тохиргоо -- Санхүү -- Дансны төрөл цэс
                - Данс
                    - Нэмэгдсэн талбарууд
                        - Зөвшөөрөгдөх мөнгөн гүйлгээний төрлүүд
                    """,
    'website': 'http://managewall.mn',
    'depends': ['account','account_accountant', 'mw_base', 'base', 'branch',],
    'data': [
#         'data/account_data.xml',
#         'data/ir_cron.xml',
        'security/ir.model.access.csv',
        'security/account_security.xml',

        'views/account_view.xml',
        'views/account_bank_statement_view.xml',
        'views/account_move_import_view.xml',
        'views/account_cash_type.xml',
        'views/account_bank_statement_import_view.xml',
        'views/account_payment.xml',
        'views/account_move_view.xml',
        'views/account_move_line_update_view.xml',
        'wizard/account_transaction_balance_view.xml',
        'wizard/import_bank_statement_view.xml',
        'report/account_transaction_balance_pivot_view.xml',
        'wizard/bank_payment_match_view.xml',
        'wizard/cash_box.xml',
        'wizard/pos_box.xml',
        'wizard/account_automatic_entry_wizard_views.xml',
        'wizard/account_mw_automatic_entry_wizard_views.xml',
        'wizard/account_mw_curr_automatic_entry_wizard_views.xml',
        'wizard/account_bank_report_view.xml',
        'report/analytic_move_report_view.xml',
    ],
    'demo': [
#         'data/account_data.xml'
             ],
    'installable': True,
    'application': True,
    'icon': '/mw_base/static/src/img/managewall.png',
#     'post_init_hook': '_account_accountant_post_init',
#     'uninstall_hook': "uninstall_hook",
    'license': 'OEEL-1',
    'assets': {
        'web.assets_backend': [
        ],
        'web.qunit_suite_tests': [
        ],
    }
}
