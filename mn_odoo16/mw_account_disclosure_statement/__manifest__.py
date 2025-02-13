# -*- coding: utf-8 -*-
##############################################################################
#
#    Managewall LLC, Enterprise Management Solution    
#    Copyright (C) 2013-2018 managewall Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#
#    Email : info@asterisk-tech.mn
#    Phone : 976 + 99081691
##############################################################################

{
    'name': 'Mongolian Accounting Disclosure Reports',
    'version': '1.0',
    'depends': ['mw_account', 'mw_account_period'],
    'author': "Managewakk LLC",
    'website': 'http://managewall.mn',
    'category': 'Mongolian Modules',
    'description': """Санхүүгийн тайлангийн тодруулга тайлан""",
    'data': [
        'views/account_disclosure_report_view.xml',
        'views/account_disclosure_view.xml',
        'security/ir.model.access.csv',
    ],
    "auto_install": False,
    "installable": True,
}
