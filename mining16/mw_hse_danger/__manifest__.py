# -*- coding: utf-8 -*-
{
    'name' : 'MW HSE Danger',
    'version' : '0.1',
    'license': 'LGPL-3',
    'author' : 'Managewall LLC by Odka',
    'website' : 'http://www.managewall.mn/',
    'category' : 'MW HSE',
    'description': 'ХАБ Хортой аюулын байдал',
    'depends' : ['base','mw_hr','mw_hse'],
    'data'   :  [
        'security/hse_danger_security.xml',
        'security/ir.model.access.csv',
        'views/hse_danger_view.xml',
        'views/menu_view.xml',
    ],
    'init_xml' : [ ],
    'demo_xml' : [ ],
    'update_xml' : [],
    'installable': True,
    'application': True,
    'auto_install': False,
}