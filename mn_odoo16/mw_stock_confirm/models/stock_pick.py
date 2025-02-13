# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules, _
from odoo.exceptions import UserError,ValidationError

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    def _default_internal_approve(self):
        if self._context.get('default_internal_approve', False):
            return True
        return False

    internal_approve = fields.Boolean(string='Бараа явуулахыг зөвшөөрөх', copy=False, default=_default_internal_approve, tracking=True)

    @api.onchange('internal_approve')
    def onchange_internal_approve(self):
        if (self.move_line_ids or self.move_ids) and self.state and self.state not in ['done'] and self.env.user.id not in self.location_id.set_warehouse_id.done_user_ids.ids and self.picking_type_id.code=='internal':
            raise UserError(u'%s Та гарч байгаа агуулахын БАТЛАХ хэрэглэгч биш байна!!!!'%(self.location_id.display_name))
        # self.send_chat_picking_loc_dest()

    def get_link_picking_tag(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_id = self.env['ir.model.data'].check_object_reference('stock', 'action_picking_tree_all')[1]
        a_name = '<a target="_blank" href="%s/web#id=%s&action=%s&model=stock.picking&view_type=form">%s</a>'%(base_url,self.id,action_id,self.name)
        return a_name
        
    def send_chat_picking_loc(self):
        p_ids = self.location_id.set_warehouse_id.done_user_ids.mapped('partner_id')
        if p_ids:
            a_name = self.get_link_picking_tag()
            html = '%s Дугаартай Дотоод Хөдөлгөөн Зөвшөөрнө үү.'%(a_name)
            self.send_chat(html, p_ids)

    def send_chat_picking_loc_dest(self):
        p_ids = self.location_dest_id.set_warehouse_id.done_user_ids.mapped('partner_id')
        if p_ids:
            a_name = self.get_link_picking_tag()
            html = '%s Дугаартай Дотоод Хөдөлгөөн ЗӨВШӨӨРӨВ.'%(a_name)
            self.send_chat(html, p_ids)

    # def action_confirm(self):
    #     res = super(StockPicking, self).action_confirm()
    #     for item in self:
    #         if item.picking_type_id.code=='internal' and self.env.user.id not in self.location_id.set_warehouse_id.done_user_ids.ids:
    #             item.send_chat_picking_loc()
    #     return res

    def action_to_draft(self):
        res = super(StockPicking, self).action_to_draft()
        for item in self:
            if item.internal_approve:
                item.internal_approve = False
        return res
    
    def button_validate(self):
        for item in self:
            if item.picking_type_id.code == 'internal' and not item.internal_approve:
                raise UserError(u'%s Гарч буй агуулахын Хэрэглэгч зөвшөөрөөгүй байна!!!!' % item.display_name)
        return super(StockPicking, self).button_validate()
        # if res is True:
        #     for obj in self:
        #         if obj.sale_id:
        #             if obj.location_dest_id.usage == 'customer':
        #                 so_picking_date=obj.date_done and obj.date_done or fields.Date.context_today(self)
        #                 invoice_id = obj.sale_id.with_context(so_picking_date=so_picking_date,so_picking_id=obj.id)._create_invoices()
        #                 invoice_id.action_post()
        #             # done_pickings = obj.sale_id.picking_ids.filtered(lambda l: l.race_id and l.state == 'done')
        #             # for done_picking in done_pickings:
        #             #     done_picking.race_id.state = 'done'
        return res

    def send_chat(self, html, partner_ids):
        if not partner_ids:
            if self.type=='none':
                return True
            raise UserError(u'Мэдэгдэл хүргэх харилцагч байхгүй байна')
        channel_obj = self.env['mail.channel']
        for item in partner_ids:
            if self.env.user.partner_id.id!=item.id:
                channel_ids = channel_obj.search([
                    ('starred_partner_ids', 'in', [item.id])
                    ,('starred_partner_ids', 'in', [self.env.user.partner_id.id])
                    ]).filtered(lambda r: len(r.channel_partner_ids) == 2).ids
                if not channel_ids:
                    vals = {
                        'channel_type': 'chat', 
                        'name': u''+item.name+u', '+self.env.user.name, 
                        'public': 'private', 
                        'starred_partner_ids': [(4, item.id), (4, self.env.user.partner_id.id)], 
                        #'email_send': False
                    }
                    new_channel = channel_obj.create(vals)
                    notification = _('<div class="o_mail_notification">created <a href="#" class="o_channel_redirect" data-oe-id="%s">#%s</a></div>') % (new_channel.id, new_channel.name,)
                    new_channel.message_post(body=notification, message_type="notification", subtype_xmlid='mail.mt_note')
                    channel_info = new_channel.channel_info()[0]
                    self.env['bus.bus']._sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id), channel_info, {
                        'id': self.id, 
                        'model':'stock.picking'})
                    channel_ids = [new_channel.id]

                self.env['mail.message'].create({
                        'message_type': 'comment', 
                        'subtype_id': 1,
                        'body': html,
                        'channel_ids':  [(6, 0, channel_ids),]
                        })
                        
    # def send_chat(self, html, partner_ids, with_mail=False, subject_mail=False, html_mail=False, attachment_ids=[]):
    #     if not partner_ids:
    #         raise UserError(u'Мэдэгдэл хүргэх харилцагч байхгүй байна')
    #     channel_obj = self.env['mail.channel']
    #     messages = []
    #     for item in partner_ids:
    #         usertei = item.useruud
    #         email = item.email or False
    #         if email and with_mail:
    #             if usertei and html_mail:
    #                 html_mail = html_mail.replace('user_base_id_id',str(usertei[0].id))
    #             try:
    #                 vals = {
    #                     'body_html': self.get_mail_html(html_mail or html, email),
    #                     'subject': '%s' % (subject_mail or ''),
    #                     'email_to': email,
    #                     'auto_delete': False,
    #                     'state': 'outgoing',
    #                 }
    #                 if attachment_ids:
    #                     # vals['attachment_ids'] = attachment_ids
    #                     vals['attachment_ids'] = list(set(attachment_ids))
    #                 mail_id = self.env['mail.mail'].sudo().create(vals)
    #                 mail_id.sudo().send()
    #             except ValueError as e:
    #                 _logger.info('send mail aldaa %s %s %s %s'%(e, str(attachment_ids), email, subject_mail))
    #                 pass
    #         if self.env.user.partner_id.id!=item.id:
    #             channel_ids = channel_obj.search([
    #                 ('channel_partner_ids', 'in', [item.id])
    #                 ,('channel_partner_ids', 'in', [self.env.user.partner_id.id])
    #                 ]).filtered(lambda r: len(r.channel_partner_ids) == 2).ids
    #             if not channel_ids:
    #                 channel_ids = channel_obj.sudo().search([
    #                 ('channel_last_seen_partner_ids.partner_id', '=', item.id)
    #                 ,('channel_last_seen_partner_ids.partner_id', '=', self.env.user.partner_id.id)
    #                 ]).filtered(lambda r: len(r.channel_last_seen_partner_ids) == 2).ids
    #             if not channel_ids:
    #                 vals = {
    #                     'channel_type': 'chat',
    #                     'name': u''+item.name+u', '+self.env.user.name,
    #                     'public': 'private',
    #                     'channel_partner_ids': [(4, item.id), (4, self.env.user.partner_id.id)],
    #                     # 'email_send': self.env.context.get('send_email',False)
    #                 }
    #                 new_channel = channel_obj.create(vals)
    #                 notification = _('<div class="o_mail_notification">created <a href="#" class="o_channel_redirect" data-oe-id="%s">#%s</a></div>') % (new_channel.id, new_channel.name,)
    #                 new_channel.message_post(body=notification, message_type="notification", subtype_xmlid='mail.mt_note')
    #                 channel_info = new_channel.channel_info()[0]
    #                 self.env['bus.bus']._sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id), channel_info, {
    #                     'id': self.id, 
    #                     'model':'res.users'})
    #                 channel_ids = [new_channel.id]
    #             if channel_ids:
    #                 mail_channel = channel_obj.browse(channel_ids[0])
    #                 message = mail_channel.with_context(mail_create_nosubscribe=True).message_post(body=html,message_type='comment',subtype_xmlid='mail.mt_comment')
    #                 messages+=message
    #     return messages