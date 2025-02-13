{
    'name': 'MW HR APPLICANT IMPORT',
    'version': '16.0.1.0',
    'license': 'LGPL-3',
    'category': 'MW Human resourse',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian HR',
    'description': """Хүний нөөцийн модуль
                - Анкет импортлох
                    - Сонгон шалгаруулалт -- Бүтэц орон тоо --Анкет импортлох
                    """,
    'depends': ['hr','hr_recruitment','mw_hr','mw_hr_applicant'],
    'data': [
        'security/ir.model.access.csv',
        'views/applicant_import_view.xml',
    ],
    'website': 'http://managewall.mn',
    'installable': True,
}