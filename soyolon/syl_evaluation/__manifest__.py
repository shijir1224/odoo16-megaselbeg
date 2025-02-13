# -*- coding: utf-8 -*-

{
    'name': 'SYL MW Evaluation',
    'version': '1.0',
    'sequence': 20,
    'category': 'Evaluation Management',
    'author': 'Managewall Nandinzaya',
    'description': """
        Contract """,
    'depends': ['hr','mw_hr_evaluation','mw_hr'],
    'data': [
        'security/security.xml',
        'views/evaluation_year_view.xml',
        'views/evaluation_view.xml',
        'views/evaluation_emp_view.xml',
        'views/evaluation_daily_view.xml',
        'views/evaluation_cons_view.xml',
        'views/hr_project_evaluation_view.xml',
        'security/ir.model.access.csv',
        
        'wizard/eval_report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
