# -*- encoding: utf-8 -*-
##############################################################################
from odoo import api, fields, models, _
from odoo.modules import get_module_resource
from datetime import datetime
import json
import openpyxl
from io import BytesIO
from operator import itemgetter
import time
import base64
from odoo.exceptions import UserError
"""
   Санхүүгийн тайлангийн тодруулга тайлан
"""
    
class AccountDisclosureReportTable8_1(models.Model):
    _name = "account.disclosure.report.table8_1"
    _description = u"8. ӨР ТӨЛБӨР"

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table8_1_1 = fields.Char(u'8.1. Дансны өглөг')
    table8_1_2 = fields.Many2many('account.account', string=u'Данс')
    
class AccountDisclosureReportTable8_2(models.Model):
    _name = "account.disclosure.report.table8_2"
    _description = u"8. ӨР ТӨЛБӨР"

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table8_2_1 = fields.Char(u'8.2 Татварын өр')
    table8_2_2 = fields.Many2one('account.account', string=u'Данс')
    
class AccountDisclosureReportTable8_3(models.Model):
    _name = "account.disclosure.report.table8_3"
    _description = u"8. ӨР ТӨЛБӨР"

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table8_3_1 = fields.Char(u'8.3. Богино хугацаат зээл')
    table8_3_2 = fields.Many2many('account.account', string=u'Данс')
    
class AccountDisclosureReportTable8_4(models.Model):
    _name = "account.disclosure.report.table8_4"
    _description = u"8. ӨР ТӨЛБӨР"

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table8_4_1 = fields.Char(u'8.4. Богино хугацаат нөөц (өр төлбөр)')
    table8_4_2 = fields.Many2many('account.account', string=u'Данс')
    
class AccountDisclosureReportTable8_5(models.Model):
    _name = "account.disclosure.report.table8_5"
    _description = u"8. ӨР ТӨЛБӨР"

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table8_5_1 = fields.Char(u'8.5. Бусад богино хугацаат өр төлбөр')
    table8_5_2 = fields.Many2many('account.account', string=u'Данс')
