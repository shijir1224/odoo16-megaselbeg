# -*- coding: utf-8 -*-
{
    'name': 'MW HR',
    'version': '16.0.1.0',
    'license': 'LGPL-3',
    'category': 'MW Human resourse',
    'sequence': 20,
    'author': 'Solongo Managewall LLC',
    'summary': 'Changed by Mongolian HR',
    'description': """Хүний нөөцийн модуль
                - Хувийн хуудас
                    - Хувийн хуудас -- Миний мэдээлэл
                - Хүний нөөц
                    - Хүний нөөц  -- Хүний нөөц-- Хүний нөөц
                - Хүний нөөц
                    - Хүний нөөц  -- ЭА-- ЭА цалингийн хүсэлт
                - Тодорхойлолт
                    - Хүний нөөц  -- Тодорхойлолт 
                - Тайлан
                    - Хүний нөөц  -- Тайлан
                -Томилолт
                    """,
    'depends': ['hr', 'account','base','hr_recruitment', 'hr_contract','hr_skills','mw_dynamic_flow','base','hr_holidays'],
    'data': [
        'security/hr_security.xml',
        'data/ir_cron_data.xml',
        'views/hr_view.xml',
        'views/hr_tr_view.xml',
        'views/hr_shift_vacation_view.xml',
        'views/hr_employee_own_data_view.xml',
        'views/hr_menu.xml',
        'views/hr_mission_view.xml',
        'wizard/views/age_pivot_report_view.xml',
        'wizard/views/employee_detail_report_view.xml',
        'wizard/views/child_pivot_report_view.xml',
        'wizard/views/employee_turnover_view.xml',
        'wizard/views/hr_report_statistics.xml',
        'security/ir.model.access.csv',
    ],
    'website': 'http://managewall.mn',
    'installable': True,
}
