# noinspection PyStatementEffect
{
    'name': 'Easy PDF creator',
    'version': '1.3',
    'license': 'LGPL-3',
    'author': 'Managewall by amaraa',
    'category': 'Tools',
    'summary': "Easy PDF report create end direct print",
    'description': """
        Easy PDF template creator, No development, Quick print(no download) """,
    'images': [
        'static/description/icon.jpg',
    ],
    'depends': ['base','web','web_editor'],
    'data': [
        'security/ir.model.access.csv',
        # 'xml/templates.xml',
        'view/pdf_template_generator_view.xml',
        'view/menu_view.xml',
    ],
    'installable': True,
    'application': True,
    'assets': {
        # Front_end  болон Back_end хамаатайн байна Backend нь шууд нийтдээ уншиж байна 
        # Front_end нь тухайн модуль дээрээ уншиж байх шиг байна
        # 'web.assets_common': [
        'web.assets_frontend': [
            'easy_pdf_creator/static/css/print_template.css', 
            'easy_pdf_creator/static/css/base.css',
        ],
        'web.assets_backend': [
            'easy_pdf_creator/static/css/base.css',
            'easy_pdf_creator/static/css/froala_style.css',
            # 'easy_pdf_creator/static/src/xml/easy_print.xml',
            'easy_pdf_creator/static/js/easy_print.js',
        ],
        'web.assets_qweb': [
            # 'easy_pdf_creator/static/src/xml/easy_print.xml',
        ],
    }
}
