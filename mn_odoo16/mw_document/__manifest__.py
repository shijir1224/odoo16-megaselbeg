{
    'name': 'MW document',
    'version': '16.0.1.0',
    'license': 'LGPL-3',
    'sequence': 21,
    'category': 'Document Management',
    'author': 'Managewall LLC',
    'description': """Баримт бичиг модуль
                - Ирсэн албан бичиг
                    - Баримт бичиг -- Албан бичиг -- Ирсэн албан бичиг
                - Явуулсан албан бичиг
                    - Баримт бичиг -- Албан бичиг -- Явуулсан албан бичиг
                - Өргөдөл гомдол
                    - Баримт бичиг -- Өргөдөл гомдол
                    """,
    'depends': ['hr', 'branch', 'mw_hr'],
    'data': [
        'security/security_doc.xml',
        'security/ir.model.access.csv',
        'views/doc_view.xml',
        'views/minute_view.xml',
        'views/task_view.xml',
        'views/complaint_view.xml',
        'views/document_print.xml'
    ],
    'installable': True
}
