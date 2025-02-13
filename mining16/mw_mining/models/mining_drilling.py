# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from io import BytesIO
import base64
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd

class MiningDrillingPlan(models.Model):
    _name = 'mining.drilling.plan'
    _inherit = ['mail.thread']
    _description = 'Mining Drilling Plan'
    _order = 'date desc'
    state = fields.Selection([('draft','Draft'),('done','Done')], 'State', tracking=True, default='draft')
    date = fields.Date('Date', required=True, default=fields.Date.context_today)
    branch_id = fields.Many2one('res.branch', 'Branch', default=lambda self: self.env.user.branch_id)
    desc = fields.Text('Description')
    drilling_line_ids = fields.One2many('mining.drilling.line', 'drilling_id', 'Drilling Line')
    # shift = fields.Selection([('day','Day'),('night','Night')], 'Shift')
    # user_id = fields.Many2one('res.users', 'Registered', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    # sum_drill_m = fields.Float(compute='_sum_all', string='Niit urumdsun gun m', readonly=True, store=True)
    # sum_tusliin_gun_m = fields.Float(compute='_sum_all', string='Niit tusliin gun m', readonly=True, store=True)
    # sum_count_tsoonog = fields.Integer(compute='_sum_all', string='Hole count', store=True)
    # sum_count_water = fields.Integer(compute='_sum_all', string='Is Water', store=True)
    # sum_count_baarsan = fields.Integer(compute='_sum_all', string='Baarsan', store=True)
    # sum_count_coal = fields.Integer(compute='_sum_all', string='Nuurstei', store=True)
    # sum_count_utg = fields.Float(compute='_sum_all', string='Niit Batalgaajsan gun')
    # # employee_ids = fields.Many2many('hr.employee', 'mining_drilling_hr_employee_rel', 'drilling_id', 'employee_id', 'Employees')
    # location_id = fields.Many2one('mining.location', 'Import block number')


class MiningDrilling(models.Model):
    _name = 'mining.drilling'
    _inherit = ['mail.thread']
    _description = 'Mining Drilling'
    _order = 'date desc'

    name = fields.Char('Name', compute='_compute_name')
    state = fields.Selection([('draft','Draft'),('done','Done')], 'State', tracking=True, default='draft')
    date = fields.Date('Date', required=True, default=fields.Date.context_today)
    branch_id = fields.Many2one('res.branch', 'Branch', default=lambda self: self.env.user.branch_id)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analyst')
    desc = fields.Text('Description')
    drilling_line_ids = fields.One2many('mining.drilling.line', 'drilling_id', 'Drilling Line')
    shift = fields.Selection([('day','Day'),('night','Night')], 'Shift')
    user_id = fields.Many2one('res.users', 'Registered', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)

    sum_drill_m = fields.Float(string='Niit urumdsun gun m', readonly=True)
    sum_tusliin_gun_m = fields.Float(string='Niit tusliin gun m', readonly=True)
    sum_count_tsoonog = fields.Integer(string='Hole count')
    sum_count_water = fields.Integer(string='Is Water')
    sum_count_baarsan = fields.Integer(string='Baarsan')
    sum_count_coal = fields.Integer(string='Nuurstei')
    sum_count_utg = fields.Float(string='Niit Batalgaajsan gun')

    # sum_drill_m = fields.Float(compute='_sum_all', string='Niit urumdsun gun m', readonly=True, store=True)
    # sum_tusliin_gun_m = fields.Float(compute='_sum_all', string='Niit tusliin gun m', readonly=True, store=True)
    # sum_count_tsoonog = fields.Integer(compute='_sum_all', string='Hole count', store=True)
    # sum_count_water = fields.Integer(compute='_sum_all', string='Is Water', store=True)
    # sum_count_baarsan = fields.Integer(compute='_sum_all', string='Baarsan', store=True)
    # sum_count_coal = fields.Integer(compute='_sum_all', string='Nuurstei', store=True)
    # sum_count_utg = fields.Float(compute='_sum_all', string='Niit Batalgaajsan gun')

    # employee_ids = fields.Many2many('hr.employee', 'mining_drilling_hr_employee_rel', 'drilling_id', 'employee_id', 'Employees')
    import_data = fields.Binary('Import excel', copy=False)
    export_data = fields.Binary('Export excel file')
    drill_technic_id = fields.Many2one('technic.equipment', 'Drilling machine',required=True)
    location_id = fields.Many2one('mining.location', 'Блокийн Дугаар', copy=False)
    drill_diameter_mm = fields.Float(related='drill_technic_id.bucket_capacity', string='Drilling diameter', store=True, readonly=True)

    employee_id = fields.Many2one('hr.employee', 'Operator')
    employee_sub_id = fields.Many2one('hr.employee', 'Assist')

    fuel = fields.Float('Авсан түлш')
    start_motoh = fields.Float('Start odometer')
    end_motoh = fields.Float('End odometer')
    work_motoh = fields.Float('Working odometer', compute='_compute_work_motoh', store=True)
    is_area = fields.Boolean('Талбайгүй', default=False, help=u'Талбайгүй бол чагтална')
    expense_line_ids = fields.One2many('mining.drilling.expense.line', 'drilling_id', 'Drilling Expense Line')

    from_hole = fields.Integer(string='Цооногоос')
    for_hole = fields.Integer(string='Цооногт')
    stone_type = fields.Selection([('f1','f=6-14'),('f2','f>14'),('f3','f=6-16'),('f4','f>16'),('f5','f<14')], 'Rock hardness')

    # @api.constrains('date', 'shift', 'location_id', 'drill_technic_id')
    # def _check_date_validate_drilling(self):
    #     drilling = self.env['mining.drilling']
    #     for item in self:
    #         if drilling.search([('date','=',item.date), ('shift','=',item.shift), ('location_id','=',item.location_id.id), ('drill_technic_id','=',item.drill_technic_id.id),('id','!=',item.id)]):
    #             raise UserError(u' %s өдөр %s ээлжинд %s блок дээр %s техник давхар бүртгэгдсэн байна'% (item.date, item.shift, item.location_id.name, item.drill_technic_id.name))

    def unlink(self):
        for item in self:
            if item.state!='draft':
                raise UserError(u'Ноорог биш баримтыг устгахгүй')

        return super(MiningDrilling, self).unlink()

    @api.depends('start_motoh','end_motoh')
    def _compute_work_motoh(self):
        for item in self:
            item.work_motoh = item.end_motoh - item.start_motoh

    @api.depends('date','branch_id')
    def _compute_name(self):
        for item in self:
            item.name = item.branch_id.name+' '+str(item.date)

    @api.depends('drilling_line_ids.bodit_urumdsun_gun_m',
        'drilling_line_ids.is_water',
        'drilling_line_ids.is_baarah',
        'drilling_line_ids.nuurs_ehelsen_gun_m')
    def _sum_all(self):
        for item in self:
            sum_drill = 0.0
            sum_water = 0
            sum_baarsan = 0
            sum_coal = 0
            sum_count_tsoonog = 0
            sum_count_utg = 0.0
            sum_tusliin_gun_m = 0.0
            for line in item.drilling_line_ids.filtered(lambda r: r.is_production == True):
                sum_drill += line.bodit_urumdsun_gun_m
                sum_count_utg += float(line.urtaashd_tootsoh_gun_m)
                sum_count_tsoonog +=1
                sum_tusliin_gun_m += line.tusliin_gun_m
                if line.is_water:
                    sum_water += 1
                if line.is_baarah:
                    sum_baarsan += 1
                if line.nuurs_ehelsen_gun_m > 0:
                    sum_coal += 1

            item.sum_drill_m = sum_drill
            item.sum_count_tsoonog = sum_count_tsoonog
            item.sum_count_water = sum_water
            item.sum_count_baarsan = sum_baarsan
            item.sum_count_coal = sum_coal
            item.sum_count_utg = sum_count_utg
            item.sum_tusliin_gun_m = sum_tusliin_gun_m


    def action_done(self):
        self.write({'state':'done'})


    def action_draft(self):
        self.write({'state':'draft'})


    def action_create_line(self):
        if not self.from_hole  or not self.for_hole:
            raise UserError(u'Цоонгоо оруул!!')

        for item in range(self.from_hole, self.for_hole+1):
            if not self.drilling_line_ids.filtered(lambda r: r.hole == item):
                self.env['mining.drilling.line'].create({
                    'hole': item,
                    'drilling_id': self.id,
                    })


    def action_import_hole(self):
        if not self.import_data:
            raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')

        fileobj = NamedTemporaryFile('w+')
        fileobj.write(base64.decodestring(self.import_data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise osv.except_osv(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        book = xlrd.open_workbook(fileobj.name)

        try :
            sheet = book.sheet_by_index(0)
        except:
            raise osv.except_osv(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
        nrows = sheet.nrows

        rowi = 6
        line_obj = self.env['mining.drilling.line']
        emp_obj = self.env['hr.employee']
        for item in range(rowi,nrows):
            row = sheet.row(item)
            hole = row[0].value
            tusliin_gun_m = row[1].value
            bodit_urumdsun_gun_m = row[2].value

            hatuu_chuluulag_ehelsen_gun_m = row[3].value
            hatuu_chuluulag_duussan_gun_m = row[4].value
            nuurs_ehelsen_gun_m = row[5].value
            nuurs_duussan_gun_m = row[6].value
            is_water = True if row[7].value else False
            is_baarah = True if row[8].value else False
            description = row[9].value
            line_id = self.drilling_line_ids.filtered(lambda r: r.hole==hole)
            if line_id:
                line_id.write({
                    'tusliin_gun_m': tusliin_gun_m,
                    'bodit_urumdsun_gun_m': bodit_urumdsun_gun_m,
                    'hatuu_chuluulag_ehelsen_gun_m': hatuu_chuluulag_ehelsen_gun_m,
                    'hatuu_chuluulag_duussan_gun_m': hatuu_chuluulag_duussan_gun_m,
                    'nuurs_ehelsen_gun_m': nuurs_ehelsen_gun_m,
                    'nuurs_duussan_gun_m': nuurs_duussan_gun_m,
                    'is_water': is_water,
                    'is_baarah': is_baarah,
                    'description': description,
                    })
            else:
                line_obj.create({
                    'drilling_id': self.id,
                    'hole': hole,
                    'tusliin_gun_m': tusliin_gun_m,
                    'bodit_urumdsun_gun_m': bodit_urumdsun_gun_m,
                    'hatuu_chuluulag_ehelsen_gun_m': hatuu_chuluulag_ehelsen_gun_m,
                    'hatuu_chuluulag_duussan_gun_m': hatuu_chuluulag_duussan_gun_m,
                    'nuurs_ehelsen_gun_m': nuurs_ehelsen_gun_m,
                    'nuurs_duussan_gun_m': nuurs_duussan_gun_m,
                    'is_water': is_water,
                    'is_baarah': is_baarah,
                    'description': description,
                    })


    def action_export(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(u'Гүйцэтгэл')

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(9)
        h1.set_align('center')
        h1.set_font_name('Arial')

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#9ad808')
        header.set_text_wrap()
        header.set_font_name('Arial')

        header_wrap = workbook.add_format({'bold': 1})
        header_wrap.set_text_wrap()
        header_wrap.set_font_size(11)
        header_wrap.set_align('center')
        header_wrap.set_align('vcenter')
        header_wrap.set_border(style=1)
        # header_wrap.set_fg_color('#6495ED')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_right = workbook.add_format()
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)
        contest_right.set_num_format('#,##0.00')

        contest_center = workbook.add_format()
        contest_center.set_text_wrap()
        contest_center.set_font_size(9)
        contest_center.set_align('center')
        contest_center.set_align('vcenter')
        contest_center.set_border(style=1)
        contest_center.set_font_name('Arial')

        cell_format2 = workbook.add_format({
        'border': 1,
        'align': 'right',
        'font_size':9,
        'font_name': 'Arial',
        # 'text_wrap':1,
        'num_format':'#,####0'
        })


        row = 0
        last_col = 9
        worksheet.merge_range(row, 0, row, last_col, u'"'+self.branch_id.name+'"'+u' Төсөл', header_wrap)

        row += 1
        worksheet.merge_range(row, 0, row, last_col, u'Өрөмдлөгийн гүйцэтгэлийн бүртгэл импортолох загвар', contest_center)

        row += 1
        worksheet.merge_range(row, 0, row, last_col, self.drill_technic_id.name+u' Өрмийн машины '+self.location_id.name+u' өрөмдсөн цооног хүлээн авсан акт', contest_center)

        row += 1
        # /Өмнөговь аймаг, Ноён сум/
        worksheet.merge_range(row, 0, row, last_col-4, self.branch_id.address or self.branch_id.name, contest_left)
        worksheet.merge_range(row, last_col-3, row, last_col, self.date, contest_right)
        row += 1
        worksheet.merge_range(row, 0, row, last_col-4, u'', contest_left)
        worksheet.merge_range(row, last_col-3, row, last_col, u'Цооногийн диаметр='+str(self.drill_diameter_mm), contest_right)
        row += 1

        worksheet.write(row, 0, u"Цооногийн дугаар", header)
        worksheet.write(row, 1, u"Өрөмдөх гүн, м", header)
        worksheet.write(row, 2, u"Өрөмдсөн гүн, м", header)
        worksheet.write(row, 3, u"Хатуу чулуулаг эхэлсэн гүн", header)
        worksheet.write(row, 4, u"Хатуу чулуулаг дууссан гүн", header)
        worksheet.write(row, 5, u"Нүүрс эхэлсэн гүн", header)
        worksheet.write(row, 6, u"Нүүрс дууссан гүн", header)
        worksheet.write(row, 7, u"Устай эсэх", header)
        worksheet.write(row, 8, u"Баарсан эсэх", header)
        worksheet.write(row, 9, u"Нэмэлт тайлбар", header)

        for item in self.drilling_line_ids:
            row+=1
            worksheet.write(row, 0, item.hole, cell_format2)
            worksheet.write(row, 1, item.tusliin_gun_m, cell_format2)
            worksheet.write(row, 2, item.bodit_urumdsun_gun_m, cell_format2)
            worksheet.write(row, 3, item.hatuu_chuluulag_ehelsen_gun_m, cell_format2)
            worksheet.write(row, 4, item.hatuu_chuluulag_duussan_gun_m, cell_format2)
            worksheet.write(row, 5, item.nuurs_ehelsen_gun_m, cell_format2)
            worksheet.write(row, 6, item.nuurs_duussan_gun_m, cell_format2)
            worksheet.write(row, 7, '1' if item.is_water else '', cell_format2)
            worksheet.write(row, 8, '1' if item.is_baarah else '', cell_format2)
            worksheet.write(row, 9, item.description if item.description else '', cell_format2)

        workbook.close()

        out = base64.encodebytes(output.getvalue())
        excel_id = self.write({'export_data': out})

        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=mining.drilling&id=" + str(self.id) + "&filename_field=filename&download=true&field=export_data&filename=" + self.name+'.xlsx',
             'target': 'new',
        }
class MiningDrillingLine(models.Model):
    _name = 'mining.drilling.line'
    _description = 'Mining Drilling Line'

    drilling_id = fields.Many2one('mining.drilling', 'Drilling', ondelete='cascade')
    hole = fields.Integer('Hole', required=True)

    tusliin_gun_m = fields.Float(string='Tusliin gun')
    bodit_urumdsun_gun_m = fields.Float('Urumdsun gun')
    urtaashd_tootsoh_gun_m = fields.Float('Batalgaajsan urtaash')
    hatuu_chuluulag_ehelsen_gun_m = fields.Float('Hatuu chuluulag ehelsen gun')
    hatuu_chuluulag_duussan_gun_m = fields.Float('Hatuu chuluulag duussan gun')
    nuurs_ehelsen_gun_m = fields.Float('Nuurs ehelsen gun')
    nuurs_duussan_gun_m = fields.Float('Nuurs duussan gun')
    is_water = fields.Boolean('Is Water')
    is_baarah = fields.Boolean('Baarsan eseh')
    description = fields.Text('Description')
    is_production = fields.Boolean('Is Production', default=True)

    # employee_id = fields.Many2one('hr.employee', 'Drilling man')
    # employee_sub_id = fields.Many2one('hr.employee', 'Drilling sub man')

    blast_line_ids = fields.One2many('mining.blast.line', 'drilling_line_id', 'Blast Line')

class MiningDrillingExpenseLine(models.Model):
    _name = 'mining.drilling.expense.line'
    _description = 'Mining Drilling Expens Line'

    drilling_id = fields.Many2one('mining.drilling', 'Drilling', ondelete='cascade')

    quantity = fields.Float('Quantity')
    product_id = fields.Many2one('product.product', 'Product', required=True)


