# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MN Analytic accounting',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Accounting',
    'sequence': 20,
    'author': 'Daramaa Managewall LLC',
    'summary': 'Changed by Mongolian Accounting',
    'description': "",
    'depends': ['account','hr','branch','mw_account','stock_account','mw_base','analytic','mw_account_brand'],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'views/account_view.xml',
        'views/account_analytic_create_views.xml',
        'wizard/automatic_entry_wizard_view.xml',
        'report/analytic_period_report_view.xml'
        ],
    # 'demo': [
    # ],
    'assets': {
        'web.assets_backend': [
            'mw_analytic_account/static/src/*',
        ],
    },
    'website': 'http://managewall.mn',
    'installable': True,
    # 'auto_install': False,
}
