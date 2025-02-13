# -*- coding: utf-8 -*-

{
    'name': 'MW HR Promotion',
    'version': '1.0',
    'sequence': 20,
    'category': 'HR Management',
    'author': 'Managewall LLC',
    'description': """
        HR """,
    'depends': ['hr','mw_hr'],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/promotion_view.xml'
        
    ],
    'installable': True,
    'auto_install': False,
}
