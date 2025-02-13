# -*- coding: utf-8 -*-

{
    'name': 'Soyolon Technic Equipment',
    'version': '1.0',
    'sequence': 31,
    'category': 'Technic',
    'author': 'Badaam Managewall LLC',
    'description': """
        Соёолон техник, тоног төхөөрөмжийн модуль
        """,
    'depends': ['mw_technic_equipment','mw_factory_equipment'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/technic_equipment_view.xml',
    ],
    'installable': True,
    'application': False,
    'qweb': [],
}
