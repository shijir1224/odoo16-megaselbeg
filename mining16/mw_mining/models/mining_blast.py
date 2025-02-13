# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
import base64
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd

class MiningBlastPlan(models.Model):
    _name = 'mining.blast.plan'
    _inherit = ['mail.thread']
    _description = 'Mining Blast Plan'
    _order = 'date desc'

    @api.model
    def _default_type(self):
        context = dict(self._context or {})
        plan_type = context.get('plan_type', False)
        if plan_type=='master':
            return 'master'
        return 'forecast'

    name = fields.Char('Name', compute='_compute_name', store=True)
    state = fields.Selection([('draft','Draft'),('done','Done')], 'State', tracking=True, default='draft')
    date = fields.Datetime('Date', required=True, default=fields.Date.context_today)
    branch_id = fields.Many2one('res.branch', 'Салбар')
    desc = fields.Text('Description')
    blast_line_ids = fields.One2many('mining.blast.plan.line', 'blast_id', 'Blast Line',copy=True)
    rock_type = fields.Selection([('soft','Soft'),('medium','Medium'),('hard','Hard')], 'Rock type')
    bit_size = fields.Integer('Bit size')
    location_id = fields.Many2one('mining.location', 'Блок')
    location_ids = fields.Many2many('mining.location', 'mining_location_blast_plan_rel', 'plan_id', 'loc_id', 'Блок')
    avarage_pf = fields.Float('Avarage PF', group_operator='avg')
    area_level = fields.Char('Blasted area level', size=9)
    blast_volume = fields.Float('Blast volume, m3')
    tsoongiin_zai = fields.Float('Distance between holes')
    egnee_zai = fields.Float('Distance between lines')
    hole_count = fields.Integer('Number of holes')
    type = fields.Selection([('master','Master'),('forecast','Normal')], 'Plan type', default=_default_type)

    actual_ids = fields.One2many('mining.blast', 'plan_id', 'Гүйцэтгэлүүд')
    product_id = fields.Many2one('product.product', 'Уулын цул')
    searhc_product_id = fields.Many2one('product.product', related='blast_line_ids.product_id')
    @api.depends('date','branch_id','desc')
    def _compute_name(self):
        for item in self:
            # item.branch_id.name or '',str(item.date) or
            item.name = '%s %s %s ' % (item.branch_id.name,item.date,item.desc)
    def action_done(self):
        self.write({'state':'done'})

    def action_draft(self):
        self.write({'state':'draft'})

class MiningBlastPlanLine(models.Model):
    _name = 'mining.blast.plan.line'
    _description = 'Mining Blast Plan Line'

    blast_id = fields.Many2one('mining.blast.plan', 'Blast Plan', ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product')
    quantity = fields.Float('Quantity')


class MiningBlast(models.Model):
    _name = 'mining.blast'
    _inherit = ['mail.thread']
    _description = 'Mining Blast'
    _order = 'date desc'

    name = fields.Char('Blast Number', required=True)
    state = fields.Selection([('draft','Draft'),('done','Done')], 'State', tracking=True, default='draft')
    date = fields.Datetime('Date', required=True, default=fields.Date.context_today)
    branch_id = fields.Many2one('res.branch', 'Branch')
    desc = fields.Text('Description')
    blast_line_ids = fields.One2many('mining.blast.line', 'blast_id', 'Blast Line')
    expense_line_ids = fields.One2many('mining.blast.expense.line', 'blast_id', 'Blast Expense Line')
    shift = fields.Selection([('day','Day'),('night','Night')], 'Shift')
    rock_type = fields.Selection([('soft','Soft'),('medium','Medium'),('hard','Hard')], 'Rock type')
    bit_size = fields.Integer('Bit size')
    location_id = fields.Many2one('mining.location', 'Block')
    location_ids = fields.Many2many('mining.location', 'mining_location_blast_rel', 'blast_id', 'loc_id', 'Блок')
    avarage_pf = fields.Float('Avarage PF', group_operator='avg')
    area_level = fields.Char('Blasted area level', size=9)
    blast_volume = fields.Float('Blast volume, m3')
    import_data = fields.Binary('Import excel', copy=False)

    plan_id = fields.Many2one('mining.blast.plan', 'Plan')
    tsoongiin_zai = fields.Float('Distance between holes')
    egnee_zai = fields.Float('Distance between lines')
    hole_count = fields.Integer('Number of holes')
    dundaj_butlagdal = fields.Float('Average crushing rate')

    anfo_qty = fields.Float('Anfo', compute='_compute_anfo_qty')
    emulsion_qty = fields.Float('Emulsion', compute='_compute_anfo_qty')
    product_id = fields.Many2one('product.product', 'Уулын цул')
    searhc_product_id = fields.Many2one('product.product', related='expense_line_ids.product_id')

    @api.depends('expense_line_ids')
    def _compute_anfo_qty(self):
        anfo_ids = self.env['mining.blast.product'].search([('type','=','anfo')]).mapped('product_id')
        emulsion_ids = self.env['mining.blast.product'].search([('type','=','emulsion')]).mapped('product_id')
        for item in self:
            item.anfo_qty = sum(item.expense_line_ids.filtered(lambda r: r.product_id.id in anfo_ids.ids).mapped('quantity'))
            item.emulsion_qty = sum(item.expense_line_ids.filtered(lambda r: r.product_id.id in emulsion_ids.ids).mapped('quantity'))

    def unlink(self):
        for item in self:
            if item.state!='draft':
                raise UserError(u'Ноорог биш баримтыг устгахгүй')

        return super(MiningBlast, self).unlink()

    def action_done(self):
        self.write({'state':'done'})

    def action_draft(self):
        self.write({'state':'draft'})

    def action_import_hole(self):
        if self.blast_line_ids:
            raise UserError(_('Blast line is not empty'))
        drilling_line = self.env['mining.drilling.line'].search([
            ('drilling_id.branch_id','=',self.branch_id.id),
            ('drilling_id.location_id','=',self.location_id.id),
            ('blast_line_ids','=',False)
            ])
        if not drilling_line:
            raise UserError(_('Not found drilling line'))
        line_obj = self.env['mining.blast.line']
        for item in drilling_line:
            line_obj.create({
                'blast_id': self.id,
                'drilling_line_id': item.id,
                })

    def action_import_excel(self):
        if not self.import_data:
            raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')

        fileobj = NamedTemporaryFile('w+')
        fileobj.write(base64.decodestring(self.import_data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise UserError(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        book = xlrd.open_workbook(fileobj.name)

        try :
            sheet = book.sheet_by_index(0)
        except:
            raise UserError(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
        nrows = sheet.nrows

        rowi = 41
        line_obj = self.env['mining.blast.line']
        emp_obj = self.env['hr.employee']
        for item in range(rowi,rowi+1):
            row = sheet.row(item)

            hole = row[1].value
            if isinstance(int(hole), int):
                line_id = line_obj.search([('hole','=',hole),('blast_id','=',self.id),('anfo_qty','<=',0),('emulsion_qty','<=',0)], limit=1)
                if not line_id:
                    raise UserError (u'%s Дугаартай цооногийн бүртгэл олдсонгүй'%(hole))

                anfo_or_emul = row[8].value
                anfo_qty = 0
                emulsion_qty = 0
                if anfo_or_emul=='ANFO':
                    anfo_qty = row[18].value
                else:
                    emulsion_qty = row[18].value

                line_id.write({
                    'anfo_qty': anfo_qty,
                    'emulsion_qty': emulsion_qty,
                    'bodit_urumdsun_gun_m': bodit_urumdsun_gun_m,
                    'employee_id': employee_id.id,
                    'employee_sub_id': employee_sub_id.id,
                    'hatuu_chuluulag_ehelsen_gun_m': hatuu_chuluulag_ehelsen_gun_m,
                    'hatuu_chuluulag_duussan_gun_m': hatuu_chuluulag_duussan_gun_m,
                    'nuurs_ehelsen_gun_m': nuurs_ehelsen_gun_m,
                    'nuurs_duussan_gun_m': nuurs_duussan_gun_m,
                    'is_water': is_water,
                    'is_baarah': is_baarah,
                    'description': description,
                    })
    @api.onchange('plan_id')
    def onchange_plan_id(self):
        if self.plan_id:
            if not self.branch_id:
                self.branch_id = self.plan_id.branch_id.id
            if not self.date:
                self.date = self.plan_id.date
            if not self.desc:
                self.desc = self.plan_id.desc
            if not self.expense_line_ids:
                tmp = []
                for x in self.plan_id.blast_line_ids:
                    tmp.append((0,0,{'product_id': x.product_id.id, 'quantity': x.quantity}))
                self.expense_line_ids = tmp
            if not self.rock_type:
                self.rock_type = self.plan_id.rock_type
            if not self.bit_size:
                self.bit_size = self.plan_id.bit_size
            if not self.avarage_pf:
                self.avarage_pf = self.plan_id.avarage_pf
            if not self.area_level:
                self.area_level = self.plan_id.area_level
            if not self.blast_volume:
                self.blast_volume = self.plan_id.blast_volume
            if not self.blast_volume:
                self.blast_volume = self.plan_id.blast_volume
            if not self.tsoongiin_zai:
                self.tsoongiin_zai = self.plan_id.tsoongiin_zai
            if not self.egnee_zai:
                self.egnee_zai = self.plan_id.egnee_zai
            if not self.hole_count:
                self.hole_count = self.plan_id.hole_count
            if not self.location_ids:
                self.location_ids = self.plan_id.location_ids




class MiningBlastLine(models.Model):
    _name = 'mining.blast.line'
    _description = 'Mining Blast Line'

    blast_id = fields.Many2one('mining.blast', 'Blast', ondelete='cascade')

    drilling_line_id = fields.Many2one('mining.drilling.line', 'Drilling line', readonly=True)
    hole = fields.Char(related='drilling_line_id.hole', readonly=True)
    tusliin_gun_m = fields.Float(related='drilling_line_id.tusliin_gun_m', readonly=True)
    drill_diameter_mm = fields.Float(related='drilling_line_id.drilling_id.drill_diameter_mm', readonly=True)
    bodit_urumdsun_gun_m = fields.Float(related='drilling_line_id.bodit_urumdsun_gun_m', readonly=True)
    urtaashd_tootsoh_gun_m = fields.Float(related='drilling_line_id.urtaashd_tootsoh_gun_m', readonly=True)
    hatuu_chuluulag_ehelsen_gun_m = fields.Float(related='drilling_line_id.hatuu_chuluulag_ehelsen_gun_m', readonly=True)
    hatuu_chuluulag_duussan_gun_m = fields.Float(related='drilling_line_id.hatuu_chuluulag_duussan_gun_m', readonly=True)
    nuurs_ehelsen_gun_m = fields.Float(related='drilling_line_id.nuurs_ehelsen_gun_m', readonly=True)
    nuurs_duussan_gun_m = fields.Float(related='drilling_line_id.nuurs_duussan_gun_m', readonly=True)
    is_water = fields.Boolean(related='drilling_line_id.is_water', readonly=True)
    is_baarah = fields.Boolean(related='drilling_line_id.is_baarah', readonly=True)
    description = fields.Text(related='drilling_line_id.description', readonly=True)


    hole = fields.Char(string='Hole')
    tusliin_gun_m = fields.Float(string='Төслийн гүн')
    drill_diameter_mm = fields.Float(string='Drill diametr')
    bodit_urumdsun_gun_m = fields.Float(string='Drilled depth')
    urtaashd_tootsoh_gun_m = fields.Float(string='Баталгаажсан уртааш',)
    hatuu_chuluulag_ehelsen_gun_m = fields.Float(string='Хатуу чулуулаг эхэлсэн гүн')
    hatuu_chuluulag_duussan_gun_m = fields.Float(string='Хатуу чулуулаг дууссан гүн')
    nuurs_ehelsen_gun_m = fields.Float(string='Нүүрс эхэлсэн гүн')
    nuurs_duussan_gun_m = fields.Float(string='Нүүрс дууссан гүн')
    is_water = fields.Boolean(string='Устай')
    is_baarah = fields.Boolean(string='Баарсан эсэх')
    description = fields.Text(string='Description')

    gasbag_ok = fields.Boolean('DW/gasbag', default=False) # Газбаг хэрэглэсэн эсэх
    gasbag_liner_ok = fields.Boolean('Gasbag liner', default=False) # Цооногийн уут


    air_deck_bottom = fields.Float('Air deck bottom, m')
    air_deck_top = fields.Float('Air deck top, m')
    stemming = fields.Float('Stemming, m')
    deck_bottom = fields.Float('Charge length bottom')
    deck_medium = fields.Float('Charge length medium')
    deck_top = fields.Float('Charge length top')
    anfo_qty = fields.Float('Anfo', default=0)
    emulsion_qty = fields.Float('Emulsion', default=0)


class MiningBlastExpenseLine(models.Model):
    _name = 'mining.blast.expense.line'
    _description = 'Mining Blast Expens Line'

    blast_id = fields.Many2one('mining.blast', 'Blast', ondelete='cascade')

    quantity = fields.Float('Quantity')
    product_id = fields.Many2one('product.product', 'Product', required=True)

class MiningBlastProduct(models.Model):
    _name = 'mining.blast.product'
    _description = 'Mining Blast product'

    product_id = fields.Many2one('product.product', 'Бараа', required=True)
    type = fields.Selection([('anfo','Анфо'), ('emulsion','Эмульс')], string='Type')

    _sql_constraints = [
        ('product_id_unig', 'UNIQUE(product_id)', 'Product is must UNIQUE!')
    ]

class ProductProduct(models.Model):
    _inherit = 'product.product'

    blast_product_ids = fields.One2many('mining.blast.product', 'product_id', 'Blast products')
