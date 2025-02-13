# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW MRP',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'MRP',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian MRP',
    'description': "",
    'depends': ['product','stock','mrp','mrp_account','mw_account','branch','mw_stock_account','mw_account_financial_report'],
    'data': [
        'security/mw_mrp_security.xml',
        'security/ir.model.access.csv',
        'views/mrp_view.xml',
        'views/mrp_cost_view.xml',
        'views/mrp_production_import_view.xml',
        'report/mrp_cost_structure_report.xml',
        # 'report/mrp_standart_report_pivot_view.xml'
        'report/account_mrp_report_view.xml',
        'wizard/account_transaction_balance_view.xml',
        'wizard/account_mrp_report_view_wizard_view.xml'
        
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
