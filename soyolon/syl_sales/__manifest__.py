# -*- coding: utf-8 -*-

{
    'name': 'Soyolon Sales',
    'version': '1.0',
    'sequence': 31,
    'category': 'Sales',
    'author': 'Bilguudei Managewall LLC',
    'description': """
        """,
    'depends': ['sale','mw_sale','syl_purchase'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sale_price_calculator_view.xml',
        'views/sale_order_view.xml',
        'views/sale_order_pr_create_view.xml',
        'views/sale_plan_view.xml',
        'wizard/wizard_sale_team_report_view.xml',
        'wizard/wizard_sale_report_view.xml',
    ],
    'installable': True,
    'application': False,
    'qweb': [],
}
