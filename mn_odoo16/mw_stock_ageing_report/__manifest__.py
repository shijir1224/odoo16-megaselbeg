# -*- coding: utf-8 -*-
##############################################################################
#

{
    "name" : "MW Stock Ageing Report",
    "version" : "1.0",
    "author" : "Manahewall LLC",
    "description": """
    Насжилтын тайлан
""",
    "website" : False,
    "category" : "Stock Report",
    "depends" : ['mw_stock'],
    "init": [],
    "data" : [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/stock_view.xml',
        'report/report_ageing_view.xml',
        'report/stock_turn_view.xml',
        'wizard/wizard_view.xml',
        'views/menu_view.xml',
    ],
    "demo_xml": [],
    "active": False,
    "installable": True,
    'license': 'OPL-1',
}