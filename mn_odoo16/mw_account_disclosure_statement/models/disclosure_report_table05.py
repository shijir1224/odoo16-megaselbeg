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
    
class AccountDisclosureReportTable5(models.Model):
    _name = "account.disclosure.report.table5"
    _description = u"5. УРЬДЧИЛЖ ТӨЛСӨН ЗАРДАЛ/ТООЦОО"
    
    main_id = fields.Many2one('account.disclosure.report.main', u'Санхүүгийн тайлангийн тодруулга үндсэн тайлан')
    table5_1 = fields.Char(u'Төрөл')
    table5_2 = fields.Many2many('account.account', string=u'Данс')
