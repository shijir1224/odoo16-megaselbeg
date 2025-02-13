# -*- coding: utf-8 -*-

{
    'name': 'MN Base',
    'version': '12.0.1',
    'license': 'LGPL-3',
    'category': 'Base',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed to meet Mongolian standards',
    'description': "",
    'depends': ['base','stock','account','purchase','hr','mail'],
    'data': [
        'security/mw_base_security.xml',
        'security/ir.model.access.csv',
        'data/currency_download_ir_cron.xml',
        'views/res_partner_inherit_view.xml',
        'views/res_users_view.xml',
        'views/abstract_exsel_report_view.xml',
        'views/res_company_inherit_view.xml',
        'wizard/base_confirm_wizard.xml',
    ],
    'qweb': [
        'static/src/xml/date_picker.xml',
    ],
    'website': 'http://managewall.mn',
    'installable': True,
    # 'auto_install': False,
}
