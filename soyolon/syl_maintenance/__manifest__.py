# -*- coding: utf-8 -*-

{
    'name': 'Soyolon Maintenance',
    'version': '1.0',
    'sequence': 31,
    'category': 'Maintenance',
    'author': 'Badaam Managewall LLC',
    'description': """
        Соёолон засварын модуль
        """,
    'depends': ['mw_technic_maintenance','mw_factory_equipment'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/maintenance_workorder_view.xml',
        'report/maintenance_working_report_view.xml',
        'views/menu_view.xml',
        # 'report/test_report_view.xml',

    ],
    'installable': True,
    'application': False,
    'qweb': [],
}
