# -*- coding: utf-8 -*-

from odoo import api, models, fields


class TechnicEquipmentSetting(models.Model):
    _inherit = 'technic.equipment.setting'

    drill_product_id = fields.Many2one('product.product', 'Өрмийн бүтээлийн бараа', domain="[('type', '=', 'service')]")

class WizardCreateStoppedTechnicPlan(models.TransientModel):
    _inherit = 'wizard.create.stopped.technic.plan'

    is_cause = fields.Boolean('Уул дээр удаан хугацааны зогсолт үүсгэх', default=True)
    cause_id = fields.Many2one('mining.motohours.cause','Cause' , domain="[('is_repair','=',True)]")
    repair_system_id = fields.Many2one('maintenance.damaged.type', string='Зогссон систем', domain="[('parent_id','=',False)]")

    def create_plans(self):
        res = super(WizardCreateStoppedTechnicPlan, self).create_plans()

        if self.date_start <= self.date_end and self.is_cause and self.cause_id and self.repair_system_id and self.technic_id:
            obj = self.env['mining.default.hour']
            obj.create({
                'start_date': self.date_start,
                'end_date': self.date_end,
                'technic_id': self.technic_id.id,
                'cause_id': self.cause_id.id,
                'repair_system_id': self.repair_system_id.id,
            })
        return res