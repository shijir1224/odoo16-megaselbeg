# -*- coding: utf-8 -*-
import datetime
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.mw_base.verbose_format import verbose_format


class HrTr(models.Model):
    _name = 'hr.tr'
    _description = u'Tr'
    _inherit = ['mail.thread']

    type_selection = [('salary', 'Цалингийн тодорхойлолт'),
                      ('work', 'Ажилладаг нь үнэн'), ('other', 'Бусад')]

    def unlink(self):
        for bl in self:
            if bl.state_type not in ('draft'):
                raise UserError(
                    _('Ноорог, илгээсэн төлөвтэй биш бол устгах боломжгүй.'))
        return super(HrTr, self).unlink()

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    wage = fields.Integer(string='Цалин', tracking=True)
    number = fields.Char(string='Дугаарлалт', tracking=True)
    reason = fields.Char(string='Тодорхойлолт авах шалтгаан',
                         required=True, tracking=True)
    create_date = fields.Date(
        string='Огноо', default=fields.Datetime.now(), copy=False, tracking=True)
    engagement_date = fields.Date(string='Ажилд орсон огноо')
    type_in = fields.Selection(
        type_selection, string='Төрөл', required=True, tracking=True)
    to_company = fields.Many2one(
        'to.company', string='Хаана', required=False, tracking=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Ажилтан', default=_default_employee, required=True, tracking=True)
    department_id = fields.Many2one(
        'hr.department', string='Хэлтэс, нэгж', tracking=True)
    job_id = fields.Many2one('hr.job', string='Албан тушаал', tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Компани', related='employee_id.company_id', store=True)
    before_tr_ids = fields.Many2many(
        'hr.tr', string='Өмнө нь авсан тодорхойлолт', compute="before_tr_view")
    wage_ch = fields.Char(string='Үндсэн цалин/хэвлэх/')
    wage_str = fields.Char(string='Үндсэн цалин/үсгээр/', compute='_amount_wage_str')


    @api.onchange('wage')
    def onchange_wage(self):
        if self.wage:
            self.wage_ch = '{0:,.2f}'.format(self.wage).split('.')[0]

    @api.depends('wage')
    def _amount_wage_str(self):
        for line in self:
            if line.wage:
                line.wage_str = verbose_format(abs(line.wage))
            else:
                line.wage_str = ''


    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            contract_id = self.env['hr.contract'].search(
                [('employee_id', '=', self.employee_id.id)], limit=1)
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id
            self.wage = contract_id.wage
            self.engagement_date = self.employee_id.engagement_in_company

    def before_tr_view(self):
        for item in self:
            before_tr = item.env['hr.tr'].search(
                [('employee_id', '=', item.employee_id.id)])
            item.before_tr_ids = before_tr.ids

    def print_to_tr(self):
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'hr.tr')], limit=1)
        template = self.env['pdf.template.generator'].sudo().search(
            [('model_id', '=', model_id.id), ('name', '=', 'tr_print')], limit=1)
        if template:
            res = template.sudo().print_template(self.id)
            return res
        else:
            raise UserError(
                _(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

    def print_tr_not_salary(self):
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'hr.tr')], limit=1)
        template = self.env['pdf.template.generator'].sudo().search(
            [('model_id', '=', model_id.id), ('name', '=', 'not_salary_tr_print')], limit=1)
        if template:
            res = template.sudo().print_template(self.id)
            return res
        else:
            raise UserError(
                _(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

    def year(self, ids):
        line = self.browse(ids)
        sheet_year = str(line.engagement_date).split('-')[0]
        return sheet_year

    def month(self, ids):
        line = self.browse(ids)
        sheet_month = str(line.engagement_date).split('-')[1]
        return sheet_month

    def day(self, ids):
        line = self.browse(ids)
        sheet_day = str(line.engagement_date).split('-')[2]
        return sheet_day

    def amount_str(self, ids):
        line = self.browse(ids)
        list = verbose_format(abs(line.wage))
        return list

    def get_company_logo(self, ids):
        report_id = self.browse(ids)
        image_buf = report_id.employee_id.hr_company_id.image1
        image_str = """<img alt="Embedded Image" width="170" src='data:image/png;base64,%s""" % image_buf+'/>'
        image_str = image_str.replace("base64,b'", "base64,", 1)
        return image_str

    def get_hash(self, ids):
        report_id = self.browse(ids)
        image_buf = report_id.employee_id.hr_company_id.image
        image_str = """<img alt="Embedded Image" width="10" src='data:image/png;base64,%s""" % image_buf+'/>'
        image_str = image_str.replace("base64,b'", "base64,", 1)
        return image_str

    def get_hash1(self, ids):
        report_id = self.browse(ids)
        image_buf = report_id.employee_id.hr_company_id.image2
        image_str = """<img alt="Embedded Image" width="20" src='data:image/png;base64,%s""" % image_buf+'/>'
        image_str = image_str.replace("base64,b'", "base64,", 1)
        return image_str

    # Dynamic flow
    def _get_dynamic_flow_line_id(self):
        return self.flow_find().id

    def _get_default_flow_id(self):
        search_domain = []
        search_domain.append(('model_id.model', '=', 'hr.tr'))
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        if self.holiday_status_id.type == 'non_shift':
            self.is_non = True
        else:
            self.is_non = False

    is_non = fields.Boolean('Is non', default=False)
    history_ids = fields.One2many('dynamic.flow.history', 'tr_id', 'Түүхүүд')
    flow_id = fields.Many2one('dynamic.flow', string='Урсгалын тохиргоо', tracking=True,
                              default=_get_default_flow_id, copy=False,
                              domain="[('model_id.model', '=', 'hr.tr')]", required=True)

    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
                                   default=_get_dynamic_flow_line_id, copy=False,
                                   domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'hr.tr')]")

    flow_line_next_id = fields.Many2one(
        'dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True, store=True)
    stage_id = fields.Many2one(
        'dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='State', store=True)
    state_type = fields.Char(
        string='State type', compute='_compute_state_type', store=True)
    next_state_type = fields.Char(
        string='Дараагийн төлөв', compute='_compute_next_state_type')
    flow_line_back_id = fields.Many2one(
        'dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
    branch_id = fields.Many2one(
        'res.branch', 'Салбар', default=lambda self: self.env.user.branch_id)
    confirm_user_ids = fields.Many2many(
        'res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True, readonly=True)

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
        next_flow_line_id = self.flow_line_id._get_next_flow_line()
        if next_flow_line_id:
            if next_flow_line_id._get_check_ok_flow(self.employee_id.sudo().department_id, self.employee_id.user_id):
                self.flow_line_id = next_flow_line_id
                self.env['dynamic.flow.history'].create_history(
                    next_flow_line_id, 'tr_id', self)
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
        action_id = self.env['ir.model.data'].id
        html = u'<b>Тодорхойлолт хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
            self.sudo().employee_id.name)
        html = u"""<span style='font-size:10pt; color:green;'><b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.tr&action=%s>%s</a></b> - ажилтан тодорхойлолт авах хүсэлт <b>%s</b> төлөвт орлоо""" % (
            base_url, self.id, action_id, self.employee_id.name, state)
        self.flow_line_id.send_chat(html, partner_ids)

    def send_chat_employee(self, partner_ids):
        state = self.flow_line_id.name
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        action_id = self.env['ir.model.data'].id
        html = u'<b>Тодорхойлолт хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
            self.employee_id.name)
        html += u"""<b><a target="_blank"  href=%s/web#id=%s&view_type=form&model=hr.tr&action=%s></a></b>Тодорхойлолт авах хүсэлт буцаагдан <b>%s</b> төлөвт орлоо""" % (
            base_url, self.id, action_id, state)
        self.flow_line_id.send_chat(html, partner_ids)

    def action_back_stage(self):
        back_flow_line_id = self.flow_line_id._get_back_flow_line()
        next_flow_line_id = self.flow_line_id._get_next_flow_line()
        if back_flow_line_id and next_flow_line_id:
            if next_flow_line_id._get_check_ok_flow(self.employee_id.department_id, self.employee_id.user_id):
                self.flow_line_id = back_flow_line_id
                self.env['dynamic.flow.history'].create_history(
                    back_flow_line_id, 'tr_id', self)
                self.send_chat_employee(self.employee_id.user_id.partner_id)
            else:
                raise UserError(_('Буцаах хэрэглэгч биш байна!'))

    def action_draft_stage(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()
        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
        else:
            raise UserError(_('Ноорог болгох хэрэглэгч биш байна.'))

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
            search_domain.append(('flow_id.model_id.model', '=', 'hr.tr'))
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

    tr_id = fields.Many2one('hr.tr', string='Тод Хүсэлт',
                            ondelete='cascade', index=True)


class ToCompany(models.Model):
    _name = 'to.company'
    _description = 'To Company'

    name = fields.Char('Нэр')
