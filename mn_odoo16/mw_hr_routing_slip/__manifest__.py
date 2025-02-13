# -*- coding: utf-8 -*-

{
    'name': 'Managewall HR Routing slip',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Human Recource Management',
    'author': 'Managewall LLC',
    'description': """Тойрох хуудас
                - Тохиргоо
                  - Тойрох хуудас тохиргоо
                   """,
    'website': 'http://managewall.mn',
    'depends': ['hr','mw_hr','mw_hr_applicant'],
    'data': [
        'security/security.xml',   
        'security/ir.model.access.csv', 
        'views/routing_slip_view.xml',
    ],
    'installable': True,
    'application': False,
    'qweb': ['static/xml/*.xml'],
}
