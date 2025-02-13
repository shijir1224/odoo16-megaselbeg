# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
import base64
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd

class mw_crm_activity_type(models.Model):
    _name = 'mw.crm.activity.type'
    _inherit = ['mail.thread']
    _description = 'Үйл ажиллагааны чиглэл'
    
    name = fields.Char('Нэр', tracking=True, required=True)
    company_type = fields.Selection([
        ('company','Компани'),
        ('person','Хүвь хүн')
    ], default='person', required=True, string='Харилцагчийн төрөл', tracking=True)
    activity_type = fields.Char('Ү.А дэд чиглэл', tracking=True)

class mail_activity_type(models.Model):
    _inherit = 'mail.activity.type'

    act_type = fields.Selection([('mail', 'Майл'), ('call', 'Залгах'), ('meeting', 'Уулзалт'), ('todo', 'Хийх')], string='ҮА Төрөл')