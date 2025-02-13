# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime, timedelta


class StockPicking(models.Model):
    _inherit = "stock.picking"

    checked_user_id = fields.Many2one('res.users', string='Баталсан хэрэглэгч', tracking=True, readonly=True)
    checked_date = fields.Datetime(string='Баталсан огноо', tracking=True, readonly=True)
    check_is = fields.Boolean(string='Батлах эсэх ёстой эсэх', compute='_compute_check_is')
    check_ok = fields.Boolean(string='Баталсан эсэх', tracking=True)
############# batlah hereglegch 2 #########
    checked_user_id2 = fields.Many2one('res.users', string='Баталсан хэрэглэгч 2', tracking=True, readonly=True)
    checked_date2 = fields.Datetime(string='Баталсан огноо 2', tracking=True, readonly=True)
    check_ok2 = fields.Boolean(string='Баталсан эсэх 2', tracking=True)
    check_is2 = fields.Boolean(string='Батлах эсэх ёстой эсэх 2', compute='_compute_check_is2')
    
    def send_chat_checker(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('stock', 'action_picking_tree_all')[1]
        html = u'<b>Хөдөлгөөн батлана уу</b><br/> Ажилтаны үүсгэсэн <i style="color: red">%s</i>  </br>'%(self.create_uid.name)
        html += u"""<b><a target="_blank"  href=%s/web#id=%s&view_type=form&model=stock.picking&action=%s>%s</a></b>"""% (base_url,self.id,action_id,self.name)
        partner_ids = self.location_dest_id.check_user_ids.mapped('partner_id')
        self.send_chat(html,partner_ids)

    def send_chat_checker2(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('stock', 'action_picking_tree_all')[1]
        html = u'<b>Хөдөлгөөн батлана уу</b><br/> Ажилтаны үүсгэсэн <i style="color: red">%s</i>  </br>'%(self.create_uid.name)
        html += u"""<b><a target="_blank"  href=%s/web#id=%s&view_type=form&model=stock.picking&action=%s>%s</a></b>"""% (base_url,self.id,action_id,self.name)
        partner_ids = self.location_dest_id.check_user_ids2.mapped('partner_id')
        self.send_chat(html,partner_ids)



    def send_chat(self, html, partner_ids):
        if not partner_ids:
            raise UserError(u'Мэдэгдэл хүргэх харилцагч байхгүй байна')
        channel_obj = self.env['mail.channel']
        for item in partner_ids:
            if self.env.user.partner_id.id!=item.id:
                channel_ids = channel_obj.search([
                    ('channel_partner_ids', 'in', [item.id])
                    ,('channel_partner_ids', 'in', [self.env.user.partner_id.id])
                    ]).filtered(lambda r: len(r.channel_partner_ids) == 2).ids
                if not channel_ids:
                    vals = {
                        'channel_type': 'chat',
                        'name': u''+item.name+u', '+self.env.user.name,
                        'public': 'private',
                        'channel_partner_ids': [(4, item.id), (4, self.env.user.partner_id.id)],
                        # 'email_send': self.env.context.get('send_email',False)
                    }
                    new_channel = channel_obj.create(vals)
                    notification = _('<div class="o_mail_notification">created <a href="#" class="o_channel_redirect" data-oe-id="%s">#%s</a></div>') % (new_channel.id, new_channel.name,)
                    new_channel.message_post(body=notification, message_type="notification", subtype_xmlid='mail.mt_note')
                    channel_info = new_channel.channel_info()[0]
                    self.env['bus.bus']._sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id), channel_info, {
                        'id': self.id, 
                        'model':'stock.picking'})

                    channel_ids = [new_channel.id]
                if channel_ids:
                    mail_channel = channel_obj.browse(channel_ids[0])
                    message = mail_channel.with_context(mail_create_nosubscribe=True).message_post(
                                                                                       body=html,
                                                                                       message_type='comment',
                                                                                       subtype_xmlid='mail.mt_comment')


    @api.depends('location_dest_id')
    def _compute_check_is(self):
        for item in self:
            item.check_is = True if item.location_dest_id.check_user_ids else False

    @api.depends('location_dest_id')
    def _compute_check_is2(self):
        for item in self:
            item.check_is2 = True if item.location_dest_id.check_user_ids2 else False

    
    @api.onchange('check_ok')
    def def_check_ok(self):
        if self.check_ok:
            if self.location_dest_id.check_user_ids and  self.env.user.id not in self.location_dest_id.check_user_ids.ids:
                raise UserError(u'Та %s Агуулахын батлах хэрэглэгч биш байна "%s" Батлах хэрэглэгч'%(self.location_dest_id.display_name,','.join(self.location_dest_id.check_user_ids.mapped('display_name'))))
            self.checked_user_id = self.env.user.id
            self.checked_date = datetime.now()
        else:
            self.checked_user_id = False
            self.checked_date = False

    @api.onchange('check_ok2')
    def def_check_ok2(self):
        if self.check_ok2:
            if self.location_dest_id.check_user_ids2 and self.env.user.id not in self.location_dest_id.check_user_ids2.ids:
                raise UserError(u'Та %s Агуулахын батлах хэрэглэгч биш байна "%s" Батлах хэрэглэгч'%(self.location_dest_id.display_name,','.join(self.location_dest_id.check_user_ids2.mapped('display_name'))))
            self.checked_user_id2 = self.env.user.id
            self.checked_date2 = datetime.now()
        else:
            self.checked_user_id2 = False
            self.checked_date2 = False

    def action_done(self):
        for item in self:
            ss = item.location_dest_id.check_user_ids
            ss += item.location_dest_id.check_user_ids2
            if item.location_dest_id.check_user_ids and not self.check_ok and self.env.user.id not in item.location_dest_id.check_user_ids.ids:
                if item.location_dest_id.check_user_ids2 and not self.check_ok and self.env.user.id not in item.location_dest_id.check_user_ids2.ids:
                    raise UserError(u'Та %s Агуулахын батлах хэрэглэгч биш байна "%s" Батлах хэрэглэгч'%(item.location_dest_id.display_name,    ','.join(ss.mapped('display_name'))))
        return super(StockPicking, self).action_done()

    

    def get_checker_signature(self,ids):
        report_id = self.browse(ids)
        user_id = report_id.checked_user_id
        html = '<table>'
        image_str = '________________________'
        user_str = '________________________'
        if user_id:
            user_str = user_id.name
        if user_id.digital_signature:
            image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,'+user_id.digital_signature+'" />'
        html += u'<tr><td><p>Захирал Баталсан </p></td><td>'+image_str+u'</td><td> <p>/'+user_str+u'/</p></td></tr>'
        html += '</table>'
        if report_id.check_is:
            return html
        return ''


class StockLocation(models.Model):
    _inherit = "stock.location"
    
    check_user_ids = fields.Many2many('res.users', 'stock_location_check_user_rel', 'loc_id', 'user_id', string='Батлах хэрэглэгчид')
    check_user_ids2 = fields.Many2many('res.users', 'stock_location_check_user_rel2', 'loc_id', 'user_id', string='Батлах хэрэглэгчид 2')
    