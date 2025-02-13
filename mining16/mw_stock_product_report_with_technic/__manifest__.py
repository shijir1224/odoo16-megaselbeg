# -*- coding: utf-8 -*-
##############################################################################
#

{
    "name" : "Stock's detailed report module TECHNIC",
    "version" : "1.0",
    "author" : "Manahewall LLC by amaraa",
    "description": """
    Бараа материалын дэлгэрэнгүй бүртгэлийн товчоо (дансаар)
    Барааны эхний үлдэгдэл, орлого, зарлага, эцсийн үлдэгдлийг тоо хэмжээ, өртгийг дансаар бүлэглэж гаргана.
""",
    "website" : False,
    "category" : "Stock Report",
    "depends" : ['mw_stock_product_report','mw_technic_equipment','mw_technic_maintenance','mw_stock_account'],
    "init": [],
    "data" : [
        'views/report_view.xml',
    ],
    "demo_xml": [],
    "active": False,
    "installable": True,
}