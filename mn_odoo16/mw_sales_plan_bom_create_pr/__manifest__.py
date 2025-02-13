# -*- coding: utf-8 -*-

{
    'name': 'Pr Create from Sale Plan by bom product',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Sales Management',
    'author': 'Managewall Amaraa',
    'description': """
        SaleOrder and Sales plan and Dashboard analysing """,
    'depends': ['mw_sales_master_plan','mw_purchase_request','mrp'],
    'summary': 'SaleOrder + Sales Plan, Dashboards',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sale_plan_pr_view.xml',
        'report/sale_plan_pr_report_view.xml',
    ],
    'installable': True,
    'application': True,
    'qweb': ['static/xml/*.xml'],
}
