# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import fields, models, api, _
from odoo.tools.translate import _
from odoo.http import request

from odoo import http, SUPERUSER_ID


class ask_email_jumotech(models.Model):
    _name = 'ask.email.jumotech'
    _description = 'Ask Email Jumotech'


    email = fields.Char('Email')
    mensagem = fields.Text('Mensagem')
    state = fields.Selection([('choose','choose'),('get', 'get'),],'Estado', default ='choose' )

    def action_send_email(self):
        template = False
        template = self.env.ref('odoo_chatgpt.avisasr_oc_email')

        mensagem='Gracias por su solicitud. En breve le enviaremos los accesos.'
        mensagem_2='La solicitud ha fallado. Póngase en contacto con Jumotech en jojeda@jumotech.com.'

        try:
            template.send_mail(self.id, force_send=False, raise_exception=True)
            self.write({'state':'get', 'mensagem':mensagem})

            return {
                'name': 'Jumotech Certifica',
                'view_mode': 'form',
                'res_model': 'ask.email.jumotech',
                'type': 'ir.actions.act_window',
                'res_id':self.id,
                'target': 'new',
            }
        except:
            self.write({'state':'get', 'mensagem':mensagem_2})
            return {
                'name': 'Jumotech Certifica',
                'view_mode': 'form',
                'res_model': 'ask.email.jumotech',
                'type': 'ir.actions.act_window',
                'res_id':self.id,
                'target': 'new',
            }

        return {
            'name': 'Jumotech Certifica',
            'view_mode': 'form',
            'res_model': 'ask.email.jumotech',
            'type': 'ir.actions.act_window',
            'res_id':self.id,
            'target': 'new',
        }
