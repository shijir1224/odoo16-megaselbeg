# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PaymentRequest(models.Model):
    _inherit = 'payment.request'

    mission_id = fields.Many2one('hr.mission', string='Томилолт', readonly=True)

class HrMission(models.Model):
    _inherit = 'hr.mission'

    request_id = fields.Many2one('payment.request', string='Төлбөрийн хүсэлт',readonly=True)
    # amount = fields.Float(string='Мөнгөн дүн')

    def action_next_stage(self):
        res = super(HrMission, self).action_next_stage()
        day = timedelta(days=5)
        for obj in self:
            if obj.state_type == 'done':
                payment_pool=self.env['payment.request']
                payment_narration=self.env['payment.request.narration'].search([('is_mission','=','True')])
                payment_flow = self.env['dynamic.flow'].search([('model_id.model', '=', 'payment.request')], order='sequence',limit=1)
                data_id = payment_pool.create({
                    'narration_id': payment_narration.id,
                    'description' : obj.name,
                    # 'user_id' : obj.employee_id.user_id.id,
                    'create_partner_id' : obj.employee_id.user_partner_id.id,
                    'department_id' : obj.employee_id.department_id.id,
                    'amount' : obj.total,
                    'flow_id': payment_flow.id,
                    'mission_id': obj.id
                })
                self.request_id = data_id.id
            # else: 
            #     raise UserError('Төлбөрийн хүсэлт үүссэн байна.')
        return res