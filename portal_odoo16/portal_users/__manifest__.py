
# -*- coding: utf-8 -*-
{
    'name': 'users Portal',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 20,
    'category': 'Portal Web',
    'author': 'mw',
    'description': """
        users Portal web  """,
    'depends': ['web', 'website', 'hr','mw_timetable', 'mw_hr','portal'], # 'users_technic',
    'data': [
        'views/users_leaves_portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # 'users_portal/static/src/js/portal_none.js',
        ],
    },
}
