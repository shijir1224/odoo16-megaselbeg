# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from datetime import datetime, timedelta

class crm_stage_history(models.Model):
    _name = 'crm.stage.history'
    _description = u'CRM stage түүх'
    _order = 'date desc'

    lead_id = fields.Many2one('crm.lead','Lead', ondelete='cascade')
    user_id = fields.Many2one('res.users', 'Өөрчилсөн Хэрэглэгч')
    date = fields.Datetime('Огноо', default=fields.Datetime.now)
    stage_id = fields.Many2one('crm.stage', 'Төлөв')
    spend_time = fields.Float(string='Зарцуулсан цаг', compute='_compute_spend_time', readonly=True, digits=(16,2))
    spend_day= fields.Float(string='Зарцуулсан хоног', compute='_compute_spend_time', readonly=True, digits=(16,0))

    @api.depends('date','lead_id')
    def _compute_spend_time(self):
        for obj in self:
            domains = []
            if obj.lead_id:
                domains = [('lead_id','=',obj.lead_id.id),('id','!=',obj.id),('date','<',obj.date)]
            if domains and isinstance(obj.id, int):
                ll = self.env['crm.stage.history'].search(domains, order='date desc', limit=1)
                if ll:
                    diff_date = obj.date-ll.date
                    secs = diff_date.total_seconds()
                    obj.spend_time = secs/3600
                    obj.spend_day = diff_date.days
                else:
                    obj.spend_time = 0
                    obj.spend_day = 0
            else:
                obj.spend_time = 0
                obj.spend_day = 0
    
    def create_history(self, stage_id, lead_id):
        self.env['crm.stage.history'].create({
            'lead_id': lead_id.id,
            'user_id': self.env.user.id,
            'date': datetime.now(),
            'stage_id': stage_id
            })

class crm_stage(models.Model):
    _inherit = 'crm.stage'
    
    anhaar_honog_dood = fields.Integer('Анхааруулах хоног доод')
    anhaar_honog_deed = fields.Integer('Анхааруулах хоног дээд')
    