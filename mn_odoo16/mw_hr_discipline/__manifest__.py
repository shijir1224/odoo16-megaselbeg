# -*- coding: utf-8 -*-

{
    'name': 'MW Hr Discipline',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Discipline Management',
    'author': 'Managewall Nandinzaya',
    'description': """
        - Сахилгын шийтгэл бүртгэл 
        - Сахилгын шийтгэл тайлан 
        """,
    'depends': ['hr','mw_hr','mw_dynamic_flow'],
    'data': [
       'security/document_security.xml',
        'security/ir.model.access.csv', 
        'views/discipline_view.xml',       
    ],
    'installable': True,
    'application': False,
}
