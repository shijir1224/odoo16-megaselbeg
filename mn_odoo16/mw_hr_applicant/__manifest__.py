{
    'name': 'MW HR APPLICANT',
    'version': '16.0.1.0',
    'license': 'LGPL-3',
    'category': 'MW Human resourse',
    'sequence': 20,
    'author': 'Solongo Managewall LLC',
    'summary': 'Changed by Mongolian HR',
    'description': """Сонгон шалгаруулалтын модуль
                - Орон тоо төлөвлөлт
                    - Сонгон шалгаруулалт -- Бүтэц орон тоо-- Орон тоо төлөвлөлт
                - Хүний нөөцийн захиалга
                    - Сонгон шалгаруулалт -- Бүтэц орон тоо-- Хүний нөөцийн захиалга
                - Нээлттэй ажлын байр
                    - Сонгон шалгаруулалт -- Бүтэц орон тоо-- Нээлттэй ажлын байр
                - Бүх анкет
                    - Сонгон шалгаруулалт  -- Ажилд орох өргөдлүүд -- Бүх анкет
                    """,
    'depends': ['hr','hr_recruitment','mw_hr_additional'],
    'data': [
        # 'wizard/views/rec_report_view.xml',
        'security/hr_security.xml',
        'views/applicant_request_view.xml',
        'views/hr_applicant_view.xml',
        'views/hr_applicant_menu.xml',
        'security/ir.model.access.csv',
        
        
    ],
    'website': 'http://managewall.mn',
    'installable': True,
}