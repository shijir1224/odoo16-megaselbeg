# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW TAX REPORT',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Accounting',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian tax report',
    'description': "",
    'depends': ['mw_base','mw_account'],
    'data': [
        'report/TT02_report_view.xml',
        'report/menuitem_view.xml',
        'security/security.xml',
        'security/ir.model.access.csv'
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
