# -*- coding: utf-8 -*-

{
    'name': 'MW CRM Call',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'crm',
    'website': 'http://managewall.mn',
    'author': 'Managewall LLC by Odka',
    'description': """
        CRM call""",
    'depends': [
        'crm','mw_crm'
    ],
    'summary': '',
    'data': [
        "security/security.xml",
        "security/ir.model.access.csv",
        # "views/template.xml",
        "views/crm_call_view.xml",
        # "views/crm_call_plan_view.xml",
        "views/menu_view.xml",
    ],
    'assets': {
            'mw_crm_call.assets':
                [
                 'mw_crm_call/static/src/js/time.js'
                ],
            # 'web.assets_qweb': [
            #     "mw_crm_call/static/src/xml/time.xml"
            # ],
        },
    'installable': True,
    'application': True,
}
