# -*- coding: utf-8 -*-
{
    'name' : 'MW HSE Dangerous Waste',
    'version' : '0.1',
    'license': 'LGPL-3',
    'author' : 'Managewall LLC by Odka',
    'website' : 'http://www.managewall.mn/',
    'category' : 'MW HSE',
    'description': 'ХАБ Байгаль орчны модуль',
    'depends' : ['base','mw_hr','mw_hse', 'mw_hse_danger'],
    'data'   :  [
        'security/hse_dangerous_security.xml',
        'security/ir.model.access.csv',
        'views/hse_dangerous_view.xml',
        'views/hse_land_use_permit_view.xml',
        'views/menu_view.xml',
    ],
    'init_xml' : [ ],
    'demo_xml' : [ ],
    'update_xml' : [],
    'installable': True,
    'application': True,
    'auto_install': False,
}