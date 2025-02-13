# -*- coding: utf-8 -*-

{
    'name': 'Managewall Contract',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 20,
    'category': 'Contract Management',
    'author': 'Managewall Nandinzaya',
    'description': """Гэрээ
        - Гэрээний бүртгэл
        - Гэрээний загвар
        - Тохиргоо
                   """,
    'website': 'http://managewall.mn',
    'depends': ['hr','branch','mw_dynamic_flow'],
    'data': [
        'security/document_security.xml',
        'security/ir.model.access.csv',  
        'views/contract_view.xml',
        'data/contract_document_cron.xml',
    ],
    'installable': True,
    'application': False,
}
