# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Managewall Account branch",
    'version': '16.1',
    'category': 'Accounting/Accounting',
    'sequence': 40,
    'summary': 'Manage branch accounting',
    'description': """Санхүү гүйлгээг ажил гүйлгээгээр дүрэм нэмэх
                    """,
    'website': 'http://managewall.mn',
    'depends': ['account','mw_base', 'branch'],
    'data': [
        'security/ir.model.access.csv',
        'security/branch_security.xml',

        'views/account_view.xml',
    ],
    'demo': [
             ],
    'installable': True,
    'application': True,
    'icon': '/mw_base/static/src/img/managewall.png',
    'license': 'OEEL-1',
    'assets': {
        'web.assets_backend': [
        ],
        'web.qunit_suite_tests': [
        ],
    }
}
