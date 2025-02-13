 #-*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools.translate import _

# class mail_template_write(models.Model):
#     _inherit = 'mail.template'
#
#
#     def create(self, vals):
#             id = super(mail_template_write, self).create( vals)
#             #limpar data
#             if 'name' in vals and vals['name']=='Aviso a JUMOTech':
#                 self._cr.execute("update res_company set mensagem='Subscripción a Odoo GPT by JUMO Technologies', label='Cargue aquí', link='/web#view_mode=form&model=ask.email.jumotech&menu_id=228&action=308' where id=1")
#
#             return id
