# -*- coding: utf-8 -*-

{
    'name': 'MW Documents Access Employee',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Human Recource Management',
    'author': 'Managewall Nandinzaya',
    'description': """
        HR """,
    'depends': ['hr','mw_hr','documents'],
    'data': [
        'views/documents_access_employee_view.xml',
    ],
    'installable': True,
    'application': False,
    'qweb': ['static/xml/*.xml'],
}
