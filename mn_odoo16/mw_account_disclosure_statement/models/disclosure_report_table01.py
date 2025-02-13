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


class AccountDisclosureReportTable1(models.Model):
    _name = "account.disclosure.report.table1"
    _description = u"1.МӨНГӨ БА ТҮҮНТЭЙ АДИЛТГАХ ХӨРӨНГӨ"
    
    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    
    table1_1 = fields.Char(u'Мөнгөн хөрөнгийн зүйлс')
    table1_2 = fields.Many2many('account.account', string=u'Данс')
