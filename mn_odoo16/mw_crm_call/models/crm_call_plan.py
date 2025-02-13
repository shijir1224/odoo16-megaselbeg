# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

class crm_call_plan(models.Model):
    _name = 'crm.call.plan'
    _description = 'crm call plan'
    _order = 'date desc'
    _inherit = ["mail.thread", "utm.mixin", "mail.activity.mixin"]

    state = fields.Selection([('draft','Ноорог'),('done','Хийгдсэн'),('cancel','Цуцлагдсан')], default='draft', tracking=True, string='Төлөв')
    date = fields.Date('Огноо', default=fields.Date.context_today, tracking=True)
    user_id = fields.Many2one('res.users', string='Хариуцагч', default=lambda self: self.env.user.id, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Харилцагч', tracking=True)
    vat = fields.Char(related='partner_id.vat', readonly=True)
    gender = fields.Selection(related='partner_id.gender', readonly=True)
    lastname = fields.Char(related='partner_id.lastname', readonly=True)
    phone = fields.Char(related='partner_id.phone', readonly=True)
    name = fields.Char('Тайлбар', required=True, tracking=True)
    call_type_id = fields.Many2one('crm.call.conf', string="Дуудлагын төрөл", tracking=True)
    call_type_id2 = fields.Many2one('crm.call.conf', string="Дуудлагын дэд төрөл")
    company_id = fields.Many2one(comodel_name="res.company", string="Компани", default=lambda self: self.env.user.company_id, tracking=True)
    guitsetgel_ids = fields.One2many('crm.call','plan_id', string='Гүйцэтгэл', readonly=True)
    number = fields.Char('Дугаарлалт', readonly=True)
    is_child_plan = fields.Boolean(string='Child тай эсэх')

    @api.model
    def create(self, vals):
        if vals.get('number', 'Шинэ') == 'Шинэ':
            vals['number'] = self.env['ir.sequence'].next_by_code('crm.call.plan') or 'Шинэ'
        result = super().create(vals)
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|',  ('name', operator, name), ('number', operator, name)]
        tv = self.search(domain + args, limit=limit)
        return tv.name_get()

    def name_get(self):
        res = []
        for item in self:
            name = item.name or ''
            if item.number:
                name = item.name+' [ ' + item.number+' ]'
            res.append((item.id, name))
        return res

    # def create_actual(self):
    #     obj = self.env['crm.call']
    #     obj.create({
    #         'plan_id': self.id,
    #         'call_type_id': self.call_type_id.id,
    #         'partner_id': self.partner_id.id,
    #         'date': self.date,
    #         'user_id': self.user_id.id,
    #         'name': self.phone,
    #         'description': 'FROM PLAN: '+self.name,
    #         })
        # if self.state!='done':
        #     self.state = 'done'

    # def write(self, values):
    #     if values.get("state"):
    #         if values.get("state") == "done":
    #             self.create_actual()
    #     return super().write(values)

