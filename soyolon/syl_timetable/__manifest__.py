
# -*- coding: utf-8 -*-

{
    'name': 'Soyolon Timetable',
    'version': '1.0',
    'sequence': 20,
    'category': 'Timetable Management',
    'author': 'Managewall Nandinzaya',
    'description': """
        Soyolon timetable  """,
    'depends': ['hr','mw_timetable','syl_hr'],
    'data': [
        'views/syl_timetable_view.xml',
        'views/syl_holiday_view.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'auto_install': True,
}
