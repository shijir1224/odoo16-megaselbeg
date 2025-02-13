# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Mw Salary',
    'version': '1.0.1',
    'license': 'OPL-1',
    'category': 'Salary',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Salary',
    'description': "",
    'depends': ['hr','mw_hr','mw_timetable','hr_contract'],
    'data': [
    
        'data/auth_signup_data.xml',
        'security/salary_security.xml',
        'security/ir.model.access.csv',
        'views/salary_config_view.xml',
        'views/salary_view.xml',
        'views/vacation_salary_view.xml',
        'views/list_salary_view.xml',
        'views/salary_update_view.xml',
        'views/receivable_payable_view.xml',
        'wizard/bank_report_view.xml',
        # 'wizard/final_salary_wizard_view.xml',
        # 'wizard/final_salary_wizard_manager_view.xml',
        'wizard/ndsh_report_view.xml',
        # 'wizard/employee_salary_page_view.xml',
        # 'wizard/employee_salary_page_manager_view.xml',
        # 'wizard/hhoat_report_view.xml',
        'wizard/final_salary_department_view.xml',
        'wizard/salary_report_view.xml',
        'wizard/pit_grew_total_new_view.xml',
        'wizard/tax_report_view.xml',
        'wizard/dynamic_report_view.xml',
        'wizard/payment_request_create_view.xml',
        
    ],

    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
    'assets' : {
        'web.assets_backend': [
            'mw_salary/static/src/xml/*',
            # 'mw_salary/static/src/js/salary_wid.js',
            'mw_salary/static/src/js/salary.js',
            
        ],
        'web.assets_qweb': [
            # EXAMPLE: Add everyithing in the folder
            'mw_salary/static/src/xml/*',
        ],
        'web.assets_common': [
            # EXAMPLE Can include sub assets bundle
            'mw_salary/static/css/salary.css',
            'mw_salary/static/src/less/scroltable.css',
        ],
        }
}
