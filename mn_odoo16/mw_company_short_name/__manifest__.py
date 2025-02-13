# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Company Short Name',
    'license': 'LGPL-3',
    'version': '1.0.1',
    'category': 'Base',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Monnis request',
    'description': "",
    'depends': ['base','hr','product','mw_dynamic_flow','web'],
    'data': [
        # 'security/security.xml',
        # 'security/ir.model.access.csv',
        'views/company_view.xml',
    ],
    'qweb': ["static/src/xml/base.xml"],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
