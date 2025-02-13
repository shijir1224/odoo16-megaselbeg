# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW mining evaluation',
    'version': '16.0.0',
    'license': 'LGPL-3',
    'category': 'MW evaluation',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian HR',
    'description': """""",
    'depends': ['mw_hr'],
    'data': [
        # 'security/security.xml',   
        'security/ir.model.access.csv', 
        'views/mining_evaluation_view.xml',
    ],

    'website': 'http://managewall.mn',
    'installable': True,
}
