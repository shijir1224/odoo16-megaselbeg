# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools
from odoo.exceptions import UserError
from datetime import datetime, time, timedelta

class power_hats_total(models.Model):
    _name = 'power.hats.total'
    _inherit = ['mail.thread']
    _description = 'power hats total'
    _order = 'date desc'
    _rec_name = 'date'

    @api.model
    def _get_default_day_type(self):
        return self.env.context.get('hats_day_type','day')
        
    date = fields.Date('Огноо', default=fields.Date.context_today, required=True, track_visibility='onchange')
    lines = fields.One2many('power.hats','parent_id', string='Мөр', copy=True)
    desc = fields.Text('Тайлбар', track_visibility='onchange')
    state = fields.Selection([('draft','Ноорог'),('done','Батлагдсан')], default='draft', string='Төлөв', required=True, track_visibility='onchange')
    day_type = fields.Selection([('day','Өдөр бүр'),('month','Сарын')], default=_get_default_day_type, string='Хац нийт төрөл', track_visibility='onchange')
    niit_35_aldagdal = fields.Float(string='35кВ нийт Алдагдал', compute='_compute_all', store=True, digits=(16, 3))
    niit_35_aldagdal_per = fields.Float(string='35кВ нийт Алдагдал %', compute='_compute_all', store=True, digits=(16, 2))
    niit_hereglee = fields.Float(string='Нийт Хэрэглээ', compute='_compute_all', store=True, digits=(16, 3))
    niit_hereglee_per = fields.Float(string='Нийт Хэрэглээ %', compute='_compute_all', store=True, digits=(16, 2))
    
    niit_6_aldagdal = fields.Float(string='6кВ нийт Алдагдал', compute='_compute_all', store=True, digits=(16, 3), track_visibility='onchange')
    niit_6_aldagdal_per = fields.Float(string='6кВ нийт Алдагдал %', compute='_compute_all', store=True, digits=(16, 2))

    shugamiin_6_aldagdal = fields.Float(string='6кВ шугамын Алдагдал', compute='_compute_all', store=True, digits=(16, 3))
    shugamiin_6_aldagdal_per = fields.Float(string='6кВ шугамын Алдагдал %', compute='_compute_all', store=True, digits=(16, 2))

    niit_aldagdal = fields.Float(string='Нийт Алдагдал', compute='_compute_all', store=True, digits=(16, 3), track_visibility='onchange')
    niit_aldagdal_per = fields.Float(string='Нийт Алдагдал %', compute='_compute_all', store=True, digits=(16, 2))
    tolgoi_niit = fields.Float(string='Толгой нийт', compute='_compute_all', store=True, digits=(16, 3))
    niit_gerel_kolonk = fields.Float(string='Гэрэлтүүлэг,колонк', compute='_compute_all', store=True, digits=(16, 3))
    niit_gadnii = fields.Float(string='Нийт Гадны байгууллага /хэрэглээ/', compute='_compute_all', store=True, digits=(16, 3))
    niit_gadnii_hasaad = fields.Float(string='Нийт хэрэглээ /гадныхыг хасаад/', compute='_compute_all', store=True, digits=(16, 3))
    udur_tarip = fields.Float('Өдөр тариф')
    orgil_tarip = fields.Float('Оргил тариф')
    shunu_tarip = fields.Float('Шөнө тариф')

    niit_hereglee_tolgoi_udur = fields.Float('Нийт хэрэглээ толгой Өдөр', compute='_compute_all', store=True, digits=(16, 3), track_visibility='onchange')
    niit_hereglee_tolgoi_orgil = fields.Float('Нийт хэрэглээ толгой Оргил', compute='_compute_all', store=True, digits=(16, 3), track_visibility='onchange')
    niit_hereglee_tolgoi_shunu = fields.Float('Нийт хэрэглээ толгой Шөнө', compute='_compute_all', store=True, digits=(16, 3), track_visibility='onchange')
    
    niit_gadnii_udur = fields.Float('Нийт гадны Өдөр', compute='_compute_all', store=True, digits=(16, 3), track_visibility='onchange')
    niit_gadnii_orgil = fields.Float('Нийт гадны Оргил', compute='_compute_all', store=True, digits=(16, 3), track_visibility='onchange')
    niit_gadnii_shunu = fields.Float('Нийт гадны Шөнө', compute='_compute_all', store=True, digits=(16, 3), track_visibility='onchange')

    niit_hereglee_udur = fields.Float('Нийт хэрэглээ Өдөр', compute='_compute_all', store=True, digits=(16, 3), track_visibility='onchange')
    niit_hereglee_orgil = fields.Float('Нийт хэрэглээ Оргил', compute='_compute_all', store=True, digits=(16, 3), track_visibility='onchange')
    niit_hereglee_shunu = fields.Float('Нийт хэрэглээ Шөнө', compute='_compute_all', store=True, digits=(16, 3), track_visibility='onchange')

    niit_hereglee_une_udur = fields.Float('Нийт хэрэглээ үнэ Өдөр', compute='_compute_all', store=True, digits=(16, 3))
    niit_hereglee_une_orgil = fields.Float('Нийт хэрэглээ үнэ Оргил', compute='_compute_all', store=True, digits=(16, 3))
    niit_hereglee_une_shunu = fields.Float('Нийт хэрэглээ үнэ Шөнө', compute='_compute_all', store=True, digits=(16, 3))
    niit_hereglee_une = fields.Float('Нийт хэрэглээ үнэ', compute='_compute_all', store=True, digits=(16, 3))

    niit_hereglee_nuat_udur = fields.Float('Нийт хэрэглээ үнэ НӨАТ Өдөр', compute='_compute_all', store=True, digits=(16, 3))
    niit_hereglee_nuat_orgil = fields.Float('Нийт хэрэглээ үнэ НӨАТ Оргил', compute='_compute_all', store=True, digits=(16, 3))
    niit_hereglee_nuat_shunu = fields.Float('Нийт хэрэглээ үнэ НӨАТ Шөнө', compute='_compute_all', store=True, digits=(16, 3))
    niit_hereglee_nuat = fields.Float('Нийт хэрэглээ үнэ НӨАТ', compute='_compute_all', store=True, digits=(16, 3))

    chadliin_tarip = fields.Float('Чадлын тариф', compute='_compute_all', store=True, digits=(16, 3))
    chadliin_nuat_tarip = fields.Float('Чадлын тариф НӨАТ', compute='_compute_all', store=True, digits=(16, 3))
    niit35_trans_ald = fields.Float('35кВ Нийт шугам трансформаторын алдагдал', compute='_compute_all', store=True, digits=(16, 2))
    niit35_trans_ald_per = fields.Float('35кВ Нийт шугам трансформаторын алдагдал хувь', compute='_compute_all', store=True, digits=(16, 2))
    

    barimt_une = fields.Float('Баримтын үнэ')
    sar_honog = fields.Integer('Хуанлийн хоног', default=1)
    niit_une = fields.Float('Нийт үнэ', compute='_compute_all', store=True, digits=(16, 3))
    dundaj_une = fields.Float('Дундаж үнэ', compute='_compute_all', store=True, digits=(16, 3))

    def update_compute(self):
        self._compute_all()
        
    @api.depends('lines','barimt_une','sar_honog','udur_tarip','orgil_tarip','shunu_tarip')
    def _compute_all(self):
        for item in self:
            head_total = sum(item.lines.filtered(lambda r: r.category=='tolgoi').mapped('niit_orolt'))
            item.tolgoi_niit = head_total
            item.niit_hereglee_tolgoi_udur = sum(item.lines.filtered(lambda r: r.category=='tolgoi').mapped('garalt_niit_6_udur'))
            item.niit_hereglee_tolgoi_orgil = sum(item.lines.filtered(lambda r: r.category=='tolgoi').mapped('garalt_niit_6_orgil'))
            item.niit_hereglee_tolgoi_shunu = sum(item.lines.filtered(lambda r: r.category=='tolgoi').mapped('garalt_niit_6_shunu'))

            sum_other = sum(item.lines.filtered(lambda r: r.category=='user1').mapped('niit_orolt'))
            item.niit_35_aldagdal = head_total - sum_other
            niit_hereglee = 0
            if item.day_type == 'month':
                niit_hereglee = sum(item.lines.filtered(lambda r: r.category=='user2').mapped('niit_orolt'))
                for x in item.lines.filtered(lambda r: r.category=='user1'):
                    niit_hereglee += sum(x.lines.filtered(lambda r: r.user1plus).mapped('hats_kv'))
            elif item.day_type == 'day':
                for x in item.lines.filtered(lambda r: r.category=='user1'):
                    niit_hereglee += sum(x.lines.filtered(lambda r: r.user1plus).mapped('hats_kv'))
                for x in item.lines.filtered(lambda r: r.category=='user2'):
                    niit_hereglee += sum(x.lines.filtered(lambda r: r.user2plus).mapped('hats_kv'))
                for x in item.lines.filtered(lambda r: r.category=='user3'):
                    niit_hereglee += sum(x.lines.filtered(lambda r: r.user3plus).mapped('hats_kv'))
            item.niit_hereglee = niit_hereglee
            user1_niit6garalt = 0
            for x in item.lines.filtered(lambda r: r.category=='user1'):
                user1_niit6garalt += x.garalt_niit_6_niit
            # user1_niit6garalt = sum([sum(x.garalt_niit_6_niit) for x in item.lines.filtered(lambda r: r.category=='user1')])
            
            user1_niit6garalt - niit_hereglee
            if item.day_type=='day':
                item.shugamiin_6_aldagdal = 0
            else:
                item.shugamiin_6_aldagdal = user1_niit6garalt - sum(item.lines.filtered(lambda r: r.category=='user2').mapped('niit_orolt'))
            if item.day_type=='day':
                user1_niit_orolt = 0
                for x in item.lines.filtered(lambda r: r.category=='user1'):
                    user1_niit_orolt += x.niit_orolt
                item.niit_6_aldagdal = user1_niit_orolt - item.niit_hereglee
            else:
                item.niit_6_aldagdal = item.shugamiin_6_aldagdal + sum(item.lines.filtered(lambda r: r.category=='user1').mapped('aldagdal_6_niit'))
            item.niit_aldagdal = item.niit_35_aldagdal + item.niit_6_aldagdal
            tot2 = head_total
            item.niit_35_aldagdal_per = item.niit_35_aldagdal/tot2*100 if tot2!=0 else 0
            tot2 = head_total
            item.niit_hereglee_per = item.niit_hereglee/tot2*100 if tot2!=0 else 0
            tot2 = head_total
            item.shugamiin_6_aldagdal_per = item.shugamiin_6_aldagdal/tot2*100 if tot2!=0 else 0
            item.niit_6_aldagdal_per = item.niit_6_aldagdal/tot2*100 if tot2!=0 else 0

            tot2 = head_total
            item.niit_aldagdal_per = item.niit_aldagdal/tot2*100 if tot2!=0 else 0
            gerel_kolonk = 0
            if item.day_type=='month':
                for x in item.lines.filtered(lambda r: r.category=='user2'):
                    gerel_kolonk += sum(x.lines.filtered(lambda r: r.user2plus).mapped('hats_kv'))
                    
                for x in item.lines.filtered(lambda r: r.category=='user3'):
                    gerel_kolonk -= sum(x.lines.filtered(lambda r: r.user3plus).mapped('hats_kv'))
            if item.day_type=='day':
                for x in item.lines.filtered(lambda r: r.category=='user2' and r.type=='atp_ktp'):
                    gerel_kolonk += sum(x.lines.filtered(lambda r: r.user2plus).mapped('hats_kv'))
            item.niit_gerel_kolonk = gerel_kolonk
            
            niit_gad = 0
            niit_gad_udur = 0
            niit_gad_orgil = 0
            niit_gad_shunu = 0
            if item.day_type=='month':
                for x in item.lines.filtered(lambda r: r.category=='user1'):
                    niit_gad += sum(x.lines.filtered(lambda r: r.user1plusdirect).mapped('hats_kv'))
                    niit_gad_udur += sum(x.lines.filtered(lambda r: r.user1plusdirect and r.tarip=='udur').mapped('hats_kv'))
                    niit_gad_orgil += sum(x.lines.filtered(lambda r: r.user1plusdirect and r.tarip=='orgil').mapped('hats_kv'))
                    niit_gad_shunu += sum(x.lines.filtered(lambda r: r.user1plusdirect and r.tarip=='shunu').mapped('hats_kv'))

            for x in item.lines.filtered(lambda r: r.category=='user3'):
                niit_gad += sum(x.lines.mapped('hats_kv'))
                niit_gad_udur += sum(x.lines.filtered(lambda r: r.tarip=='udur').mapped('hats_kv'))
                niit_gad_orgil += sum(x.lines.filtered(lambda r: r.tarip=='orgil').mapped('hats_kv'))
                niit_gad_shunu += sum(x.lines.filtered(lambda r: r.tarip=='shunu').mapped('hats_kv'))
            
            item.niit_gadnii_udur = niit_gad_udur
            item.niit_gadnii_orgil = niit_gad_orgil
            item.niit_gadnii_shunu = niit_gad_shunu

            item.niit_hereglee_udur = item.niit_hereglee_tolgoi_udur - item.niit_gadnii_udur
            item.niit_hereglee_orgil = item.niit_hereglee_tolgoi_orgil - item.niit_gadnii_orgil
            item.niit_hereglee_shunu = item.niit_hereglee_tolgoi_shunu - item.niit_gadnii_shunu

            item.niit_gadnii = niit_gad
            item.niit_gadnii_hasaad = item.tolgoi_niit - niit_gad

            item.niit_hereglee_une_udur = item.niit_hereglee_udur*item.udur_tarip
            item.niit_hereglee_une_orgil = item.niit_hereglee_orgil*item.orgil_tarip
            item.niit_hereglee_une_shunu = item.niit_hereglee_shunu*item.shunu_tarip
            item.niit_hereglee_une = item.niit_hereglee_une_udur+item.niit_hereglee_une_orgil+item.niit_hereglee_une_shunu
            
            if item.day_type=='month':
                item.niit_hereglee_nuat_udur = item.niit_hereglee_une_udur*0.1
                item.niit_hereglee_nuat_orgil = item.niit_hereglee_une_orgil*0.1
                item.niit_hereglee_nuat_shunu = item.niit_hereglee_une_shunu*0.1
                item.niit_hereglee_nuat = item.niit_hereglee_nuat_udur+item.niit_hereglee_nuat_orgil+item.niit_hereglee_nuat_shunu
                item.chadliin_tarip = item.niit_hereglee_une_orgil/(5*item.sar_honog)*25000 if item.sar_honog!=0 else 0
                item.chadliin_nuat_tarip = item.chadliin_tarip*0.1
                item.niit_une = item.barimt_une+item.niit_hereglee_une+item.chadliin_tarip+item.niit_hereglee_nuat+item.chadliin_nuat_tarip
                item.dundaj_une = item.niit_une/item.niit_gadnii_hasaad if item.niit_gadnii_hasaad!=0 else 0
                # Дэд станцууд нийт
                ded_st_niit = sum(item.lines.filtered(lambda r: r.category=='user1').mapped('niit_aldagdal_niit'))
                item.niit35_trans_ald = item.niit_35_aldagdal+ded_st_niit
                item.niit35_trans_ald_per = item.niit35_trans_ald/item.tolgoi_niit*100 if item.tolgoi_niit!=0 else 0
            else:
                item.niit_hereglee_nuat_udur = 0
                item.niit_hereglee_nuat_orgil = 0
                item.niit_hereglee_nuat_shunu = 0
                item.niit_hereglee_nuat = 0
                item.chadliin_tarip = 0
                item.chadliin_nuat_tarip = 0
                item.niit_une = 0
                item.dundaj_une = 0

    def action_to_done(self):
        for item in self.lines:
            item.action_to_done()
        self.state = 'done'

    def action_to_draft(self):
        for item in self.lines:
            item.action_to_draft()
        self.state = 'draft'

class power_hats(models.Model):
    _name = 'power.hats'
    _inherit = ['mail.thread']
    _description = 'power hats'
    _order = 'date desc, sequence'

    @api.model
    def _get_default_date(self):
        if self.parent_id:
            return self.parent_id.date
        else:
            return str(datetime.now().strftime("%Y-%m-%d"))
        
    parent_id = fields.Many2one('power.hats.total', string='Хац Нийт')
    day_type = fields.Selection([('day','Өдөр бүр'),('month','Сарын')], related='parent_id.day_type', readonly=True)
    sequence = fields.Integer('Дараалал', default=1)
    date = fields.Date('Огноо', related='parent_id.date', store=True, readonly=True, track_visibility=True)
    lines = fields.One2many('power.hats.line','parent_id', string='Мөр', copy=True)
    station_id = fields.Many2one('power.category', string='Станц/Хөрөнгө', domain="[('main_type','=','group')]", track_visibility=True)
    type = fields.Selection([('station','Станц Сонгох'),('company_department','Байгууллага'),('technic','Экскаватор'),('asset','Хөрөнгө'),('atp_ktp','ATP KTP')], default='station', string='Төрөл', required=True, track_visibility=True)
    # erdenes, ms1, ms2 user1     atp-uud, ktp-uud, eksca-uud, shop, ett, titantower user2
    # trans, venveim erhettunsh, primary energy, erin mongol user3
    category = fields.Selection([('tolgoi','Толгой'),('user1','Хэрэглэгч 1'),('user2','Хэрэглэгч 2'),('user3','Хэрэглэгч 3')], string='Category', required=True, track_visibility=True)
    state = fields.Selection([('draft','Ноорог'),('done','Батлагдсан')], default='draft', string='Төлөв', required=True, track_visibility=True)
    name = fields.Char('Нэр', compute='_compute_name')
    desc = fields.Text('Тайлбар', track_visibility=True)

    garalt_niit_6_udur = fields.Float(string='6кВ нийт гаралт өдөр', compute='_compute_all', store=True, digits=(16, 3))
    garalt_niit_6_orgil = fields.Float(string='6кВ нийт гаралт оргил', compute='_compute_all', store=True, digits=(16, 3))
    garalt_niit_6_shunu = fields.Float(string='6кВ нийт гаралт шөнө', compute='_compute_all', store=True, digits=(16, 3))
    garalt_niit_6_niit = fields.Float(string='6кВ нийт гаралт нийт', compute='_compute_all', store=True, digits=(16, 3))

    aldagdal_35_udur = fields.Float(string='35кВ тр-ын алдагдал өдөр', compute='_compute_all', store=True, digits=(16, 3))
    aldagdal_35_orgil = fields.Float(string='35кВ тр-ын алдагдал оргил', compute='_compute_all', store=True, digits=(16, 3))
    aldagdal_35_shunu = fields.Float(string='35кВ тр-ын алдагдал шөнө', compute='_compute_all', store=True, digits=(16, 3))
    aldagdal_35_niit = fields.Float(string='35кВ тр-ын алдагдал нийт', compute='_compute_all', store=True, digits=(16, 3))

    aldagdal_6_udur = fields.Float(string='6кВ ХБ алдагдал өдөр', compute='_compute_all', store=True, digits=(16, 3))
    aldagdal_6_orgil = fields.Float(string='6кВ ХБ алдагдал оргил', compute='_compute_all', store=True, digits=(16, 3))
    aldagdal_6_shunu = fields.Float(string='6кВ ХБ алдагдал шөнө', compute='_compute_all', store=True, digits=(16, 3))
    aldagdal_6_niit = fields.Float(string='6кВ ХБ алдагдал нийт', compute='_compute_all', store=True, digits=(16, 3))
    
    niit_aldagdal_udur = fields.Float(string='Нийт алдагдал өдөр', compute='_compute_all', store=True, digits=(16, 3))
    niit_aldagdal_orgil = fields.Float(string='Нийт алдагдал оргил', compute='_compute_all', store=True, digits=(16, 3))
    niit_aldagdal_shunu = fields.Float(string='Нийт алдагдал шөнө', compute='_compute_all', store=True, digits=(16, 3))
    niit_aldagdal_niit = fields.Float(string='Нийт алдагдал нийт', compute='_compute_all', store=True, digits=(16, 3))
    
    # huvi nemev
    aldagdal_35_udur_per = fields.Float(string='35кВ хувь тр-ын алдагдал өдөр', compute='_compute_all', store=True, digits=(16, 2))
    aldagdal_35_orgil_per = fields.Float(string='35кВ хувь тр-ын алдагдал оргил', compute='_compute_all', store=True, digits=(16, 2))
    aldagdal_35_shunu_per = fields.Float(string='35кВ хувь тр-ын алдагдал шөнө', compute='_compute_all', store=True, digits=(16, 2))
    aldagdal_35_niit_per = fields.Float(string='35кВ  хувь тр-ын алдагдал нийт', compute='_compute_all', store=True, digits=(16, 2))

    aldagdal_6_udur_per = fields.Float(string='6кВ ХБ хувь алдагдал өдөр', compute='_compute_all', store=True, digits=(16, 2))
    aldagdal_6_orgil_per = fields.Float(string='6кВ ХБ хувь алдагдал оргил', compute='_compute_all', store=True, digits=(16, 2))
    aldagdal_6_shunu_per = fields.Float(string='6кВ ХБ хувь алдагдал шөнө', compute='_compute_all', store=True, digits=(16, 2))
    aldagdal_6_niit_per = fields.Float(string='6кВ ХБ хувь алдагдал нийт', compute='_compute_all', store=True, digits=(16, 2))
    
    niit_aldagdal_udur_per = fields.Float(string='Нийт хувь алдагдал өдөр', compute='_compute_all', store=True, digits=(16, 2))
    niit_aldagdal_orgil_per = fields.Float(string='Нийт хувь алдагдал оргил', compute='_compute_all', store=True, digits=(16, 2))
    niit_aldagdal_shunu_per = fields.Float(string='Нийт хувь алдагдал шөнө', compute='_compute_all', store=True, digits=(16, 2))
    niit_aldagdal_niit_per = fields.Float(string='Нийт хувь алдагдал нийт', compute='_compute_all', store=True, digits=(16, 2))
    
    niit_orolt = fields.Float(string='Нийт оролт', compute='_compute_all', store=True, digits=(16, 3))
    niit_orolt_per = fields.Float(string='Нийт оролт хувь', compute='_compute_parent_per', store=True, digits=(16, 2))
    
    @api.depends('parent_id')
    def _compute_parent_per(self):
        for item in self:
            tot2 = 0
            if item.parent_id:
                tot2 = float(item.parent_id.tolgoi_niit)-float(item.parent_id.niit_35_aldagdal)
            if item.type in ['company_department','technic']:
                item.niit_orolt_per = item.niit_orolt/tot2*100 if tot2!=0 else 0
            else:
                item.niit_orolt_per = 0

    @api.depends('lines')
    def _compute_all(self):
        for item in self:
            tot = 0
            if item.type=='station' and item.lines.filtered(lambda r: r.object_id.orolt=='35'):
                tot = sum(item.lines.filtered(lambda r: r.object_id.orolt=='35').mapped('hats_kv'))
            else:
                tot = sum(item.lines.mapped('hats_kv'))
            item.niit_orolt = tot

            tot = sum(item.lines.filtered(lambda r: not r.object_id.orolt and r.tarip=='udur').mapped('hats_kv'))
            item.garalt_niit_6_udur = tot
            tot = sum(item.lines.filtered(lambda r: not r.object_id.orolt and r.tarip=='orgil').mapped('hats_kv'))
            item.garalt_niit_6_orgil = tot
            tot = sum(item.lines.filtered(lambda r: not r.object_id.orolt and r.tarip=='shunu').mapped('hats_kv'))
            item.garalt_niit_6_shunu = tot
            tot = item.garalt_niit_6_udur + item.garalt_niit_6_orgil + item.garalt_niit_6_shunu
            item.garalt_niit_6_niit = tot
            tot2 = sum(item.lines.filtered(lambda r: r.object_id.orolt=='35' and r.tarip=='udur').mapped('hats_kv'))
            tot = tot2-sum(item.lines.filtered(lambda r: r.object_id.orolt=='6' and r.tarip=='udur').mapped('hats_kv'))
            item.aldagdal_35_udur = tot
            tot = item.aldagdal_35_udur/tot2*100 if tot2!=0 else 0
            item.aldagdal_35_udur_per = tot
            
            tot2 = sum(item.lines.filtered(lambda r: r.object_id.orolt=='35' and r.tarip=='orgil').mapped('hats_kv'))
            tot = tot2-sum(item.lines.filtered(lambda r: r.object_id.orolt=='6' and r.tarip=='orgil').mapped('hats_kv'))
            item.aldagdal_35_orgil = tot
            tot = item.aldagdal_35_orgil/tot2*100 if tot2!=0 else 0
            item.aldagdal_35_orgil_per = tot

            tot2 = sum(item.lines.filtered(lambda r: r.object_id.orolt=='35' and r.tarip=='shunu').mapped('hats_kv'))
            tot = tot2-sum(item.lines.filtered(lambda r: r.object_id.orolt=='6' and r.tarip=='shunu').mapped('hats_kv'))
            item.aldagdal_35_shunu = tot
            tot = item.aldagdal_35_shunu/tot2*100 if tot2!=0 else 0
            item.aldagdal_35_shunu_per = tot

            tot = item.aldagdal_35_udur + item.aldagdal_35_orgil + item.aldagdal_35_shunu
            item.aldagdal_35_niit = tot
            tot2 = sum(item.lines.filtered(lambda r: r.object_id.orolt=='35').mapped('hats_kv'))
            item.aldagdal_35_niit_per = item.aldagdal_35_niit/tot2*100 if tot2!=0 else 0

            tot2 = sum(item.lines.filtered(lambda r: r.object_id.orolt=='6' and r.tarip=='udur').mapped('hats_kv'))
            tot = tot2-item.garalt_niit_6_udur
            item.aldagdal_6_udur = tot
            tot = item.aldagdal_6_udur/tot2*100 if tot2!=0 else 0
            item.aldagdal_6_udur_per = tot
            
            tot2 = sum(item.lines.filtered(lambda r: r.object_id.orolt=='6' and r.tarip=='orgil').mapped('hats_kv'))
            tot = tot2-item.garalt_niit_6_orgil
            item.aldagdal_6_orgil = tot
            tot = item.aldagdal_6_orgil/tot2*100 if tot2!=0 else 0
            item.aldagdal_6_orgil_per = tot

            tot2 = sum(item.lines.filtered(lambda r: r.object_id.orolt=='6' and r.tarip=='shunu').mapped('hats_kv'))
            tot = tot2-item.garalt_niit_6_shunu
            item.aldagdal_6_shunu = tot
            tot = item.aldagdal_6_shunu/tot2*100 if tot2!=0 else 0
            item.aldagdal_6_shunu_per = tot

            tot = item.aldagdal_6_udur + item.aldagdal_6_orgil + item.aldagdal_6_shunu
            item.aldagdal_6_niit = tot
            tot2 = sum(item.lines.filtered(lambda r: r.object_id.orolt=='6').mapped('hats_kv'))
            item.aldagdal_6_niit_per = item.aldagdal_6_niit/tot2*100 if tot2!=0 else 0


            tot = item.aldagdal_6_udur + item.aldagdal_35_udur
            item.niit_aldagdal_udur = tot
            tot2 = sum(item.lines.filtered(lambda r: r.object_id.orolt=='35' and r.tarip=='udur').mapped('hats_kv'))
            item.niit_aldagdal_udur_per = item.niit_aldagdal_udur/tot2*100 if tot2!=0 else 0

            tot = item.aldagdal_6_orgil + item.aldagdal_35_orgil
            item.niit_aldagdal_orgil = tot
            tot2 = sum(item.lines.filtered(lambda r: r.object_id.orolt=='35' and r.tarip=='orgil').mapped('hats_kv'))
            item.niit_aldagdal_orgil_per = item.niit_aldagdal_orgil/tot2*100 if tot2!=0 else 0

            tot = item.aldagdal_6_shunu + item.aldagdal_35_shunu
            item.niit_aldagdal_shunu = tot
            tot2 = sum(item.lines.filtered(lambda r: r.object_id.orolt=='35' and r.tarip=='shunu').mapped('hats_kv'))
            item.niit_aldagdal_shunu_per = item.niit_aldagdal_shunu/tot2*100 if tot2!=0 else 0

            tot = item.niit_aldagdal_udur + item.niit_aldagdal_orgil + item.niit_aldagdal_shunu
            item.niit_aldagdal_niit = tot
            tot2 = sum(item.lines.filtered(lambda r: r.object_id.orolt=='35').mapped('hats_kv'))
            item.niit_aldagdal_niit_per = item.niit_aldagdal_niit/tot2*100 if tot2!=0 else 0
            
    @api.onchange('station_id','type')
    def onc_station(self):
        # if not self.lines:
        res = {'domain': {'station_id': [('main_type','=','group')]}}
        if self.type=='station':
            objs = self.env['power.category'].search([('is_hats','=',True),('main_type','=','asset'),('id','child_of',self.station_id.id)], order='orolt desc')
            lines = []
            for item in objs:
                temp = (0,0,{'object_id': item.id, 'tarip':'udur'})
                lines.append(temp)
                temp = (0,0,{'object_id': item.id, 'tarip':'orgil'})
                lines.append(temp)
                temp = (0,0,{'object_id': item.id, 'tarip':'shunu'})
                lines.append(temp)
            self.lines = lines
        if self.type in ['company_department','technic']:
            objs = self.env['power.selection'].search([('is_hats','=',True),('type','=',self.type)])
            lines = []
            for item in objs:
                temp = (0,0,{'object_selection_id': item.id, 'tarip':'udur'})
                lines.append(temp)
                temp = (0,0,{'object_selection_id': item.id, 'tarip':'orgil'})
                lines.append(temp)
                temp = (0,0,{'object_selection_id': item.id, 'tarip':'shunu'})
                lines.append(temp)
            self.lines = lines

        if self.type=='asset':
            res = {'domain': {'station_id': [('main_type','=','asset')]}}
        return res

    def action_to_draft(self):
        self.state = 'draft'
    
    def action_to_done(self):
        self.state = 'done'
        

    @api.depends('date','type')
    def _compute_name(self):
        for item in self:
            s_date = item.date or ''
            cname = '%s'%(dict(self._fields['type'].selection).get(item.type))
            item.name = s_date+' '+cname

class power_hats_line(models.Model):
    _name = 'power.hats.line'
    _description = 'power hats line'
    _order = 'sequence desc'

    sequence = fields.Integer('Дараалал', default=1)
    parent_id = fields.Many2one('power.hats', string='Бүртгэл', ondelete='cascade')
    date = fields.Date(related='parent_id.date', store=True, readonly=True)
    station_id = fields.Many2one('power.category', related='parent_id.station_id', store=True, readonly=True)
    object_id = fields.Many2one('power.category', string='ФИДЕР')
    object_selection_id = fields.Many2one('power.selection', string='фидер')
    coef = fields.Integer(string='КОЭФ')
    zaalt_e = fields.Float(string='ЗААЛТ ЭХНИЙ', digits=(16, 3))
    zaalt_s = fields.Float(string='ЗААЛТ СҮҮЛИЙН', digits=(16, 3))
    hats_kv = fields.Float(string='ХАЦ кВт.ц', compute='_compute_hats_kv', store=True, digits=(16, 3))
    tarip = fields.Selection([('udur','өдөр'),('orgil','оргил'),('shunu','шөнө')], string='Тариф', required=True)
    orolt = fields.Selection([('6','6 Оролт'),('35','35 Оролт')], related='object_id.orolt', string='Оролт', readonly=True,)
    user1plus = fields.Boolean('Хэрэглэгч 1+', default=False)
    user1plusdirect = fields.Boolean('Хэрэглэгч 1+ шууд', default=False)
    user2plus = fields.Boolean('Хэрэглэгч 2+', default=False)
    user3plus = fields.Boolean('Хэрэглэгч 3+', default=False)

    @api.depends('zaalt_e','zaalt_s')
    def _compute_hats_kv(self):
        for item in self:
            item.hats_kv = (item.zaalt_s-item.zaalt_e)*item.coef

    # tur haav Dulguun oruulav
    # @api.constrains('tarip', 'object_id', 'object_selection_id')
    # def _validate_tarip(self):
    #     for item in self:
    #         if item.object_id and self.env['power.hats.line'].search([('id','!=',item.id),('tarip','=',item.tarip),('parent_id','=',item.parent_id.id),('object_id','=',item.object_id.id)]):
    #             raise UserError(u'Тариф давхардаж болохгүй {0} {1} {2}'.format(item.display_name,item.tarip, item.object_id.display_name))
    #         if item.object_selection_id and self.env['power.hats.line'].search([('id','!=',item.id),('tarip','=',item.tarip),('parent_id','=',item.parent_id.id),('object_selection_id','=',item.object_selection_id.id)]):
    #             raise UserError(u'Тариф давхардаж болохгүй {0} {1} {2} .'.format(item.display_name,item.tarip, item.object_selection_id.display_name))
            