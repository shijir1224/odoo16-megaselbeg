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

class AccountDisclosureReportTable6_1(models.Model):
    _name = "account.disclosure.report.table6_1"
    _description = u"6. ҮНДСЭН ХӨРӨНГӨ "
    
    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table6_1_1 = fields.Char(u'Үндсэн хөрөнгө (өртөг)')
    table6_1_2 = fields.Many2many('account.account', string=u'Данс')

class AccountDisclosureReportTable6_2(models.Model):
    _name = "account.disclosure.report.table6_2"
    _description = u"6. Хуримтлагдсан элэгдэл "

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table6_2_1 = fields.Char(u'Хуримтлагдсан элэгдэл')
    table6_2_2 = fields.Many2many('account.account', string=u'Данс')
