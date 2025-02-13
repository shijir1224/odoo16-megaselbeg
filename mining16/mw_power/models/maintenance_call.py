# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import time

class MaintenanceCall(models.Model):
    _inherit = 'maintenance.call'

    state = fields.Selection([
            ('draft', u'Ноорог'), 
            ('open', u'Илгээсэн'),
            ('to_wo', u'WO нээсэн'),
            ('to_eo', u'EO нээсэн'),
            ('to_expense', u'Шаардах үүссэн'),
            ('closed', u'Хаагдсан'),
            ('cancelled', u'Цуцлагдсан'),], 
            default='draft', string=u'Төлөв', track_visibility=True)
    eo_id = fields.Many2one('power.workorder', 'EO', readonly=True)
    call_type = fields.Selection([
            ('technic', u'Техникийн засвар'),
            ('grane_job', u'Краны ажил'),
            ('welding_job', u'Гагнуурын ажил'),
            ('other_repair', u'Аж ахуйн засвар'),
            ('power_call', u'Цахилгааны дуудлага'),
            ('power_exca_portable', u'Цахилгаан экс зөвөр нүүдэл'),
            ], 
            string=u'Ажлын хүсэлтийн төрөл', required=True, default='technic',
        states={'open': [('readonly', True)],'to_wo': [('readonly', True)],'to_eo': [('readonly', True)],'to_expense': [('readonly', True)],'closed': [('readonly', True)]})
        
    def action_create_eo(self):
        if self.eo_id:
            raise UserError('EO үүссэн байна!')
        customer_department_id = self.env['power.selection'].search([('type','=','company_department'),('hr_department_id','=',self.department_id.id)], limit=1).id
        origin = self.name or ''
        vals = {
                'origin': origin,
                'date': self.date_required,
                'shift': self.shift,
                'customer_department_id': customer_department_id,
                'completed_repairs': self.description,
            }
        eo_id = self.env['power.workorder'].create(vals)
        self.eo_id = eo_id.id
        self.state = 'to_eo'
        self.validator_id = self.env.user.id
        str_html = '%s Ажлын хүсэлтээс үүсгэгдлээ '%(self.name)
        html =u'Elecricatl Order </br>%s <span style="color: blue;">%s</span>'% (self.eo_id.get_url(),str_html)
        group_id = self.env.ref( "mw_power.group_power_manager")
        partner_ids = group_id.mapped('users.partner_id')
        group_id = self.env.ref( "mw_power.group_power_dispatcher")
        partner_ids += group_id.mapped('users.partner_id')
        self.env['power.warehouse.config'].send_chat(html, partner_ids)
    
    def action_to_close(self):
        if not self.performance_description:
            raise UserError(_(u'Гүйцэтгэсэн ажлыг оруулна уу!'))  

        # Засварчдын ажлын цагийг шалгах
        if not self.employee_timesheet_lines and not self.workorder_id and self.eo_id:
            raise UserError(_(u'Засварчны цагийг оруулна уу! Call')) 
        else:
            for line in self.employee_timesheet_lines:
                if not line.date_start or not line.date_end:
                    raise UserError(_(u'Засварчны эхэлсэн, дууссан цагийг оруулна уу!')) 

        self.date_close = datetime.now()
        self.state = 'closed'
        self.close_user_id = self.env.user.id