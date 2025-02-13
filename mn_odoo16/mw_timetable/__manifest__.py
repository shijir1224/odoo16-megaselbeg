# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Managewall Timetable',
    'version': '1.1',
    'category': 'MW Timetable',
    'sequence': 20,
    'author': 'Nandinzaya Managewall LLC',
    'summary': 'Changed by Mongolian HR',
    'description': """Цаг бүртгэл модуль
                - Ээлж тохиргоо
                    - Хүний нөөц -- Цаг бүртгэл--Ээлж
                - Хуваарь ростер тохиргоо
                    - Хүний нөөц  -- Цаг бүртгэл -- Хуваарь
                - Цагийн төлөвлөгөө
                    - Хүний нөөц  -- Цаг бүртгэл -- Цагийн төлөвлөгөө
                - Цагийн баланс
                    - Хүний нөөц  -- Цаг бүртгэл -- Цагийн баланс  
                - Цагийн хүсэлт
                    - Хүний нөөц  -- Бүх цаг хүсэлт
                    """,
    'website': 'http://managewall.mn',
    'depends': ['hr','hr_holidays','branch','hr_attendance','mw_hr','mw_dynamic_flow','base','mw_attendance_terminal'],
    'data': [
        'security/hr_security.xml',
        'wizard/back_description_view.xml',
        'views/timetable_view.xml',
        'views/timetable_line_view.xml',
        'views/timetable_other_view.xml',
        'views/timetable_plan_view.xml',
        'views/hour_balance_view.xml',
        'views/hr_holidays_view.xml', 
        'views/menu.xml',
        'wizard/timetable_report_view.xml',   
        'wizard/timetable_daily_report_view.xml',   
        'security/ir.model.access.csv', 
    ],
    'installable': True,
    'auto_install': False,
    'assets' : {
        'web.assets_backend': [
            'mw_timetable/static/src/xml/*',
            'mw_timetable/static/src/js/hour_balance.js',
            'mw_timetable/static/src/js/hour_balance_wid.js',
            'mw_timetable/static/src/js/timesheet_wid.js',
            'mw_timetable/static/src/js/timesheet.js',
           
        ],
        'web.assets_qweb': [
            # EXAMPLE: Add everyithing in the folder
            'mw_timetable/static/src/xml/*',
        ],
        'web.assets_common_minimal': [
            # EXAMPLE lib          
        ],
        'web.assets_common': [
            # EXAMPLE Can include sub assets bundle
            'mw_timetable/static/css/base.css',
            'mw_timetable/static/css/balance.css',
            'mw_timetable/static/src/less/scroltable.css',
        ],
    },
        'license': 'OPL-1',
}
