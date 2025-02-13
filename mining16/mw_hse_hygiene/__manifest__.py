# -*- coding: utf-8 -*-
{
    'name' : 'MW HSE Hygiene',
    'version' : '0.1',
    'license': 'LGPL-3',
    'author' : 'Managewall LLC by Odka',
    'website' : 'http://www.managewall.mn/',
    'category' : 'MW HSE',
    'description': 'ХАБ Эрүүл ахуй',
    'depends' : ['base','hr','mw_hr','mw_hse'],
    'data'   :  [
        'security/hse_hygiene_security.xml',
        'security/ir.model.access.csv',
        'views/hse_food_hygiene_view.xml',
        'views/rida_check_view.xml',
        'views/food_check_view.xml',
        'views/food_poisoning_view.xml',
        'views/tool_measurement_view.xml',
        'views/hygiene_sterilization_view.xml',
        'views/menu_view.xml'
    ],
    'init_xml' : [ ],
    'demo_xml' : [ ],
    'update_xml' : [],
    'installable': True,
    'application': True,
    'auto_install': False,
}