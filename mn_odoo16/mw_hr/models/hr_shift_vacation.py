# -*- coding: utf-8 -*-
import datetime
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

import os
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import xlsxwriter
from io import BytesIO
import base64
DATETIME_FORMAT = "%Y-%m-%d"
DATE_FORMAT = "%Y-%m-%d"

class ShiftVacationRequest(models.Model):
    _name = "shift.vacation.request"
    _description = "Shift Vacation Request"
    _inherit = ['mail.thread']
    _order = 'payslip_date'

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    def unlink(self):
        for bl in self:
            if bl.state_type != 'draft':
                raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
        return super(ShiftVacationRequest, self).unlink()

    name = fields.Char(string='Нэр')
    year = fields.Char(string=u'Жил', required=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Ажилтан', default=_default_employee, required=True)
    department_id = fields.Many2one('hr.department', string=u'Хэлтэс')
    job_id = fields.Many2one('hr.job', string='Албан тушаал')
    company_id = fields.Many2one('res.company', string='Компани',
                                 default=lambda self: self.env.user.company_id)
    in_company_date = fields.Date(
        string='Компанид ажилд орсон огноо', readonly=True)
    before_shift_vac_date = fields.Date(
        string='Өмнө жил ЭА цалин авсан огноо', readonly=True)
    this_vac_date = fields.Date(
        string='Хуваарьт ЭА цалин авах огноо', readonly=True)
    payslip_date = fields.Date(
        string='ЭАЦалин авах огноо', tracking=True, required=True)
    is_personally = fields.Boolean(
        string='Биеэр эдлэх бол чагтална уу', default=False)
    count_day = fields.Char(string='Амрах хоног', readonly=True)
    con_day = fields.Float(string='Ногдох хоног', readonly=True,
                           compute='_compute_con_day', store=True)
    desc = fields.Char(string='Тайлбар', tracking=True)
    is_con = fields.Boolean(string='Ногдуулж авах эсэх?', default=True)
    create_date = fields.Date(string='Үүсгэсэн огноо',
                              readonly=True, default=fields.Date.context_today)
    state = fields.Selection([('draft', 'Ноорог'), ('send', 'Илгээсэн'), ('confirm', 'Хянасан'), (
        'done', 'Баталсан'), ('cancel', 'Цуцалсан')], 'Төлөв', default='draft', readonly=True, tracking=True)

    work_year_bef = fields.Date(string='Ажлын жил')
    startdate = fields.Date(string='Эхлэх огноо')
    enddate = fields.Date(string='Дуусах огноо')
    days = fields.Float('Нийт хоног', compute="_compute_day", readonly=True,store=True, default=0, digits=(2, 1), tracking=True)

    def daterange(self, startdate, enddate):
        for n in range(int((enddate - startdate).days)+1):
            yield startdate + timedelta(n)
            
    @api.depends('startdate', 'enddate')
    def _compute_day(self):
        st_d = 0
        en_d = 0
        for item in self:
            if item.startdate and item.enddate:
                st_d = datetime.strptime(
                    str(item.startdate), DATETIME_FORMAT).date()
                en_d = datetime.strptime(
                    str(item.enddate), DATETIME_FORMAT).date()
                days_count = 0
                day_too = 0
                for single_date in item.daterange(st_d, en_d):
                    days_count += 1 if single_date.weekday() < 5 else 0
                    day_too = days_count
                item.days = day_too

    @api.onchange('in_company_date')
    def onchange_work_year(self):
        today = date.today()
        if self.in_company_date:
            if self.in_company_date.year == today.year:
                self.work_year_bef = self.in_company_date.replace(
                    today.year + 1)
            else:
                self.work_year_bef = self.in_company_date.replace(today.year)

    @api.onchange('create_date')
    def onchange_create_date(self):
        if self.create_date:
            self.year = self.create_date.year

    @api.depends('is_con', 'payslip_date', 'before_shift_vac_date', 'count_day')
    def _compute_con_day(self):
        for item in self:
            if item.is_con == True and item.payslip_date and item.before_shift_vac_date and item.count_day:
                date1 = datetime.strptime(
                    str(item.before_shift_vac_date), "%Y-%m-%d")
                date2 = datetime.strptime(str(item.payslip_date), "%Y-%m-%d")
                delta = date2-date1
                item.con_day = delta.days * float(item.count_day)/365
            else:
                item.con_day = float(item.count_day)

    @api.depends('employee_id')
    def _onchange_request_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id

    @api.onchange('employee_id')
    def _onchange_request_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id
            self.in_company_date = self.employee_id.engagement_in_company
            self.before_shift_vac_date = self.employee_id.before_shift_vac_date
            self.count_day = self.employee_id.days_of_annualleave
            self.this_vac_date = self.employee_id.before_year_shipt_leave_date

    def action_send(self):
        total_year = timedelta(days=0)
        year = 0
        month = 0
        emp = self.env['hr.employee'].search(
            [('id', '=', self.employee_id.id)], limit=1)
        if self.before_shift_vac_date:
            s_date = datetime.strptime(
                str(self.before_shift_vac_date), "%Y-%m-%d")
            e_date = datetime.strptime(str(self.payslip_date), "%Y-%m-%d")
            dur = e_date - s_date
            total_year += dur
            year = (total_year.days/365)
            month = ((total_year.days-(total_year.days/365*365))/30)
            months = year * 12 + month
            if months < 6:
                raise UserError(_('%s кодтой ажилтан өмнө жил ээлжийн амралт эдлээд 6 сар болоогүй учир ээлжийн амралт "%s" огноонд авах боломжгүй.Хүний нөөц-д хандана уу!!') %
                                (self.employee_id.identification_id, self.payslip_date))
        elif emp.engagement_in_company and not emp.before_shift_vac_date:
            s_date = datetime.strptime(
                str(emp.engagement_in_company), "%Y-%m-%d")
            e_date = datetime.strptime(str(self.payslip_date), "%Y-%m-%d")
            dur = e_date - s_date
            total_year += dur
            year = (total_year.days/365)
            month = ((total_year.days-(total_year.days/365*365))/30)
            months = year * 12 + month
            if months < 6:
                raise UserError(_(u'"%s" кодтой ажилтан өмнө жил ээлжийн амралт эдлээд 6 сар болоогүй учир ээлжийн амралт "%s" огноонд авах боломжгүй.Хүний нөөц-д хандана уу!!') %
                                (self.employee_id.identification_id, self.payslip_date))
        else:
            raise UserError(_(
                            u'"%s" кодтой ажилтан өмнө жил ээлжийн амралт эдэлсэн огноог оруулна уу!!') % (self.employee_id.identification_id))
        self.write({'state': 'send'})

    # Dynamic flow
    def _get_dynamic_flow_line_id(self):
        return self.flow_find().id

    def _get_default_flow_id(self):
        search_domain = []
        search_domain.append(('model_id.model', '=', 'shift.vacation.request'))
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        if self.holiday_status_id.type == 'non_shift':
            self.is_non = True
        else:
            self.is_non = False

    is_non = fields.Boolean('Is non', default=False)
    history_ids = fields.One2many(
        'dynamic.flow.history', 'shift_id', 'Түүхүүд')
    flow_id = fields.Many2one('dynamic.flow', string='Урсгалын тохиргоо', tracking=True,
                              default=_get_default_flow_id, copy=False,
                              domain="[('model_id.model', '=', 'shift.vacation.request')]", required=True)

    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
                                   default=_get_dynamic_flow_line_id, copy=False,
                                   domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'shift.vacation.request')]")

    flow_line_next_id = fields.Many2one(
        'dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True, store=True)
    stage_id = fields.Many2one(
        'dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='State', store=True)
    state_type = fields.Char(
        string='State type', compute='_compute_state_type', store=True)
    next_state_type = fields.Char(
        string='Дараагийн төлөв', compute='_compute_next_state_type')
    is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
    flow_line_back_id = fields.Many2one(
        'dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
    branch_id = fields.Many2one(
        'res.branch', 'Салбар', default=lambda self: self.env.user.branch_id)
    confirm_user_ids = fields.Many2many(
        'res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True, readonly=True)
    back_user_leave_ids = fields.Many2many(
        'res.users', 'back_users_hr_shift_rel', string='Буцаасан Хэрэглэгчид', store=True, readonly=True)

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

    def action_next_stage(self):
        self.action_send()
        next_flow_line_id = self.flow_line_id._get_next_flow_line()
        if next_flow_line_id:
            if next_flow_line_id._get_check_ok_flow(self.branch_id, self.employee_id.sudo().department_id, self.employee_id.user_id):
                self.flow_line_id = next_flow_line_id
                self.env['dynamic.flow.history'].create_history(
                    next_flow_line_id, 'shift_id', self)
                self.send_chat_employee1(
                    self.sudo().employee_id.partner_id)
                if self.flow_line_next_id:
                    send_users = self.flow_line_next_id._get_flow_users(
                        self.branch_id, self.employee_id.sudo().department_id, self.sudo().employee_id.user_id)
                    if send_users:
                        self.send_chat_next_users(
                            send_users.mapped('partner_id'))

            else:
                con_user = next_flow_line_id._get_flow_users(
                    self.branch_id, False)
                confirm_usernames = ''
                if con_user:
                    confirm_usernames = ', '.join(
                        con_user.mapped('display_name'))
                raise UserError(
                    u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)

    def send_chat_next_users(self, partner_ids):
        state = self.flow_line_id.name
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        action_id = self.env.ref('mw_hr.action_shift_vacation_request').id
        html = u'<b>ЭА хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
            self.sudo().employee_id.name)
        html = u"""<span style='font-size:10pt; color:green;'><b><a target="_blank" href=%s/web#id=%s&form&model=shift.vacation.request&action=%s>%s</a></b> - ажилтан ЭА олговрын хүсэлт <b>%s</b> төлөвт орлоо""" % (
            base_url, self.id, action_id, self.employee_id.name, state)
        self.flow_line_id.send_chat(html, partner_ids)

    def send_chat_employee(self, partner_ids):
        state = self.flow_line_id.name
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        action_id = self.env.ref('mw_hr.action_shift_vacation_request').id
        html = u'<b>ЭА хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
            self.employee_id.name)
        html += u"""<b><a target="_blank"  href=%s/web#id=%s&form&model=shift.vacation.request&action=%s></a></b>ЭА хүсэлт буцаагдан <b>%s</b> төлөвт орлоо""" % (
            base_url, self.id, action_id, state)
        self.flow_line_id.send_chat(html, partner_ids, True)

    def send_chat_employee1(self, partner_ids):
        state = self.flow_line_id.name
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        action_id = self.env.ref('mw_hr.action_shift_vacation_request').id
        html = u'<b>ЭА хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
            self.employee_id.name)
        html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=shift.vacation.request&action=%s></a></b> ЭА хүсэлт <b>%s</b> төлөвт орлоо""" % (
            base_url, self.id, action_id, state)
        self.flow_line_id.send_chat(html, partner_ids, True)

    def action_back_stage(self):
        back_flow_line_id = self.flow_line_id._get_back_flow_line()
        next_flow_line_id = self.flow_line_id._get_next_flow_line()
        if back_flow_line_id and next_flow_line_id:
            if next_flow_line_id._get_check_ok_flow(self.employee_id.department_id, self.employee_id.user_id):
                self.flow_line_id = back_flow_line_id
                self.env['dynamic.flow.history'].create_history(
                    back_flow_line_id, 'shift_id', self)
                self.back_user_leave_ids = [(4, self.env.user.id)]
                self.send_chat_employee(
                    self.employee_id.user_id.partner_id)
            else:
                raise UserError(_('Буцаах хэрэглэгч биш байна!'))

    def action_draft_stage(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()

        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
        else:
            raise UserError(_('Ноорог болгох хэрэглэгч биш байна.'))

    @api.depends('flow_line_id.is_not_edit')
    def _compute_is_not_edit(self):
        for item in self:
            item.is_not_edit = item.flow_line_id.is_not_edit

    @api.depends('flow_line_next_id.state_type')
    def _compute_next_state_type(self):
        for item in self:
            item.next_state_type = item.flow_line_next_id.state_type

    @api.depends('flow_line_id.stage_id')
    def _compute_flow_line_id_stage_id(self):
        for item in self:
            item.stage_id = item.flow_line_id.stage_id

    @api.depends('flow_line_id')
    def _compute_state_type(self):
        for item in self:
            item.state_type = item.flow_line_id.state_type

    def flow_find(self, domain=[], order='sequence'):
        search_domain = []
        if self.flow_id:
            search_domain.append(('flow_id', '=', self.flow_id.id))
        else:
            search_domain.append(
                ('flow_id.model_id.model', '=', 'shift.vacation.request'))
        return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1)

    @api.onchange('flow_id')
    def _onchange_flow_id(self):
        if self.flow_id:
            if self.flow_id:
                self.flow_line_id = self.flow_find().id
        else:
            self.flow_line_id = False


class DynamicFlowHistory(models.Model):
    _inherit = 'dynamic.flow.history'

    shift_id = fields.Many2one(
        'shift.vacation.request', string='ЭА Хүсэлт', ondelete='cascade', index=True)


class ShiftVacationPlan(models.Model):
    _name = "shift.vacation.plan"
    _description = "Shift Vacation Plan"
    _inherit = ['mail.thread']

    def unlink(self):
        for bl in self:
            if bl.state != 'draft':
                raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
        return super(ShiftVacationPlan, self).unlink()

    name = fields.Char('Нэр')
    line_ids = fields.One2many('shift.vacation.plan.line', 'plan_id', 'Lines')
    department_id = fields.Many2one('hr.department', string='Хэлтэс')
    year = fields.Char(string='Он', tracking=True)
    state = fields.Selection([('draft', 'Ноорог'), ('send', 'Илгээсэн'), ('done', 'Баталсан'), (
        'cancel', 'Цуцалсан')], 'Төлөв', default='draft', readonly=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Компани',
                                 default=lambda self: self.env.user.company_id, readonly=True)
    work_location_id = fields.Many2one(
        'hr.work.location', string='Ажлын байршил')

    def action_done(self):
        for line in self.line_ids:
            line.write({'state': 'done'})
        self.write({'state': 'done'})

    def action_send(self):

        for line in self.line_ids:
            line.write({'state': 'send'})
        self.write({'state': 'send'})

    def action_draft(self):
        for line in self.line_ids:
            line.write({'state': 'draft'})
        self.write({'state': 'draft'})

    def action_cancel(self):
        for line in self.line_ids:
            line.write({'state': 'cancel'})
        self.write({'state': 'cancel'})

    # excel хэвлэлт
    def action_print(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        file_name = 'Ээлжийн амралтын төлөвлөгөө'

        # CELL styles тодорхойлж байна
        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(11)
        h1.set_font('Times new roman')
        h1.set_align('center')
        h1.set_align('vcenter')

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(10)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#c4d79b')

        content_left = workbook.add_format({'num_format': '###,###,###.##'})
        content_left.set_text_wrap()
        content_left.set_font('Times new roman')
        content_left.set_font_size(9)
        content_left.set_border(style=1)
        content_left.set_align('left')

        content_left_date = workbook.add_format({'num_format': 'YYYY-MM-DD'})
        content_left_date.set_text_wrap()
        content_left_date.set_font('Times new roman')
        content_left_date.set_font_size(9)
        content_left_date.set_border(style=1)
        content_left_date.set_align('left')

        sheet = workbook.add_worksheet(u'Төлөвлөгөө')

        sheet.merge_range(0, 0, 0, 3, u'Байгууллагын нэр:' +
                          ' ' + self.company_id.name, content_left),
        sheet.merge_range(
            3, 0, 3, 8, u'%s ОНЫ ЭЭЛЖИЙН АМРАЛТЫН ТӨЛӨВЛӨГӨӨ' % (self.year), h1)
        rowx = 6
        sheet.merge_range(rowx, 0, rowx+2, 0, u'Д/д', theader),
        sheet.merge_range(rowx, 1, rowx+2, 1, u'Ажилтны код', theader),
        sheet.merge_range(rowx, 2, rowx+2, 2, u'Овог', theader),
        sheet.merge_range(rowx, 3, rowx+2, 3, u'Нэр', theader),
        sheet.merge_range(rowx, 4, rowx+2, 4, u'Албан тушаал', theader),
        sheet.merge_range(rowx, 5, rowx+2, 5, u'Хэлтэс', theader),
        sheet.merge_range(rowx, 6, rowx+2, 6, u'Компанид ажилд орсон огноо', theader),
        sheet.merge_range(rowx, 7, rowx+2, 7,u'Ажлын жил эхлэх огноо', theader),
        sheet.merge_range(rowx, 8, rowx+2, 8,u'Ажлын жил дуусах огноо', theader),
        sheet.merge_range(rowx, 9, rowx+2, 9, u'Улсад ажилласан жил', theader),
        sheet.merge_range(rowx, 10, rowx+2, 10, u'Үндсэн хоног', theader),
        sheet.merge_range(rowx, 11, rowx+2, 11, u'Нэмэлт хоног', theader),
        sheet.merge_range(rowx, 12, rowx+2, 12, u'Нийт амрах хоног', theader),
        sheet.merge_range(rowx, 13, rowx+2, 13,u'Өмнөх ЭА цалин авсан огноо', theader),
        sheet.merge_range(rowx, 14, rowx+2, 14,u'Энэ жил ЭА цалин авах огноо', theader),

        sheet.set_column('A:A', 4)
        sheet.set_column('B:B', 7)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:BB', 10)

        n = 1
        rowx += 3
        e_date=None
        s_date=None
        for data in self.line_ids:
            if data.in_company_date and self.year:
                in_company_date = datetime.strptime(str(data.in_company_date), DATE_FORMAT)    
                e_date = in_company_date.replace(year=int(self.year))
                s_date = e_date - relativedelta(years=1)
                if s_date.date() < data.in_company_date:
                    s_date = data.in_company_date

            sheet.write(rowx, 0, n, content_left)
            sheet.write(
                rowx, 1, data.employee_id.identification_id, content_left)
            sheet.write(rowx, 2, data.employee_id.last_name, content_left)
            sheet.write(rowx, 3, data.employee_id.name, content_left)
            sheet.write(rowx, 4, data.job_id.name, content_left)
            sheet.write(rowx, 5, data.department_id.name, content_left)
            sheet.write(rowx, 6, data.in_company_date, content_left_date)
            sheet.write(rowx, 7, s_date, content_left_date)
            sheet.write(rowx, 8, e_date, content_left_date)
            sheet.write(rowx, 9, data.uls_year, content_left)
            sheet.write(rowx, 10, data.und_day, content_left)
            sheet.write(rowx, 11, data.add_day, content_left)
            sheet.write(rowx, 12, data.count_day, content_left)
            sheet.write(rowx, 13, data.before_shift_vac_date, content_left_date)
            sheet.write(rowx, 14, data.payslip_date, content_left_date)
            rowx += 1
            n += 1
        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create(
            {'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }

    def execute_query(self):
        query = """SELECT 
			department_id,
			job_id,
			employee_id,
			in_company_date,
			before_shift_vac_date,
			payslip_date
			FROM shift_vacation_request
			WHERE year='%s'
			""" % (self.year)
        self.env.cr.execute(query)
        return self.env.cr.fetchall()

    def create_plan_line(self):
        line_pool = self.env['shift.vacation.plan.line']
        if self.line_ids:
            self.line_ids.unlink()
        records = self.execute_query()
        for record in records:
            employee_pool = self.env['hr.employee'].browse(record[2])
            line_data_id = line_pool.create({
                'department_id': record[0],
                'job_id': record[1],
                'employee_id': record[2],
                'plan_id': self.id,
                'in_company_date': record[3],
                'before_shift_vac_date': record[4],
                'payslip_date': record[5],
                'uls_year': employee_pool.sum_uls_work_year,
                'count_day': employee_pool.days_of_annualleave
            })
        return True


class ShiftVacationPlanLine(models.Model):
    _name = "shift.vacation.plan.line"
    _description = "Shift Vacation Plan line"

    plan_id = fields.Many2one('shift.vacation.plan', string='Plan')
    department_id = fields.Many2one('hr.department', string='Хэлтэс')
    job_id = fields.Many2one('hr.job', string='Албан тушаал')
    employee_id = fields.Many2one('hr.employee', string='Ажилтан')
    in_company_date = fields.Date(string='Компанид ажилд орсон огноо')
    before_shift_vac_date = fields.Date(string='Өмнө жил ЭА цалин авсан огноо')
    start_date = fields.Date(string='Эхлэх огноо')
    end_date = fields.Date(string='Дуусах огноо')
    payslip_date = fields.Date(string='Олговор авах огноо')
    und_day = fields.Char(string='Үндсэн хоног',default=15)
    add_day = fields.Char(string='Нэмэлт хоног',compute = 'compute_add_day',store=True)
    count_day = fields.Char(string='Нийт амрах хоног')
    
    uls_year = fields.Char(string='Улсад ажилласан жил')
    state = fields.Selection([('draft', 'Draft'), ('send', 'Send'),
                             ('done', 'Done'), ('cancel', 'Cancel')], 'Төлөв', default='draft')


    @api.depends('und_day', 'count_day')
    def compute_add_day(self):
        for item in self:
            if item.count_day:
                item.add_day = str(int(item.count_day)-int(item.und_day))
            else:
                item.add_day = 0

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id
            self.in_company_date = self.employee_id.engagement_in_company
            self.before_shift_vac_date = self.employee_id.before_shift_vac_date


class ShiftVacationSchedule(models.Model):
    _name = "shift.vacation.schedule"
    _description = "Shift Vacation Schedule"
    _inherit = ['mail.thread']
    _order = 'start_date'

    def unlink(self):
        for bl in self:
            if bl.state != 'draft':
                raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
        return super(ShiftVacationSchedule, self).unlink()

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char('Нэр', required=True, tracking=True)
    start_date = fields.Date('Эхлэх огноо', required=True, tracking=True)
    end_date = fields.Date('Дуусах огноо', required=True, tracking=True)
    import_data = fields.Binary('Exsel file')
    file_fname = fields.Char(string='File name')
    company_id = fields.Many2one(
        'res.company', 'Компани', default=lambda self: self.env.user.company_id, readonly=True, required=True)
    line_ids = fields.One2many(
        'shift.vacation.schedule.line', 'schedule_id', 'Lines')
    state = fields.Selection([('draft', 'Ноорог'), ('send', 'Илгээсэн'), ('confirm', 'ХН менежер баталсан'), (
        'done', 'Санхүү хүлээж авсан')], 'Төлөв', readonly=True, default='draft', tracking=True)
    type = fields.Selection([('plan', 'Төлөвлөгөөнөөс татах'), ('request', 'Хүсэлтээс татах'), (
        'other', 'Ажилтны мэдээллээс')], 'Хаанаас татах сонгоно уу', required=True, default='draft')
    employee_id = fields.Many2one('hr.employee', string=u'Бүртгэсэн ажилтан',
                                  store=True, default=_default_employee, required=True)

    @api.onchange('import_data')
    @api.depends('import_data', 'file_fname')
    def check_file_type(self):
        if self.import_data:
            filename, filetype = os.path.splitext(self.file_fname)

    def action_print(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        file_name = 'Ээлжийн амралтын цалин олгох ажилчид'

        # CELL styles тодорхойлж байна
        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(11)
        h1.set_font('Times new roman')
        h1.set_align('center')
        h1.set_align('vcenter')

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(10)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#c4d79b')

        content_left = workbook.add_format({'num_format': '###,###,###.##'})
        content_left.set_text_wrap()
        content_left.set_font('Times new roman')
        content_left.set_font_size(9)
        content_left.set_border(style=1)
        content_left.set_align('left')

        content_right = workbook.add_format({})
        content_right.set_text_wrap()
        content_right.set_font('Times new roman')
        content_right.set_font_size(9)
        content_right.set_border(style=1)
        content_right.set_align('left')

        content_left_date = workbook.add_format({'num_format': 'YYYY-MM-DD'})
        content_left_date.set_text_wrap()
        content_left_date.set_font('Times new roman')
        content_left_date.set_font_size(9)
        content_left_date.set_border(style=1)
        content_left_date.set_align('left')

        sheet = workbook.add_worksheet(u'ЭА цалин олгох')

        sheet.merge_range(0, 0, 0, 3, u'Байгууллагын нэр:' +
                          ' ' + self.company_id.name, content_right),
        sheet.merge_range(
            3, 0, 3, 8, u'%s ОНЫ %s САРЫН ЭЭЛЖИЙН АМРАЛТЫН ЦАЛИН ОЛГОХ' % (self.start_date.year,self.start_date.month), h1)
        rowx = 6
        sheet.merge_range(rowx, 0, rowx+2, 0, u'Д/д', theader),
        sheet.merge_range(rowx, 1, rowx+2, 1, u'Ажилтны код', theader),
        sheet.merge_range(rowx, 2, rowx+2, 2, u'Овог', theader),
        sheet.merge_range(rowx, 3, rowx+2, 3, u'Нэр', theader),
        sheet.merge_range(rowx, 4, rowx+2, 4, u'Регистрийн дугаар', theader),
        sheet.merge_range(rowx, 5, rowx+2, 5, u'Албан тушаал', theader),
        sheet.merge_range(rowx, 6, rowx+2, 6, u'Хэлтэс', theader),
        sheet.merge_range(rowx, 7, rowx+2, 7,
                          u'Компанид ажилд орсон огноо', theader),
        sheet.merge_range(rowx, 8, rowx+2, 8,
                          u'Ажлын жил эхлэх огноо', theader),
        sheet.merge_range(rowx, 9, rowx+2, 9,
                          u'Ажлын жил дуусах огноо', theader),
        sheet.merge_range(rowx, 10, rowx+2, 10, u'Улсад ажилласан жил', theader),
        sheet.merge_range(rowx, 11, rowx+2, 11, u'Амрах хоног', theader),
        sheet.merge_range(rowx, 12, rowx+2, 12,
                          u'Өмнөх ЭА цалин авсан огноо', theader),
        sheet.merge_range(rowx, 13, rowx+2, 13,
                          u'Энэ жил ЭА цалин авах огноо', theader),

        sheet.set_column('A:A', 4)
        sheet.set_column('B:B', 7)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:BB', 10)

        n = 1
        rowx += 3
        e_date=None
        s_date=None
        for data in self.line_ids:
            if data.in_company_date and self.start_date:
                in_company_date = datetime.strptime(str(data.in_company_date), DATE_FORMAT)    
                e_date = in_company_date.replace(year=int(self.start_date.year))
                s_date = e_date - relativedelta(years=1)
                if s_date.date() < data.in_company_date:
                    s_date = data.in_company_date

            sheet.write(rowx, 0, n, content_left)
            sheet.write(
                rowx, 1, data.employee_id.identification_id, content_left)
            sheet.write(rowx, 2, data.employee_id.last_name, content_left)
            sheet.write(rowx, 3, data.employee_id.name, content_left)
            sheet.write(rowx, 4, data.employee_id.passport_id, content_left)
            sheet.write(rowx, 5, data.job_id.name, content_left)
            sheet.write(rowx, 6, data.department_id.name, content_left)
            sheet.write(rowx, 7, data.in_company_date, content_left_date)
            sheet.write(rowx, 8, s_date, content_left_date)
            sheet.write(rowx, 9, e_date, content_left_date)
            sheet.write(rowx, 10, data.uls_year, content_left)
            sheet.write(rowx, 11, data.count_day, content_left)
            sheet.write(rowx, 12, data.before_shift_vac_date, content_left_date)
            sheet.write(rowx, 13, data.payslip_date, content_left_date)
            rowx += 1
            n += 1
        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create(
            {'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }
    
    

    def create_schedule_line(self):
        line_pool = self.env['shift.vacation.schedule.line']
        if self.line_ids:
            self.line_ids.unlink()
        for obj in self:
            schedule_id = obj.id
            if self.type == 'plan':
                query = """SELECT 
					 department_id,
					 job_id,
					 employee_id,
					 in_company_date,
					 before_shift_vac_date,
					 payslip_date,
					 count_day,
					 state
					 FROM shift_vacation_plan_line
					 WHERE payslip_date>='%s' and payslip_date<='%s' and state='done' 
					 """ % (obj.start_date, obj.end_date)
                self.env.cr.execute(query)
                records = self.env.cr.fetchall()
            elif self.type == 'request':
                query = """SELECT 
					department_id,
					job_id,
					employee_id,
					in_company_date,
					before_shift_vac_date,
					payslip_date,
					company_id,
					con_day
					FROM shift_vacation_request shr
					WHERE payslip_date>='%s' and payslip_date<='%s' and state_type='done'  and company_id=%s
					""" % (obj.start_date, obj.end_date, self.company_id.id)
                self.env.cr.execute(query)
                records = self.env.cr.fetchall()
                minikin = {}
            else:
                query = """SELECT 
					department_id,
					job_id,
					id,
					engagement_in_company,
					name,
					before_year_shipt_leave_date,
					company_id
					FROM hr_employee hr
					WHERE before_year_shipt_leave_date>='%s' and before_year_shipt_leave_date<='%s'  and company_id=%s
					""" % (obj.start_date, obj.end_date, self.company_id.id)
                self.env.cr.execute(query)
                records = self.env.cr.fetchall()
            minikin = {}
            for record in records:
                employee_pool = self.env['hr.employee'].browse(record[2])
                count_day = 0
                if self.type == 'plan':
                    count_day = record[6]
                elif self.type == 'request':
                    count_day = str(record[7])[:4]
                else:
                    count_day = employee_pool.days_of_annualleave

                if employee_pool.is_minikin == True:
                    minikin = 'Хэвийн'
                else:
                    minikin = 'Хэвийн бус'

                line_data_id = line_pool.create({
                    'department_id': record[0],
                    'job_id': record[1],
                    'employee_id': record[2],
                    'schedule_id': schedule_id,
                    'in_company_date': record[3],
                    'before_shift_vac_date': employee_pool.before_shift_vac_date,
                    'payslip_date': record[5],
                    'is_minikin': minikin,
                    'uls_year': employee_pool.sum_uls_work_year,
                    'count_day': count_day,
                })
        return True

    def action_send(self):
        for line in self.line_ids:
            line.write({'state': 'send'})
        self.write({'state': 'send'})

    def action_confirm(self):
        for line in self.line_ids:
            line.write({'state': 'confirm'})
        self.write({'state': 'confirm'})

    def action_done(self):
        for line in self.line_ids:
            line.write({'state': 'done'})
        self.write({'state': 'done'})

    def action_draft(self):
        for line in self.line_ids:
            line.write({'state': 'draft'})
        self.write({'state': 'draft'})


class ShiftVacationScheduleLine(models.Model):
    _name = "shift.vacation.schedule.line"
    _description = "shipt leave schedule line"
    _order = 'in_company_date'

    schedule_id = fields.Many2one('shift.vacation.schedule', string='Schedule')
    department_id = fields.Many2one('hr.department', string='Хэлтэс')
    job_id = fields.Many2one('hr.job', string='Албан тушаал')
    employee_id = fields.Many2one(
        'hr.employee', string='Ажилтан', required=True)
    in_company_date = fields.Date(string='Компанид ажилд орсон огноо')
    payslip_date = fields.Date(string='ЭА цалин авах огноо')
    before_shift_vac_date = fields.Date(string='Өмнө жил ЭА цалин авсан огноо')
    count_day = fields.Char(string='Амрах хоног')
    uls_year = fields.Char(string='Улсад ажилласан жил')

    state = fields.Selection([('draft', 'Ноорог'), ('send', 'ХН хянасан'), ('confirm', 'ХН менежер баталсан'), (
        'done', 'Санхүү хүлээж авсан'), ('cancel', 'Цуцалсан')], 'Төлөв', readonly=True, default='draft')
    is_minikin = fields.Char(string='Ажиллах нөхцөл')

    @api.onchange('employee_id')
    def onchange_request_employee_id(self):
        self.department_id = self.employee_id.department_id
        self.job_id = self.employee_id.job_id
        self.in_company_date = self.employee_id.engagement_in_company
        self.before_shift_vac_date = self.employee_id.before_shift_vac_date
        self.count_day = self.employee_id.days_of_annualleave
        self.uls_year = self.employee_id.sum_uls_work_year
        if self.employee_id.is_minikin == False:
            self.is_minikin = 'Хэвийн'
        else:
            self.is_minikin = 'Хэвийн бус'
