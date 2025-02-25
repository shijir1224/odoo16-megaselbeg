# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Inter Company Module for Sale/Purchase Orders and Invoices',
    'version': '1.1',
    'license': 'LGPL-3',
    'summary': 'Intercompany SO/PO/INV rules',
    'category': 'Productivity',
    'description': ''' Module for synchronization of Documents between several companies. For example, this allow you to have a Sales Order created automatically when a Purchase Order is validated with another company of the system as vendor, and inversely.

    Supported documents are SO, PO and invoices/credit notes.
''',
    'depends': [
        'sale_management',
        'purchase_stock',
        'sale_stock',
        'branch',
        'mw_stock',
        'mw_purchase_request'
    ],
    'data': [
        'views/inter_company_so_po_view.xml',
        'views/res_config_settings_views.xml',
        'views/stock_warehouse_views.xml',
        'views/stock_picking_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'wizard/comparison_report_view.xml',
        'wizard/invoice_comparison_report_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
