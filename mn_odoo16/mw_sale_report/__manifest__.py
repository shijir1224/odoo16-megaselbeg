# -*- coding: utf-8 -*-
{
    "name" : "MW Sale report module",
    "version" : "2.0",
    'license': 'LGPL-3',
    "author" : "Managewall LLC",
    "description": """
        Борлуулалтын тайлан
    """,
    "website" : False,
    "category" : "Report",
    "depends" : ['sale','sale_stock','sales_team', 'mw_sale_return',
                'mw_sales_contract_promotion','mw_sales_master_plan'],
    "init": [],
    "update_xml" : [
        'security/ir.model.access.csv',
        'reports/sale_warehouse_report.xml',
    ],
    "demo_xml": [],
    "auto_install": False,
    "installable": True,
    'application': True,
}
