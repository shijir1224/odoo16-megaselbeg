# -*- coding: utf-8 -*-

{
    'name': 'MW Purchase request with equipment',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Purchase',
    'website': 'http://manangewall.mn',
    'author': 'Managewall LLC',
    'description': """
        Product request to purchase order""",
    'depends': ['mw_purchase_request','mw_purchase_request_technic','mw_factory_equipment','mw_dynamic_flow'],
    'summary': '',
    'data': [
            "views/purchase_request_view.xml",
            "views/dynamic_view.xml",
    ],
    'installable': True,
    'application': False,

}
