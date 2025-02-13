# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Dashboard Data beldeh',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Dashboard',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Manager dashboard-iig pr po-toi holboh',
    'description': "",
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/dashboard_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
