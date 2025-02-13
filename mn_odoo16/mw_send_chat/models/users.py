# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    useruud = fields.One2many('res.users', 'partner_id', string='Хэрэглэгчид')

class ResUsers(models.Model):
    # _name = 'res.users'
    _inherit = 'res.users'
    # _inherit = ['res.users', 'mail.thread', 'mail.activity.mixin']

    def get_mail_html(self, html, email=False):
        return html

    def send_chat(self, html, partner_ids, with_mail=False, subject_mail=False, html_mail=False, attachment_ids=[]):
        if not partner_ids:
            raise UserError(u'Мэдэгдэл хүргэх харилцагч байхгүй байна')
        channel_obj = self.env['mail.channel']
        messages = []
        for item in partner_ids:
            usertei = item.useruud
            email = item.email or False
            if email and with_mail:
                if usertei and html_mail:
                    html_mail = html_mail.replace('user_base_id_id',str(usertei[0].id))
                try:
                    vals = {
                        'body_html': self.get_mail_html(html_mail or html, email),
                        'subject': '%s' % (subject_mail or ''),
                        'email_to': email,
                        'auto_delete': False,
                        'state': 'outgoing',
                    }
                    if attachment_ids:
                        # vals['attachment_ids'] = attachment_ids
                        vals['attachment_ids'] = list(set(attachment_ids))
                    mail_id = self.env['mail.mail'].sudo().create(vals)
                    mail_id.sudo().send()
                except ValueError as e:
                    _logger.info('send mail aldaa %s %s %s %s'%(e, str(attachment_ids), email, subject_mail))
                    pass
            if self.env.user.partner_id.id!=item.id:
                channel_ids = channel_obj.search([
                    ('channel_partner_ids', 'in', [item.id])
                    ,('channel_partner_ids', 'in', [self.env.user.partner_id.id])
                    ]).filtered(lambda r: len(r.channel_partner_ids) == 2).ids
                if not channel_ids:
                    channel_ids = channel_obj.sudo().search([
                    ('message_partner_ids', '=', item.id)
                    ,('message_partner_ids', '=', self.env.user.partner_id.id)
                    ]).filtered(lambda r: len(r.message_partner_ids.ids) == [2]).ids
                if not channel_ids:
                    vals = {
                        'channel_type': 'chat',
                        'name': u''+item.name+u', '+self.env.user.name,
                        # 'public': 'private',
                        'channel_partner_ids': [(4, item.id), (4, self.env.user.partner_id.id)],
                        # 'email_send': self.env.context.get('send_email',False)
                    }
                    new_channel = channel_obj.create(vals)
                    notification = _('<div class="o_mail_notification">created <a href="#" class="o_channel_redirect" data-oe-id="%s">#%s</a></div>') % (new_channel.id, new_channel.name,)
                    new_channel.message_post(body=notification, message_type="notification", subtype_xmlid='mail.mt_note')
                    channel_info = new_channel.channel_info()[0]
                    self.env['bus.bus']._sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id), channel_info, {
                        'id': self.id, 
                        'model':'res.users'})
                    channel_ids = [new_channel.id]
                if channel_ids:
                    mail_channel = channel_obj.browse(channel_ids[0])
                    message = mail_channel.message_post(body=html,message_type='comment',subtype_xmlid='mail.mt_comment').with_context(mail_create_nosubscribe=True)
                    messages+=message
        return messages

    def send_emails(self, partners, subject, body, attachment_ids):
        for partner in partners:
            mail_obj = self.env['mail.mail'].sudo().create({
                'email_from': self.env.user.company_id.email,
                'email_to': partner.email,
                'reply_to': self.env.user.email_formatted,
                'subject': subject,
                'body_html': '%s' % body,
                'attachment_ids': attachment_ids
            })
            mail_obj.send()