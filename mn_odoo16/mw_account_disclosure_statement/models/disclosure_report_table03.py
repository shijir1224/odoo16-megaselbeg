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

class AccountDisclosureReportTable3(models.Model):
    _name = "account.disclosure.report.table3"
    _description = u"3. БУСАД САНХҮҮГИЙН ХӨРӨНГӨ"

    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table3_1 = fields.Char(u'Төрөл')
    table3_2 = fields.Many2many('account.account', string=u'Бусад талуудаас авах авлага')
