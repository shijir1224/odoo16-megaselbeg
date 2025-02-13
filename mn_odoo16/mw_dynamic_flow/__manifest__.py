# -*- coding: utf-8 -*-

{
    'name': 'MW Dynamic Flow',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Flow',
    'website': 'http://managewall.mn',
    'author': 'Managewall LLC',
    'description': """
        Dynamic work flow""",
    'depends': ['base','product','branch','hr','mw_send_chat'],
    'summary': '',
    'data': [
            "security/flow_security.xml",
            "security/ir.model.access.csv",
            "views/success.xml",
            "views/dynamic_flow_view.xml",
    ],
    'installable': True,
    'application': False,
    'icon': '/mw_dynamic_flow/static/img/icon.png',
}
