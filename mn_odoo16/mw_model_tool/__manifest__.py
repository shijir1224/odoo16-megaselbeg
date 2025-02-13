# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Model tool',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Tool',
    'sequence': 28,
    'author': 'Managewall by Badaam',
    'summary': 'Model tool',
    'description': "",
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/model_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
