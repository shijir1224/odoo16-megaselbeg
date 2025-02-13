# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import date,datetime,timedelta
import logging
_logger = logging.getLogger(__name__)

@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

class res_partner(models.Model):
    _inherit = 'res.partner'

    rank_partner_id = fields.Many2one('res.partner.rank',  string='Зэрэглэл', compute='_compute_rank', store=True, tracking=True, readonly=False)
    partner_depend_deed_ids = fields.One2many('res.partner.depend.partner',  'partner_id',string='Юу болохууд', readonly=True)
    partner_depend_real_ids = fields.One2many('res.partner.depend.partner',  'base_partner_id',string='Холбоо барих')
    partner_depend_real2_ids = fields.One2many('res.partner.depend.partner',  'base_partner_id',string='Холбоо барих2')

    gender = fields.Selection([('male','Эр'),('female','Эм')], string='Хүйс', tracking=True, store=True, compute='_compute_gender_birth')
    birthday = fields.Date(string='Төрсөн өдөр', tracking=True, store=True, compute='_compute_gender_birth')
    age_your = fields.Integer(string='Нас', compute='_compute_age_your')
    activity_type1_id = fields.Many2one('mw.crm.activity.type', 'Ү.А чиглэл/Ажил эрхлэлт', tracking=True)
    activity_type = fields.Char(related='activity_type1_id.activity_type', string='Ү.А дэд чиглэл', store=True)
    owner_type = fields.Selection([
        ('llc','ХХК'),
        ('lc','ХК'),
        ('turiin','Төрийн байгууллага'),
        ('turiin_bus','Төрийн бус байгууллага'),
        ('gadaad','Гадаадын хөрөнгө оруулалт'),
        ('other','Бусад')], 'Өмчлөлийн хэлбэр', tracking=True)
    

    # tracking=true bolgov
    lastname = fields.Char(index=True, tracking=True, string='Овог')
    name = fields.Char(index=True, tracking=True, required=True)
    ref = fields.Char(string='Reference', index=True, tracking=True)
    lang = fields.Selection(_lang_get, string='Language', default=lambda self: self.env.lang,
                            tracking=True,
                            help="All the emails and documents sent to this contact will be translated in this language.")
    
    user_id = fields.Many2one('res.users', string='Salesperson', tracking=True,
      help='The internal user in charge of this contact.')
    vat = fields.Char(string='Tax ID', tracking=True, help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.", required=True, index=True)
    website = fields.Char('Website Link', tracking=True)
    comment = fields.Text(string='Notes', tracking=True)
    active = fields.Boolean(default=True,tracking=True)
    # employee = fields.Boolean(help="Check this box if this contact is an Employee.")
    street = fields.Char(tracking=True)
    # street2 = fields.Char()
    # zip = fields.Char(change_default=True)
    # city = fields.Char()
    email = fields.Char(tracking=True, index=True)
    phone = fields.Char(tracking=True, index=True)
    mobile = fields.Char(tracking=True, index=True)
    tovch_depend_name = fields.Char('Хамаарал товч', compute='name_partner_depend_real_ids')
    feedback_ids = fields.One2many('mw.feedback', 'partner_id', string="Санал гомдол")
    lead_ids = fields.One2many('crm.lead', 'partner_id', string="Сэжимүүд")
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """ search full name and barcode """
        if args is None:
            args = []
        recs = self.search(['|','|','|','|',('name', operator, name),('vat', operator, name),('ref', operator, name),('phone', operator, name),('lastname', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.depends('partner_depend_real_ids')
    def name_partner_depend_real_ids(self):
        for item in self:
            dep_names = []
            for d in item.partner_depend_real_ids:
                n1 = d.name or ''
                n2 = d.depend_type_id.display_name or ''
                dep_names.append('%s %s'%(n1,n2))
            item.tovch_depend_name = '| '.join(dep_names)

    @api.depends('birthday')
    def _compute_age_your(self):
        for item in self:
            item.age_your = item.get_age()

    def get_age(self):
        current_date = datetime.now()
        current_year = current_date.year
        try:
            year = self.birthday.year
            return  current_year-int(year)
        except Exception as e:
            return 0

    def get_birthday(self, register):
        if register:
            reg = register
            year = reg[2:4]
            month = reg[4:6]
            day = reg[6:8]
            if int(month[0])>=2:
                year='20'+year
                month = str(int(month[0])-2)+month[1]
            else:
                year='19'+year
            b_day = year+'-'+month+'-'+day
            datetime.strptime(b_day, '%Y-%m-%d')
            return b_day

    @api.depends('vat', 'company_type')
    def _compute_gender_birth(self):
        for item in self:
            vat_gender = False
            vat_birthday = None
            if item.vat and item.company_type=='person':
                if len(item.vat)>=9:
                    try:
                        lan2 = item.vat[len(item.vat)-2]
                        if (int(lan2) % 2) == 0:
                            vat_gender = 'female'
                        else:
                            vat_gender = 'male'
                    except Exception as e:
                        _logger.info('gender aldaa %s'%(e))
                        pass
                    try:
                        vat_birthday = item.get_birthday(item.vat)
                    except Exception as e:
                        _logger.info('birthday aldaa %s'%(e))
                        pass

            item.gender = vat_gender
            item.birthday = vat_birthday
    def _get_rank(self, sale_val):
        return self.env['res.partner.rank'].search([('type','=',self.company_type),('min_sale','<=',sale_val),('max_sale','>=',sale_val)], limit=1)

    def _compute_rank(self):
        for item in self:
            item.rank_partner_id = False

    # def name_get(self):
    #     res = []
    #     for partner in self:
    #         res_name = super(res_partner, partner).name_get()
    #         if partner.ref:
    #             res_name = u''+res_name[0][1]+u' ['+partner.ref+']'
    #             res.append((partner.id, res_name))
    #         else:
    #             res.append(res_name[0])
    #     return res

class res_partner_rank(models.Model):
    _name = 'res.partner.rank'
    _description = 'Харилцагчийн зэрэглэл'
    _order = 'type, sequence'

    name = fields.Char('Нэр', required=True)
    type = fields.Selection([('company','Байгууллага'), ('person','Хувь хүн')],'Төрөл', required=True)
    sequence = fields.Integer('Дараалал', default=1)
    min_sale = fields.Float('Доод борлуулалт')
    max_sale = fields.Float('Дээд борлуулалт')
    priority = fields.Selection([
                    ('0', '0'),
                    ('1', '1'),
                    ('2', '2'),
                    ('3', '3'),
                    ('4', '4'),
                    ('5', '5'),
                ], string='Од')
    
class res_partner_depend(models.Model):
    _name = 'res.partner.depend'
    _description = 'Харилцагчийн хамаарлын төрөл'
    
    name = fields.Char('Хамаарлын нэр', required=True)
    company_ok = fields.Boolean('Компаний хамаарал', default=False)
    depend_partner_cc_ids = fields.One2many('res.partner.depend.partner', 'depend_type_id', string="holboo 2 holboo")
    depend_partner_count = fields.Integer(string="Бүртгэлтэй харилцагчид", compute="_compute_partner_count")



    @api.depends('depend_partner_cc_ids')
    def _compute_partner_count(self):
        for item in self.sudo():
            item.depend_partner_count = len(item.depend_partner_cc_ids)

    def view_depended_partners(self):
        self.ensure_one()
        action = self.env.ref('base.action_partner_form').read()[0]
        action['domain'] = [('id','in',self.depend_partner_cc_ids.base_partner_id.ids)]
        return action
    
    

    

class res_partner_depend_partner(models.Model):
    _name = 'res.partner.depend.partner'
    _description = 'Харилцагчийн хамаарал харилцагч'
    
    base_partner_id = fields.Many2one('res.partner', 'One2many Харилцагч', index=True)
    partner_id = fields.Many2one('res.partner', 'Байгаа харилцагч', index=True)
    depend_type_id = fields.Many2one('res.partner.depend',  string='Таны юу болох')
    company_ok = fields.Boolean(related='depend_type_id.company_ok', readonly=True)
    name = fields.Char(string='Нэр', store=True, readonly=False, compute='_compute_partner')
    phone = fields.Char(string='Утас', store=True, readonly=False, compute='_compute_partner')
    vat = fields.Char(string='Регистр', store=True, readonly=False, compute='_compute_partner')
    lastname = fields.Char(string="Овог",store=True, readonly=False, compute='_compute_partner' )
    email = fields.Char(string='И-мэйл', store=True,readonly=False, compute='_compute_partner')
  
    def name_get(self):
        res = []
        for obj in self:
            iin = ' -ийн'
            if obj.company_ok:
                iin = ''
            name = (obj.base_partner_id.name or obj.name or '')+iin
            if obj.depend_type_id:
                name +=' /'+obj.depend_type_id.display_name+'/'
            res.append((obj.id, name))
        return res

    @api.depends('partner_id')
    def _compute_partner(self):
        for item in self:
            item.name = item.partner_id.name
            item.phone = item.partner_id.phone
            item.vat = item.partner_id.vat
            item.lastname = item.partner_id.lastname
            item.email = item.partner_id.email

    def create(self, val):
        res = super(res_partner_depend_partner, self).create(val)

        return res