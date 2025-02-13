# -*- coding: utf-8 -*-
########################################################################################
#                       ЭЗЭМШИГЧИЙН ЭРХ (C) "ДАТАБЭЙНК" ХХК                            #
#                                                                                      #
#    БҮХ ЭРХ ХУУЛИАР ХАМГААЛАГДСАН БОЛНО. ЭНЭХҮҮ ПРОГРАМ НЬ "ДАТАБЭЙНК" ХХК-ИЙН ӨМЧ    #
#     БӨГӨӨД ГАГЦХҮҮ "ДАТАБЭЙНК" ХХК-ИЙН ХЭРЭГЦЭЭНД ХЭРЭГЛЭГДЭХ БОЛНО. ПРОГРАММЫН      #
#       ЯМАР Ч ХЭСГИЙГ "ДАТАБЭЙНК" ХХК-ИЙН УРЬДЧИЛАН ОЛГОСОН ЗӨВШӨӨРӨЛГҮЙГЭЭР          #
#             ХУУЛБАРЛАХ ЭСВЭЛ БУСДАД ЗАДРУУЛАХ, ТҮГЭЭХИЙГ ХОРИГЛОНО.                  #
#                                                                                      #
#                              "ДАТАБЭЙНК" ХХК-ИЙН ӨМЧ                                 #
#                                                                                      #
#  ----------------------------------------------------------------------------------  #
#                                                                                      #
#                     DATABANK LLC CONFIDENTIAL AND PROPRIETARY                        #
#                                                                                      #
#                     COPYRIGHT (C) DATABANK LLC since 2017                            #
#                                                                                      #
#      ALL RIGHTS RESERVED BY DATABANK LLC.  THIS PROGRAM MUST BE                      #
#    USED SOLELY FOR THE PURPOSE FOR WHICH IT WAS FURNISHED BY DATABANK LLC.           #
#   NO PART OF THIS PROGRAM MAY BE REPRODUCED OR DISCLOSED TO OTHERS, IN ANY           #
#        FORM, WITHOUT THE PRIOR WRITTEN PERMISSION OF DATABANK LLC.                   #
#                                                                                      #
#     USE OF COPYRIGHT NOTICE DOES NOT EVIDENCE PUBLICATION OF THE PROGRAM.            #
#                                                                                      #
#                     DATABANK LLC CONFIDENTIAL AND PROPRIETARY                        #
#                                                                                      #
########################################################################################

{
    'name': 'POS Go Conn payment',
    'version': '1.0.1',
    'author': 'DATABANK LLC',
    'website': 'https://databank.mn/',
    'images': ["static/img/banner.png"],
    'category': 'Sales/Point of Sale',
    'sequence': 7,
    'description': 'Integrate your POS with an PINPAD payment method.',
    'summary': ' Odoo ERP системийн ПОС-ийн програм дээр Databank PINPAD төхөөрөмжөөр бэлэн бус гүйлгээ хийх боломжтой болно',
    'data': [
        'data/payment_method_data.xml',
        'views/res_config_settings_views.xml',
        'views/pos_payment_method_inherit_view.xml',
    ],
    'depends': ['point_of_sale'],
    'installable': True,
    'auto_install': False,
    'assets': {
        'point_of_sale.assets': [
            'dtb_pos_go_conn_payment/static/src/js/models.js',
            'dtb_pos_go_conn_payment/static/src/js/payment.js',
            'dtb_pos_go_conn_payment/static/src/js/PaymentScreen.js',
        ],
    },
    'license': 'GPL-3',
    'price': 0, 
    'currency': 'EUR',
}
