# -*- coding: utf-8 -*-

{
    'name': 'Soyolon Hse',
    'license': 'LGPL-3',
    'version': '1.0',
    'sequence': 10,
    'category': 'Hse',
    'author': 'Managewall LLC',
    'description': """
        Соёолон хаб модуль
        """,
    'depends': ['hr','mw_hr','mw_hse','mw_training','mw_hse_dangerous_waste','mw_hse_health','mw_hse_ppe_registration','mw_stock_moves','syl_hr','mw_hse'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/hse_stock_other_expense_view.xml',
        'views/hse_hazard_import_view.xml',
        'views/hse_act_view.xml',
        'views/hse_workplace_inspection.xml',
        'views/hse_work_hazard_analysis_view.xml',
        'views/hse_hazard_report.xml',
        'views/sequence.xml',
        'views/hse_accident_investigation_view.xml',
        'views/hse_risk_assessment_workplace_view.xml',
        'views/hse_discipline_action_view.xml',
        'views/hse_daily_report_view.xml',
        'views/hse_employee_training_view.xml',
        'views/hse_ambulance_view.xml',
        'views/hse_salary_kpi_line_view.xml',
        'views/environment_measurement_views.xml',
        'views/menu_view.xml',
    ],
    'installable': True,
    'application': False,
    'qweb': [],
}
