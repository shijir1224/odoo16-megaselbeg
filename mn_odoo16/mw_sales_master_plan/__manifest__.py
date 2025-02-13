# -*- coding: utf-8 -*-

{
    'name': 'Sale plan & Dashboard',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Sales Management',
    'author': 'Managewall LLC',
    'description': """
        SaleOrder and Sales plan and Dashboard analysing """,
    'depends': ['base','sale','sale_stock','branch'],
    'summary': 'SaleOrder + Sales Plan, Dashboards',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'views/sales_master_plan_view.xml',
        'views/partner_special_product_plan_view.xml',

        'report/sale_plan_pivot_report_view.xml',
        'report/sale_pivot_report_view.xml',
        
        'wizard/wizard_sales_plan_report_view.xml',
        'wizard/wizard_sales_report_view.xml',

        # 'wizard/wizard_sales_excel_report_view.xml',
       
        # 'views/sales_plan_dashboard_view.xml',
        # 'views/widget_path.xml',
        'views/menu_view.xml',
    ],
    'installable': True,
    'application': True,
    'qweb': ['static/xml/*.xml'],
}
