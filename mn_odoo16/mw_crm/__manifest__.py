# -*- coding: utf-8 -*-

{
    'name': 'MW CRM',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Purchase',
    'website': 'http://managewall.mn',
    'author': 'Managewall LLC',
    'description': """
        Main managewall purchase stock""",
    'depends': [
        'crm',
    ],
    'summary': '',
    'data': [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/mw_crm_team_view.xml",
        "views/mw_crm_activity_type_view.xml",
        "views/mw_activity_view.xml",
        "views/mw_crm_view.xml",
        "views/mw_campaign_view.xml",
        "views/mw_feedback_view.xml",
        "views/mw_res_partner_view.xml",
        "views/mw_gratitude_view.xml",
    ],
    'installable': True,
    'application': True,
}
