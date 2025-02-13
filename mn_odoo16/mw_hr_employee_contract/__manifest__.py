# -*- coding: utf-8 -*-

{
    'name': 'MW HR Employee Contract',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Human Recource Management',
    'author': 'Managewall LLC',
    'description': """
        HR """,
    'depends': ['hr','mw_hr'],
    'data': [
        'security/security.xml',   
        'security/ir.model.access.csv', 
        'views/hr_employee_contract_view.xml',
        'views/employee_contract_print_view.xml',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': False,
    'qweb': ['static/xml/*.xml'],
}
