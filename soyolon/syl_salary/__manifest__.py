# -*- coding: utf-8 -*-

{
    'name': 'Soyolon Salary',
    'version': '1.0',
    'sequence': 10,
    'category': 'Salary',
    'author': 'Managewall LLC',
    'description': """
        Соёолон цалингийн модуль
        """,
    'depends': ['mw_hr','mw_salary','mw_timetable'],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/salary_view.xml',
        'views/other_salary_view.xml',
        'data/syl_template_data.xml',
        'wizard/ndsh_report_syl_view.xml',
        'wizard/pit_grew_total.xml',
        'wizard/other_bank_report.xml',
    ],
    'installable': True,
    'application': False,
    'qweb': [],
    'assets' : {
        'web.assets_backend': [
            'syl_salary/static/src/xml/*',
            'mw_salary/static/src/js/salary.js',
        ],
        'web.assets_qweb': [
            'syl_salary/static/src/xml/salary_templates.xml',
        ],
        'web.assets_common': [
            'mw_salary/static/css/salary.css',
            'mw_salary/static/src/less/scroltable.css',
        ],
        }
}
