# -*- coding: utf-8 -*-

{
    'name': 'MW Purchase Report',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Purchase',
    'website': 'http://managewall.mn',
    'author': 'Managewall LLC',
    'description': """
        Худалдан авалтын тайлангууд""",
    'depends': ['purchase','mw_purchase'],
    'summary': '',
    'data': [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/purchase_report_view.xml",
        "views/menu_view.xml",
    ],
    'installable': True,
    'application': False,
}
