# -*- coding: utf-8 -*-
{
    'name' : 'MW HSE Employee Training',
    'version' : '0.1',
    'license': 'LGPL-3',
    'author' : 'Managewall LLC by Odka',
    'website' : 'http://www.managewall.mn/',
    'category' : 'MW HSE',
    'description': 'Mongolian mining operator company',
    'depends' : ['base','branch','hr','mw_hr','mw_hse','mw_timetable'],
    'data'   : [
                'security/hse_training_security.xml',
                'security/ir.model.access.csv',
                'views/hse_employee_training_view.xml',
                'views/hse_employee_daily_instruction_view.xml',
                'views/menu_view.xml',
    ],
    'init_xml' : [ ],
    'demo_xml' : [ ],
    'update_xml' : [],
    'installable': True,
    'application': True,
    'auto_install': False,
}