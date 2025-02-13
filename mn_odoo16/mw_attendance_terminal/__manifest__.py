# -*- coding: utf-8 -*-

{
    'name': 'MW attendance terminal',
    'version': '1.0',
   
    'sequence': 31,
    'category': 'Tools',
    'website': 'http://managewall.mn',
    'author': 'Managewall LLC Nandinzaya',
    'description': """
        Download attendance from Terminal, DB
        pip install zklib
        pip install pymssql
        ZK төхөөрөмжөөс ирц татах """,
    'depends': ['base','hr','hr_attendance'],
    'summary': '',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_attendance_terminal_view.xml',
        'views/mw_attendance_view.xml',
        'wizard/attendance_generator_view.xml', 
    ],
     'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
