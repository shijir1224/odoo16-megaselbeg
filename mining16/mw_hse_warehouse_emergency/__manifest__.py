# -*- coding: utf-8 -*-
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-today MNO LLC (<http://www.mno.mn>)
#
{
    'name' : 'MW HSE Warehouse Emergency',
    'version' : '0.1',
    'license': 'LGPL-3',
    'author' : 'Managewall LLC by Odka',
    'website' : 'http://www.managewall.mn/',
    'category' : 'MW HSE',
    'description': 'ХАБ Агуулахын бүртгэл бараагаар болон галын хороор',
    'depends' : ['base','hr','mw_hr','mw_hse'],
    'data'   :  [
        'security/hse_warehouse_security.xml',
        'security/ir.model.access.csv',
        'views/hse_warehouse_view.xml',
        'views/hse_warehouse_health_view.xml',
        'views/hse_product_view.xml',
        'views/menu_view.xml',
    ],
    'init_xml' : [ ],
    'demo_xml' : [ ],
    'update_xml' : [],
    'installable': True,
    'application': True,
    'auto_install': False,
}