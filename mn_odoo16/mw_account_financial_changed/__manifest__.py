# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Managewall Account oca",
    'version': '16.1',
    'category': 'Accounting/Accounting',
    'sequence': 40,
    'summary': 'Manage financial and analytic accounting',
    'description': """Санхүүгийн  тайлангууд модуль
                - OCA насжилтыг дансдад тохируулах
                - Тайлан хэвлэх
                    """,
    'website': 'http://managewall.mn',
    'depends': ['account','account_financial_report', 'branch'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'security/account_security.xml',
        'views/account_view.xml'
    ],
    'demo': [
             ],
    'installable': True,
    'application': True,
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
