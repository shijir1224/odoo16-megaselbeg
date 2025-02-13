# -*- coding: utf-8 -*-

{
    'name': 'MW HR Set Confirm Users',
    'version': '1.0',
    'sequence': 31,
    'category': 'Human Recource Management',
    'author': 'Managewall LLC',
    'description': """
        HR """,
    'depends': ['hr','mw_hr'],
    'data': [
        'security/ir.model.access.csv', 
        'views/set_user_view.xml',
    ],
    'installable': True,
    'application': False,
    'qweb': ['static/xml/*.xml'],
}
