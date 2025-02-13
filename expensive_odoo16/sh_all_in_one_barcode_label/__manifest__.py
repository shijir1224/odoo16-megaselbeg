# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    'name': 'Dynamic Product Labels | All In One Barcode Labels | Product Template Barcode Label',
    'author': 'Softhealer Technologies',
    'website': "https://www.softhealer.com",
    "support": "support@softhealer.com",
    'version': '16.0.6',
    "license": "OPL-1",
    'category': 'Productivity',
    'summary': "Product Custom Labels Custom Product Label Template Print sale barcode label purchase barcode label Dynamic Product Page Label invoice barcode label Product Barcode Label stock barcode Label With Fields Barcode Labels for Product Template Odoo",
    "description":  """ Every company has its label standard. so our module helps to make dynamic product labels. We provide 3 predefined templates for product labels. You can generate dynamic product label templates. You can add customizable extra fields in the product label. We provide label print options for the products, sales/quotation, purchase/request for quotation, inventory/incoming order/delivery order/internal transfer, invoice/bill/credit note/debit note. Bulk print supported. Print barcodes and QR codes for lot and serial numbers, along with quantities. Display strike prices. Include text, images, and logos. Choose customer and product details. You can print lot/serial numbers, display strike prices, print pricelists, view sale and cost prices with tax, and configure barcode quantity printing. Cheers!""" ,

    'depends': [
        'sale_management',
        'purchase',
        'stock',
    ],
    'data': [
        'security/sh_dynamic_lable_print_security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/product_views.xml',
        'views/sh_dynamic_template_views.xml',
        'data/sh_dynamic_template_data.xml',
        'wizard/sh_product_lable_print_views.xml',
        'report/barcode_report_views.xml',
    ],
    "images": ["static/description/background.png"],
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": "35",
    "currency": "EUR"
}
