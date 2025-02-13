# -*- coding: utf-8 -*-

from odoo import fields, models
import time

class RequestTemplate(models.Model):
    _name = 'request.template'
    _description = 'Workflow Request Template'
    
    date=fields.Datetime("Creation Date", readonly=True)
    complete_date=fields.Datetime('Confirmed Date', readonly=True)
    wkf_note_ids=fields.One2many('request.template.wkf.notes','request_id','Workflow History', readonly=True)
    amount = fields.Float('Amount',required=True, readonly=True, states={'draft':[('readonly',False)]})

class RequestTemplateWkfNotes(models.Model):
    _name = 'request.template.wkf.notes'
    _description = 'Workflow Notes of Request Template'
    _order = 'date'
    
    create_ok = fields.Boolean('Create ok', default=False)
    name=    fields.Char('Name', size=64, required=True, translate=True)
    user_id=fields.Many2one('res.users', 'User', required=True)
    date=fields.Datetime('Date', required=True)
    amount=fields.Float('Amount')
    notes=fields.Text('Notes')
    action=fields.Selection([('next','Next'),('back','Back'),('cancel','Cancel')],'Action', required=True)
    request_id=fields.Many2one('payment.request', 'Request', required=True, ondelete="cascade")
    flow_line_id = fields.Many2one('dynamic.flow.line', 'Төлөв')
   
    def create_history(self,flow_line_id,request,action,amount=0):
        context = self.env.context
        request_id = request.id
        request_obj = request
        notes = request.description
        desc = request.name
        val = {
               'name' : _(desc),
               'user_id' : self.env.user.id,
               'action' : action,
               'notes' : notes,
               'amount':amount,
               'request_id' : request_id,
               'date':time.strftime('%Y-%m-%d %H:%M:%S'),
               'flow_line_id':flow_line_id.id
        }
        note_id = self.env['request.template.wkf.notes'].create(val)

class RequestTemplateVerify(models.TransientModel):
    _name = 'request.template.verify'
    _description = 'Request Template Verify'

    notes=fields.Text('Notes')

    def approve(self):
        ''' Ажлын урсгалын дараагийн алхамд шилжүүлж тэмдэглэлийг хадгална.
        
            Usage : <button name="%(action_requestable_object_verify)s" 
                        string="Approve" type="action" icon="gtk-ok"
                        context="{'desc':'Department Manager Verification',
                            model':'request.payment','signal':'action_department'}"/>
        '''
        context = self.env.context
        request_id = self.env.context.get('active_id', [])  
        request_obj = self.env[context['model']].browse(request_id)
        request_template_id = request_obj.request_tmpl_id.id
        notes = self.notes
        desc = context['desc']
        val = {
               'name' : _(desc),
               'user_id' : self.env.user.id,
               'action' : 'approved',
               'notes' : notes,
               'request_id' : request_template_id,
               'date':time.strftime('%Y-%m-%d')
        }
        note_id = self.env['request.template.wkf.notes'].create(val)
        request_obj.write({'state':context['signal_approve']})
        # Chat илгээх
        res_model = self.env['ir.model.data'].search([
                ('module','=','mw_account_payment_request'),
                ('name','=','res_groups_cash_accountant')])
        group = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
        for receiver in group.users:
            if receiver.partner_id:
                if self.env.user.partner_id.id != receiver.partner_id.id:
                    channel_ids = self.env['mail.channel'].search([
                       ('channel_partner_ids', 'in', receiver.partner_id.id),
                       ('channel_partner_ids', 'in', self.env.user.partner_id.id),
                       ]).filtered(lambda r: len(r.channel_partner_ids) == 2).ids
                    if not channel_ids:
                        vals = {
                            'channel_type': 'chat', 
                            'name': u''+receiver.partner_id.name+u', '+self.env.user.name, 
                            'public': 'private', 
                            'channel_partner_ids': [(4, receiver.partner_id.id), (4, self.env.user.partner_id.id)], 
                            # #'email_send': False
                        }
                        new_channel = self.env['mail.channel'].create(vals)
                        notification = _('<div class="o_mail_notification">created <a href="#" class="o_channel_redirect" data-oe-id="%s">#%s</a></div>') % (new_channel.id, new_channel.name,)
                        new_channel.message_post(body=notification, message_type="notification", subtype_xmlid='mail.mt_note')
                        channel_info = new_channel.channel_info()[0]
                        self.env['bus.bus']._sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id), channel_info, {'id': self.id, 'model':'request.template.verify'})
                        channel_ids = [new_channel.id]
                    # MSG илгээх
                    html = u"<span style='font-size:10pt; font-weight:bold; color:red;'>Бэлэн мөнгөний хүсэлт батлагдаж мөнгөн хөрөнгийн нягтлангуудад илгээгдлээ," +u' Та шалгана уу!</span>'
                    self.env['mail.message'].create({
                               'message_type': 'comment', 
                               'subtype_id': 1,
                               'body':  html,
                               'channel_ids':  [(6, 0, channel_ids),]
                               })
        return {'type': 'ir.actions.act_window_close'}
    
    def reject(self):
        '''Ажлын урсгалын татгалзах алхамд шилжүүлж тэмдэглэлийг хадгална.
        
            Usage : <button name="%(action_requestable_object_reject)s" 
                        string="Approve" type="action" icon="gtk-ok"
                        context="{'desc':'Department Manager Verification',
                            model':'request.payment','signal':'action_department'}"/>
        '''
        context = self.env.context
        request_id = self.env.context.get('active_id', [])  
        request_obj = self.env[context['model']].browse(request_id)
        request_template_id = request_obj.request_tmpl_id.id
        notes = self.notes
        desc = context['desc']
        val = {
               'name' : _(desc),
               'user_id' : self.env.user.id,
               'action' : 'rejected',
               'notes' : notes,
               'request_id' : request_template_id,
               'date':time.strftime('%Y-%m-%d')
        }
        note_id = self.env['request.template.wkf.notes'].create(val)
        request_obj.write({'state':'cancel'})
        
        return {'type': 'ir.actions.act_window_close'}
