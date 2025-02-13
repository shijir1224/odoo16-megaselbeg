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

class AccountDisclosureReportTable9_1(models.Model):
    _name = "account.disclosure.report.table9_1"
    _description = u"9. БОРЛУУЛАЛТЫН ОРЛОГО БОЛОН БОРЛУУЛАЛТЫН ӨРТӨГ"
    
    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table9_1_1 = fields.Char(u'Үзүүлэлт')
    table9_1_2 = fields.Many2many('account.account', string=u'Данс')


class AccountDisclosureReportTable9_2(models.Model):
    _name = "account.disclosure.report.table9_2"
    _description = u"9. БОРЛУУЛАЛТЫН ОРЛОГО БОЛОН БОРЛУУЛАЛТЫН ӨРТӨГ"

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table9_2_1 = fields.Char(u'Үзүүлэлт')
    table9_2_2 = fields.Many2many('account.account', string=u'Данс')


class AccountDisclosureReportTable9_3(models.Model):
    _name = "account.disclosure.report.table9_3"
    _description = u"9. БОРЛУУЛАЛТЫН ОРЛОГО БОЛОН БОРЛУУЛАЛТЫН ӨРТӨГ"

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table9_3_1 = fields.Char(u'Үзүүлэлт')
    table9_3_2 = fields.Many2many('account.account', string=u'Данс')


class AccountDisclosureReportTable9_4(models.Model):
    _name = "account.disclosure.report.table9_4"
    _description = u"9. БОРЛУУЛАЛТЫН ОРЛОГО БОЛОН БОРЛУУЛАЛТЫН ӨРТӨГ"

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table9_4_1 = fields.Char(u'Үзүүлэлт')
    table9_4_2 = fields.Many2many('account.account', string=u'Данс')


class AccountDisclosureReportTable9_5(models.Model):
    _name = "account.disclosure.report.table9_5"
    _description = u"9. БОРЛУУЛАЛТЫН ОРЛОГО БОЛОН БОРЛУУЛАЛТЫН ӨРТӨГ"

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table9_5_1 = fields.Char(u'Үзүүлэлт')
    table9_5_2 = fields.Many2many('account.account', string=u'Данс')

