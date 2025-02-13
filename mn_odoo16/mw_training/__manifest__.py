# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'ManageWall Training',
    'version': '1.0.1',
    'license': 'OPL-1',
    'category': 'MW Training',
    'sequence': 20,
    'author': 'Nandinzaya Managewall LLC',
    'summary': 'Changed by Mongolian HR',
    'description': """Сургалт
                - Сургалтын хүсэлт
                - Сургалт хөгжил 
                - Сургалтын бүртгэл
                - Сургалтын төрөл
                - Сургалтын хөтөлбөр төлөвлөгөө 
                   """,
    'depends': ['hr','mw_hr'],
    'data': [
        'security/training_security.xml',
        'security/ir.model.access.csv',
        'views/training_view.xml',
        'views/menu_view.xml',
    ],

    'website': 'http://managewall.mn',
    'installable': True,
}
