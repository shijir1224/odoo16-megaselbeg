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

class AccountDisclosureReportTable10(models.Model):
    _name = "account.disclosure.report.table10"
    _description = u"10. БУСАД ОРЛОГО, ОЛЗ (ГАРЗ), АШИГ (АЛДАГДАЛ)"
    
    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table10_1 = fields.Char(u'Бусад орлого')
    table10_2 = fields.Many2many('account.account', string=u'Данс')
