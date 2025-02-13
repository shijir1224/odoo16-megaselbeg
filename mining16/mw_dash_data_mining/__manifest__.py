# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Dashboard Data beldeh Mining',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Dashboard',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Manager dashboard-iig pr po-toi holboh',
    'description': "",
    'depends': ['mw_dash_data','mw_mining','mw_oil_fuel','mw_technic_maintenance'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
