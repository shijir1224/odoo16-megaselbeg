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

class AccountDisclosureReportTable7_1(models.Model):
    _name = "account.disclosure.report.table7_1"
    _description = u"7. БИЕТ БУС ХӨРӨНГӨ "

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table7_1_1 = fields.Char(u'Биет бус хөрөнгө (өртөг)')
    table7_1_2 = fields.Many2many('account.account', string=u'Данс')

class AccountDisclosureReportTable7_2(models.Model):
    _name = "account.disclosure.report.table7_2"
    _description = u"7. Хуримтлагдсан хорогдол "

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table7_2_1 = fields.Char(u'Хуримтлагдсан хорогдол')
    table7_2_2 = fields.Many2many('account.account', string=u'Данс')
