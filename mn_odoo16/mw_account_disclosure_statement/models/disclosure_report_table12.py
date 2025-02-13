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

class AccountDisclosureReportTable12(models.Model):
    _name = "account.disclosure.report.table12"
    _description = u"12. ОРЛОГЫН ТАТВАРЫН ЗАРДАЛ"
    
    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table12_1 = fields.Char(u'Үзүүлэлт')
    table12_2 = fields.Many2many('account.account', string=u'Данс')
