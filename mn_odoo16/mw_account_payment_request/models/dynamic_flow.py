# -*- coding: utf-8 -*-
from odoo import fields, models

class DynamicFlowLineInherit(models.Model):
    _inherit = 'dynamic.flow.line'
    # Columns
    state_type = fields.Selection(selection_add=[
        ('dep_directors', 'Газрын захирал'),
        ('fin_manager', 'Санхүүгийн менежер'),
        ('gen_account', 'Ерөнхий нягтлан'),
        ('accountant', 'Нягтлан'),
        ('fin_director', 'Санхүү хариуцсан захирал'),
        ('president_ceo', 'Ерөнхийлөгч, эсвэл Гүйцэтгэх захирлын орлогч'),
        ('ceo', ' Гүйцэтгэх захирал'),
        ('computing', 'Тооцоолох'),])

class DynamicFlowInherit(models.Model):
    _inherit = 'dynamic.flow'

    department_ids = fields.Many2many('hr.department','dynamic_flow_payment_rec_rel','flow_id','dep_id', 'Departments')
    desc_temlate = fields.Html(u'Гүйлгээний утга загвар')
