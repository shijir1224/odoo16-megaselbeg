# -*- coding: utf-8 -*-

{
    'name': 'MW PoDDon',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Payment',
    'website': 'http://managewall.mn',
    'author': 'Managewall LLC by Odka',
    'description': """
        Төлбөрийн хүсэлт Подон""",
    'depends': [
        'stock',
        'mw_stock',
        'mw_stock_moves',
        'mw_account_payment_request',
    ],
    'summary': '',
    'data': [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/mw_podon_view.xml",
        "views/mw_podon_line_in_use_view.xml",
        "views/mw_podon_line_transfer_view.xml",
        "views/stock_picking_view.xml",
        "views/menu_item.xml",
    ],
    'icon': '/mw_podon/static/img/podon.png',
    'installable': True,
    'application': True,
}