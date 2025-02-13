# -*- coding: utf-8 -*-

{
    'name': 'MW CRM Blacklist',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Purchase',
    'website': 'http://managewall.mn',
    'author': 'Managewall LLC',
    'description': """
        Main managewall purchase stock""",
    'depends': [
        'crm','contacts'
    ],
    'summary': '',
    'data': [
        "security/ir.model.access.csv",
        "views/mw_res_partner_view.xml",
    ],
    'installable': True,
    'application': True,
}
