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

class AccountDisclosureReportTable11_1(models.Model):
    _name = "account.disclosure.report.table11_1"
    _description = u"11. ЗАРДАЛ"
    
    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table11_1_1 = fields.Char(u'Борлуулалт маркетингийн болон ерөнхий удирдлагын зардал')
    table11_1_2 = fields.Many2many('account.account', string=u'Данс /Борлуулалт, маркетинг/')
#     table11_1_3 = fields.Many2many('account.account', string=u'Данс /Ерөнхий, удирдлага/')


class AccountDisclosureReportTable11_2(models.Model):
    _name = "account.disclosure.report.table11_2"
    _description = u"11. ЗАРДАЛ"

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table11_2_1 = fields.Char(u'Бусад зардал')
    table11_2_2 = fields.Many2many('account.account', string=u'Данс')

