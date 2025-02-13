# -*- coding: utf-8 -*-
from odoo import fields
from odoo.models import TransientModel


class BaseConfirmWizard(TransientModel):
    _name = 'base.confirm.wizard'
    _description = 'Base confirm wizard'

    res_model = fields.Char('Model', required=True)
    res_id = fields.Integer('ID', required=True)
    message = fields.Char('Message', required=True)
    function_name = fields.Char('Function name', required=True)

    def confirm(self):
        model = self.env[self.res_model].with_context(base_wizard_confirmed=True).browse(self.res_id)
        function = getattr(model, self.function_name)
        return function()
