# -*- coding: utf-8 -*-

{
    'name': "Salesman's Route planner",
    'version': '1.0',
    'sequence': 31,
    'category': 'Sales Management',
    'author': 'Managewall LLC',
    'description': """Боруулалтын модуль
                        - Худалдааны төлөөлөгчийн маршрут
                    """,
    'depends': ['base', 'sale', 'mw_sales_master_plan', 'base_geolocalize', 
                # 'web_google_maps_drawing'
                ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/salesman_route_planner_view.xml',
        'views/res_partner_inherit_view.xml',
        'views/res_user_location.xml',
        'wizard/wizard_salesman_route_report_view.xml',
        'wizard/wizard_salesman_route_excel_report_view.xml',
        'report/salesman_route_report_view.xml',
        'report/salesman_route_map_report_view.xml',
        'views/menu_view.xml',
        # 'views/google_places_template.xml'
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_qweb': [
            'mw_salesman_route_planner/static/xml/custom_templates.xml'
        ],
        'web.assets_backend': [
            'mw_salesman_route_planner/static/js/widget.js',
        ],
    },
    'license': 'OPL-1',
}
