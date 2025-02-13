# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Mining Import',
    'version': '1.0.0',
    'category': 'Mining',
    'sequence': 21,
    'author': 'Managewall LLC',
    'summary': 'Mining Haul  mark medee import hiih',
    'description': "",
    'depends': ['mw_mining'],
    'data': [
        'security/ir.model.access.csv',
        'views/mining_import_view.xml',
    ],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
