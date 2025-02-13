# -*- coding: utf-8 -*-
import os
import datetime
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError



class HrOffer(models.Model):
    _name = 'hr.offer'
    _description = 'Hr Offer'
    _inherit = ['mail.thread']

    def document_default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    employee_id = fields.Many2one(
        'hr.employee', string='Бүртгэсэн ажилтны нэр', default=document_default_employee, tracking=True)
    job_id = fields.Many2one('hr.job', string='Бүртгэсэн ажилтны албан тушаал')
    department_id = fields.Many2one(
        'hr.department', string='Бүртгэсэн ажилтны Алба хэлтэс')
    date = fields.Date('Бүртгэсэн огноо ')

    offer_employee_id = fields.Many2one(
        'hr.employee', string='Ажилтны нэр')
    offer_job_id = fields.Many2one('hr.job', string='Албан тушаал')
    offer_department_id = fields.Many2one(
        'hr.department', string='Алба хэлтэс')

    offer_idea = fields.Text(string='Товч утга')
    offer_date = fields.Date(
        string='Санал хүсэлтийн огноо', default=fields.Date.context_today)
    offer_received_date = fields.Date(string='Хүлээж авсан огноо')
    name = fields.Char(string='')

    file_att_ids = fields.Many2many('ir.attachment', 'hr_offer_attach_rel', 'item_id', 'offer_attach_id',
                                    string='Хавсралт')

    @api.onchange('offer_employee_id')
    def onchange_offer_employee_id(self):
        self.offer_department_id = self.offer_employee_id.department_id.id
        self.offer_job_id = self.offer_employee_id.job_id.id

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.department_id = self.employee_id.department_id.id
        self.job_id = self.employee_id.job_id.id


# dynamic flow


    def _get_dynamic_flow_line_id(self):
        return self.flow_find().id

    def _get_default_flow_id(self):
        search_domain = []
        search_domain.append(
            ('model_id.model', '=', 'hr.offer'))
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    visible_flow_line_ids = fields.Many2many(
        'dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')
    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True,
                                                               index=True, default=_get_dynamic_flow_line_id, copy=False, domain="[('id','in', visible_flow_line_ids)]")
    history_ids = fields.One2many(
        'dynamic.flow.history', 'offer_id', 'Түүхүүд')
    flow_id = fields.Many2one('dynamic.flow', string='Урсгалын тохиргоо', tracking=True, default=_get_default_flow_id,
                              copy=True, required=True, domain="[('model_id.model', '=', 'hr.offer')]")

    flow_line_next_id = fields.Many2one(
        'dynamic.flow.line', related='flow_line_id.flow_line_next_id',  store=True)

    stage_id = fields.Many2one(
        'dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='State', store=True)

    flow_line_back_id = fields.Many2one(
        'dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
    next_state_type = fields.Char(
        string='Дараагийн төлөв', compute='_compute_next_state_type')
    state_type = fields.Char(string='Төлөвийн төрөл',
                             compute='_compute_state_type', store=True)
    is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
    confirm_user_ids = fields.Many2many(
        'res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True, readonly=True)
    branch_id = fields.Many2one(
        'res.branch', 'Салбар', default=lambda self: self.env.user.branch_id)

    @api.depends('flow_id.line_ids', 'flow_id.is_amount')
    def _compute_visible_flow_line_ids(self):
        for item in self:
            if item.flow_id:
                item.visible_flow_line_ids = self.env['dynamic.flow.line'].search(
                    [('flow_id', '=', item.flow_id.id), ('flow_id.model_id.model', '=', 'hr.offer')])
            else:
                item.visible_flow_line_ids = []

    @api.depends('flow_line_id.is_not_edit')
    def _compute_is_not_edit(self):
        for item in self:
            item.is_not_edit = item.flow_line_id.is_not_edit

    @api.depends('flow_line_id', 'flow_id.line_ids')
    def _compute_user_ids(self):
        for item in self:
            temp_users = []
            for w in item.flow_id.line_ids:
                temp = []
                try:
                    temp = w._get_flow_users(item.branch_id, item.sudo(
                    ).employee_id.department_id, item.sudo().employee_id.user_id).ids
                except:
                    pass
                temp_users += temp
            item.confirm_user_ids = temp_users

    @api.depends('flow_line_id')
    def _compute_state_type(self):
        for item in self:
            item.state_type = item.flow_line_id.state_type

    @api.depends('flow_line_next_id.state_type')
    def _compute_next_state_type(self):
        for item in self:
            item.next_state_type = item.flow_line_next_id.state_type

    api.depends('flow_line_id.stage_id')

    def _compute_flow_line_id_stage_id(self):
        for item in self:
            item.stage_id = item.flow_line_id.stage_id

    def flow_find(self, domain=[], order='sequence'):
        search_domain = []
        if self.flow_id:
            search_domain.append(('flow_id', '=', self.flow_id.id))
        else:
            search_domain.append(
                ('flow_id.model_id.model', '=', 'hr.offer'))
        return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1)

    @api.onchange('flow_id')
    def _onchange_flow_id(self):
        if self.flow_id:
            if self.flow_id:
                self.flow_line_id = self.flow_find()
        else:
            self.flow_line_id = False

    def action_next_stage(self):
        next_flow_line_id = self.flow_line_id._get_next_flow_line()
        if next_flow_line_id:
            if self.visible_flow_line_ids and next_flow_line_id.id not in self.visible_flow_line_ids.ids:
                check_next_flow_line_id = next_flow_line_id
                while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
                    temp_stage = check_next_flow_line_id._get_next_flow_line()
                    if temp_stage.id == check_next_flow_line_id.id or not temp_stage:
                        break
                    check_next_flow_line_id = temp_stage
                next_flow_line_id = check_next_flow_line_id

            if next_flow_line_id._get_check_ok_flow(False, False):
                self.flow_line_id = next_flow_line_id
                if next_flow_line_id.state_type == 'sent':
                    self.action_sent()
                if self.flow_line_id.state_type == 'done':
                    self.action_done()

                    # History uusgeh
                self.env['dynamic.flow.history'].create_history(
                    next_flow_line_id, 'offer_id', self)

                if self.flow_line_next_id:
                    send_users = self.flow_line_next_id._get_flow_users(
                        False, False)
                    if send_users:
                        self.send_chat_next_users(
                            send_users.mapped('partner_id'))
            else:
                con_user = next_flow_line_id._get_flow_users(False, False)
                confirm_usernames = ''
                if con_user:
                    confirm_usernames = ', '.join(
                        con_user.mapped('display_name'))
                raise UserError(
                    u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)

    def action_back_stage(self):
        back_flow_line_id = self.flow_line_id._get_back_flow_line()
        if back_flow_line_id:
            if back_flow_line_id._get_check_ok_flow(False, False):
                self.flow_line_id = back_flow_line_id
                self.env['dynamic.flow.history'].create_history(
                    back_flow_line_id, 'offer_id', self)
            else:
                raise UserError(_('Буцаах хэрэглэгч биш байна!'))

    def action_cancel_stage(self):
        flow_line_id = self.flow_line_id._get_cancel_flow_line()
        if flow_line_id._get_check_ok_flow(False, False):
            self.flow_line_id = flow_line_id
            self.env['dynamic.flow.history'].create_history(flow_line_id, self)
            self.state = 'cancel'
        else:
            raise UserError(_('Та цуцлах хэрэглэгч биш байна.'))

    def action_draft_stage(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()
        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
            self.state_type = 'draft'
            self.env['dynamic.flow.history'].create_history(
                flow_line_id, 'offer_id', self)
        else:
            raise UserError(_('Ноорог болгох хэрэглэгч биш байна.'))

    def send_chat_employee(self, partner_ids):
        state_type = self.flow_line_id.name
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        action_id = self.env.ref('mw_hr.hr_mission_action').id
        html = u'<b>Томилолтын хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
            self.employee_id.name)
        html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.offert&action=%s>%s</a></b>, томилолтын хүсэлт <b>%s</b> төлөвт орлоо""" % (
                base_url, self.id, action_id, self.name, state_type)
        self.flow_line_id.send_chat(html, partner_ids)

    def send_chat_next_users(self, partner_ids):
        state_type = self.flow_line_id.name
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        action_id = self.env.ref('mw_hr.hr_mission_action').id
        html = u'<b>Томилолтын хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
            self.employee_id.name)
        html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.offer&action=%s>%s</a></b>,томилолтын хүсэлт  <b>%s</b> төлөвт орлоо""" % (
                base_url, self.id, action_id, self.name, state_type)
        self.flow_line_id.send_chat(html, partner_ids)

    def unlink(self):
        for bl in self:
            if bl.state_type != 'draft':
                raise UserError('Ноорог төлөвтэй биш бол устгах боломжгүй.')
        return super(HrOffer, self).unlink()

    def action_draft(self):
        self.state_type = 'draft'

    def action_sent(self):
        if not self.name:
            self.name = self.env['ir.sequence'].next_by_code(
                'hr.offer')
        self.state_type = 'sent'

    def action_done(self):
        self.state_type = 'done'


class DynamicFlowHistory(models.Model):
    _inherit = 'dynamic.flow.history'

    offer_id = fields.Many2one(
        'hr.offer', string='Хүсэлт', ondelete='cascade', index=True)
