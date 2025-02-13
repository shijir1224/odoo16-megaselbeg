# -*- coding: utf-8 -*-
##############################################################################
#

{
    "name" : "Stock's detailed report module GOVERMENT",
    "version" : "1.0",
    "author" : "Manahewall LLC by amaraa",
    "description": """
    Бараа материалын дэлгэрэнгүй бүртгэлийн товчоо (дансаар)
    Барааны эхний үлдэгдэл, орлого, зарлага, эцсийн үлдэгдлийг тоо хэмжээ, өртгийг дансаар бүлэглэж гаргана.
""",
    "website" : False,
    "category" : "Stock Report",
    "depends" : ['mw_stock_product_report'],
    "init": [],
    "data" : [
        'wizard/product_detailed_income_expense_wizard_view.xml',
    ],
    "demo_xml": [],
    "auto_install": False,
    "installable": True,
    'license': 'OPL-1',
}