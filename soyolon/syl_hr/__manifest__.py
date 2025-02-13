# -*- coding: utf-8 -*-

{
    'name': 'Soyolon Hr',
    'version': '1.0',
    'sequence': 10,
    'category': 'HR Management',
    'author': 'Managewall LLC',
    'description': """
        Соёолон хүний нөөцийн модуль
        """,
    'depends': ['hr_recruitment','mw_hr', 'mw_salary', 'mw_hr_order', 'hr', 'mw_hr_applicant','mw_hr_additional', 'utm', 'mw_hr_employee_contract', 'mw_hr_org_structure', 'mw_hr_discipline', 'mw_technic_equipment','mw_document','mw_hr_allowance'],
    'data': [
        'security/security.xml',
         'security/ir.model.access.csv',
        'views/hr_view.xml',
        'views/syl_hr_shift_vacation_view.xml',
        'views/hr_order_view.xml',
        'views/hr_shift_view.xml',
        'views/other_request_view.xml',
        'views/hr_job_view.xml',
        'views/hr_applicant_view.xml',
        'views/hr_tr_view.xml',
        'views/hr_mission_view.xml',
        'views/hr_resigned_view.xml',
        'views/act_wait_work_view.xml',
        'views/hr_migration_view.xml',
        'views/hr_offer_view.xml',
        'views/hr_turnover_view.xml',
        'views/syl_hr_complaint_view.xml',
        'wizard/resigned_report_view.xml',
        'wizard/age_pivot_report_syl_view.xml',
        'wizard/well_being_report_view.xml',
         'wizard/turn_over_report_view.xml',
       
    ],
    'installable': True,
    'application': False,
    'qweb': [],
}
