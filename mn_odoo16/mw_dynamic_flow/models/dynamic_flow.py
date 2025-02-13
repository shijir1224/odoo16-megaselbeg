# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class res_company(models.Model):
    _inherit = 'res.company'

    main_user_ids = fields.One2many('res.users', 'company_id', string='Main users')


class ResUsers(models.Model):
    _inherit = 'res.users'
    _description = 'Res users'

    # Columns
    manager_user_ids = fields.Many2many('res.users', 'res_user_manager_users_rel', 'user_id', 'manager_id',
                                        string='Батлах хэрэглэгчид',
                                        )

    flow_line_ids = fields.Many2many('dynamic.flow.line', 'dynamic_flow_line_res_users_rel', 'user_id', 'flow_id',
                                     string='Урсгалууд')


class DynamicFlow(models.Model):
    _name = 'dynamic.flow'
    _description = 'Dynamic Flow'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    branch_ids = fields.Many2many('res.branch', string='Салбарууд', )
    line_ids = fields.One2many('dynamic.flow.line', 'flow_id', string='Line', required=True, copy=True)
    categ_ids = fields.Many2many('product.category', 'dynamic_flow_product_categ_rel', 'flow_id', 'categ_id',
                                 string='Category', copy=True)
    #     type = fields.Selection([('purchase_request','Purchase Request')], string='Type',)
    model_id = fields.Many2one('ir.model', string="Model name", help="Your model name")
    is_amount = fields.Boolean(string="Мөнгөн дүгээс хамаарсан", default=False)
    # is_amount_all = fields.Boolean(string="Мөнгөн дүгээс хамаарсан ALL", default=False)
    amount_price_min = fields.Float(string='Мөнгөн дүнгээс бага', default=0)
    amount_price_max = fields.Float(string='Мөнгөн дүнгээс их', default=0)
    user_ids = fields.Many2many('res.users', 'dynamic_flow_allowed_users_rel', 'flow_id', 'user_id',
                                string='Хэрэглэгчид')
    active = fields.Boolean(default=True)
    activity_ok = fields.Boolean(default=True, string='Activity Ok')
    company_id = fields.Many2one('res.company', string="Компани", default=lambda self: self.env.user.company_id)


class DynamicFlowLine(models.Model):
    _name = 'dynamic.flow.line'
    _description = 'Dynamic Flow Line'
    _order = 'sequence, id'
    _rec_name = 'stage_id'

    def _get_default_sequence(self):
        return self.env['ir.sequence'].next_by_code('dynamic.flow.line') or 1

    # name = fields.Char(string='Name', size=128)
    name = fields.Char(related='stage_id.name')
    stage_id = fields.Many2one('dynamic.flow.line.stage', string='Төлөв')
    flow_id = fields.Many2one('dynamic.flow', string='Dynamic Flow', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', required=True, default=_get_default_sequence)
    state_type = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
        ('invoice', 'Invoice'),
        ('master', 'Master'),
        ('parts_user', 'Parts user'),
        ('senior', 'Senior'),
        ('engineer', 'Engineer'),
        ('chief', 'Chief'),
        ('inactive', 'inactive'),
    ], string='State type', index=True)
    amount_price_min = fields.Float(string='Мөнгөн дүнгээс бага', default=0)
    amount_price_max = fields.Float(string='Мөнгөн дүнгээс их', default=0)
    is_not_edit = fields.Boolean(string='Is Not Edit', default=False)
    is_required = fields.Boolean(string='Is Required', default=False)
    type = fields.Selection(
        [('fixed', 'Fixed'), ('group', 'Group'), ('user', 'User'), ('all', 'All'), ('none', 'None')], string='Type',
        required=True, default='group')
    user_id = fields.Many2one('res.users', string='User')
    user_ids = fields.Many2many('res.users', 'dynamic_flow_line_res_users_rel', 'flow_id', 'user_id',
                                string='Хэрэглэгчид')
    group_id = fields.Many2one('res.groups', string='Group')
    is_print = fields.Boolean(string='Is Print', default=False)
    is_mail = fields.Boolean(string='Is Mail', default=False)
    is_activity_with_mail = fields.Boolean(string='Activity мэйлтэй нь хамт илгээх', default=False)
    is_mail_batlah = fields.Boolean(string='Батлах товч майлээр харуулах', default=False)
    check_type = fields.Selection(
        [('department', 'Хэлтэсийн менежер'), ('branch', 'Салбар менежер'), ('manager', 'Тухайн хүний менежер')],
        string='Шалгах төрөл')

    flow_line_next_id = fields.Many2one('dynamic.flow.line', 'Дараагийн төлөв', compute='_compute_flow_line_id')
    flow_line_back_id = fields.Many2one('dynamic.flow.line', 'Өмнөх төлөв', compute='_compute_flow_line_id')
    company_id = fields.Many2one('res.company', string="Компани", related='flow_id.company_id')

    @api.onchange('state_type')
    def onch_state_type(self):
        if self.state_type == 'done':
            self.is_not_edit = True

    @api.depends('sequence', 'flow_id', 'state_type')
    def _compute_flow_line_id(self):
        for item in self:
            item.flow_line_next_id = item._get_next_flow_line()
            item.flow_line_back_id = item._get_back_flow_line()

    def _get_flow_users(self, branch_id=False, department_id=False, user_id=False):
        ret_users = False
        u_ids = False
        if self.type in ['fixed', 'user']:
            ret_users = self.user_ids
        elif self.type == 'group':
            ret_users = self.group_id.users
        elif self.type == 'all':
            ret_users = self.user_ids + self.group_id.users

        if ret_users and self.check_type:
            if self.check_type == 'department':
                if not department_id:
                    raise ValidationError(
                        u'%s Урсгалд Хэлтэс явуулаагүй байна %s %s %s' % (self.name, branch_id, department_id, user_id))
                u_ids = department_id.manager_ids.mapped('user_id')
                if not ret_users.filtered(lambda r: r.id in u_ids.ids):
                    raise ValidationError(u'"%s" төлөвийн Хэлтэсийн менежер сонгогдоогүй байна' % self.name)
                return ret_users.filtered(lambda r: r.id in u_ids.ids)
            elif self.check_type == 'branch':
                if not branch_id:
                    raise ValidationError(u'%s Урсгалд Салбар явуулаагүй байна' % self.name)
                return ret_users.filtered(lambda r: r.id == branch_id.user_id.id)
            elif self.check_type == 'manager':
                # TODO тухайн төлөв дээр байгаа хэн ч баталж болоод байгаа учир дарлаа
                # if self.env.user.id in ret_users.ids:
                #     return self.env.user
                if not user_id:
                    raise ValidationError(u'%s Урсгалд Хэрэглэгч явуулаагүй байна' % self.name)
                if not ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids):
                    raise ValidationError(
                        u'"%s" төлөвийн %s Хэрэглэгч дээр менежер сонгогдоогүй байна' % (self.name, user_id.name))
                return ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids)
        return ret_users

    def _get_check_ok_flow(self, branch_id=False, department_id=False, user_id=False):
        if self.type == 'none':
            return True
        check_users = self._get_flow_users(branch_id, department_id, user_id)
        if check_users:
            if self.env.user.id in check_users.ids:
                return True
        # if self.type=='fixed' and check_users:
        #     if self.env.user.id in check_users.ids:
        #         return True
        # if self.type=='group' and check_users:
        #     if self.env.user.id in self.group_id.users.ids:
        #         return True
        # if self.type=='all' and check_users:
        #     if self.env.user.id in self.user_ids.ids or self.env.user.id in self.group_id.users.ids:
        #         return True
        # if self.type=='none':
        #     return True
        return False

    def _get_next_flow_line(self, flow_line_ids=False):
        if self.id:
            if flow_line_ids:
                next_flow_line_id = self.env['dynamic.flow.line'].search([
                    ('flow_id', '=', self.flow_id.id),
                    ('id', '!=', self.id),
                    ('sequence', '>', self.sequence),
                    ('sequence', 'in', flow_line_ids.mapped('sequence')),
                    ('state_type', 'not in', ['cancel']),
                ], limit=1)
                return next_flow_line_id
            else:
                next_flow_line_id = self.env['dynamic.flow.line'].search([
                    ('flow_id', '=', self.flow_id.id),
                    ('id', '!=', self.id),
                    ('sequence', '>', self.sequence),
                    ('state_type', 'not in', ['cancel']),
                ], limit=1)
                return next_flow_line_id
        else:
            return False

    def _get_back_flow_line(self, flow_line_ids=False):
        if self.id:
            if flow_line_ids:
                back_flow_line_id = self.env['dynamic.flow.line'].search([
                    ('flow_id', '=', self.flow_id.id),
                    ('id', '!=', self.id),
                    ('sequence', '<', self.sequence),
                    ('sequence', 'in', flow_line_ids.mapped('sequence')),
                    ('state_type', 'not in', ['cancel']),
                ], limit=1)
                return back_flow_line_id
            else:
                back_flow_line_id = self.env['dynamic.flow.line'].search([
                    ('flow_id', '=', self.flow_id.id),
                    ('id', '!=', self.id),
                    ('sequence', '<', self.sequence),
                    ('state_type', 'not in', ['cancel']),
                ], limit=1, order="sequence desc")
            return back_flow_line_id
        return False

    def _get_inactive_flow_line(self):
        flow_line_id = self.env['dynamic.flow.line'].search([
            ('flow_id', '=', self.flow_id.id),
            ('id', '!=', self.id),
            ('state_type', '=', 'inactive'),
        ], limit=1)
        return flow_line_id

    def _get_cancel_flow_line(self):
        flow_line_id = self.env['dynamic.flow.line'].search([
            ('flow_id', '=', self.flow_id.id),
            ('id', '!=', self.id),
            ('state_type', '=', 'cancel'),
        ], limit=1)
        return flow_line_id

    def _get_draft_flow_line(self):
        flow_line_id = self.env['dynamic.flow.line'].search([
            ('flow_id', '=', self.flow_id.id),
            ('id', '!=', self.id),
            ('state_type', '=', 'draft'),
        ], limit=1)
        return flow_line_id

    def _get_done_flow_line(self):
        flow_line_id = self.env['dynamic.flow.line'].search([
            ('flow_id', '=', self.flow_id.id),
            ('id', '!=', self.id),
            ('state_type', '=', 'done'),
        ], limit=1)
        return flow_line_id

    def _get_batlah_tovch(self):
        return _('Батлах')

    def _get_harah_tovch(self):
        return _('Харах')

    def send_chat(self, html, partner_ids, with_mail=False, subject_mail=False, obj_id=False, attachment_ids=[]):
        if not partner_ids:
            if self.type == 'none':
                return True
            raise UserError(u'Мэдэгдэл хүргэх харилцагч байхгүй байна {0}'.format(self.name))

        channel_obj = self.env['mail.channel']
        is_mail_batlah = False
        html_mail = False
        # attachment_ids = False
        if self.flow_line_next_id and not with_mail:
            with_mail = self.flow_line_next_id.is_mail
            subject_mail = (str(self.flow_id.model_id.name) or '') + ':' + (self.name or '')
            if obj_id:
                subject_mail += ' ' + str(obj_id.display_name)

                if attachment_ids:
                    attachment_ids = self.env['ir.attachment'].sudo().search(
                        [('id', 'in', attachment_ids), ('res_model', '!=', self.flow_id.model_id.model)]).ids

                attachmentIDs = self.env['ir.attachment'].sudo().search(
                    [('res_id', '=', obj_id.id), ('res_model', '=', self.flow_id.model_id.model)]).ids

                _logger.info('-------before send attachment_ids--------%s' % attachment_ids)
                if attachmentIDs:
                    attachment_ids += attachmentIDs
                _logger.info('-------send cattachment_ids--------%s +++++++%s' % (attachment_ids, len(attachment_ids)))

            is_mail_batlah = self.flow_line_next_id.is_mail_batlah
            if is_mail_batlah and obj_id:
                if obj_id:
                    template = self.env['pdf.template.generator'].search(
                        [('model_id', '=', self.flow_id.model_id.id), ('name', '=', 'mail_batlah')], limit=1)
                    if not template:
                        template = self.env['pdf.template.generator'].search(
                            [('model_id', '=', self.flow_id.model_id.id), ('name', '=', 'default')], limit=1)
                    action_id = self.env['ir.actions.act_window'].search(
                        [('res_model', '=', str(self.flow_id.model_id.model))], limit=1).id or ''
                    if template:
                        dbname = self._cr.dbname
                        base_url = self.get_base_url()
                        translate_value = self._get_batlah_tovch()
                        translate_value_harah = self._get_harah_tovch()
                        com_str_id = ''
                        try:
                            com_str_id = '&amp;cids=%s' % obj_id.company_id.id
                        except Exception as ee:
                            _logger.info('-------ERROR company_id.gui--------%s' % ee)
                        html_mail = """
                        <div style="text-align: center; margin: 16px 0px 16px 0px;">
                        <a style="padding: 5px 10px; color: #FFFFFF; text-decoration: none; background-color: #875A7B; border: 1px solid #875A7B; border-radius: 3px" href="{0}/flow/action_next_stage?db={1}&amp;model_name={2}&amp;id={3}&amp;user_id_id=user_base_id_id&amp;flow_line_id={4}" target="_blank">{5}</a>
                        <a style="padding: 5px 10px; color: #FFFFFF; text-decoration: none; background-color: #875A7B; border: 1px solid #875A7B; border-radius: 3px" href="{0}/web?db={1}#&amp;id={3}{8}&amp;view_type=form&amp;model={2}&amp;action={7}" target="_blank">{6}</a>
                        </div>
                        

                        """.format(base_url, dbname, str(self.flow_id.model_id.model), obj_id.id,
                                   obj_id.flow_line_id.id, translate_value, translate_value_harah, action_id,
                                   com_str_id)
                        html_mail += template.get_template_data_html(obj_id.id)
                        # print ('html_mail',html_mail)
                        # res
                        # return res
                    # else:
                    #     raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

                # html_mail = 'False--------'
        self.env['res.users'].send_chat(html, partner_ids, with_mail, subject_mail, html_mail, attachment_ids)

    def send_chat_html(self, obj_id, name=''):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        obj = self.env['ir.actions.act_window']
        action_id = obj.search([('res_model', '=', self.flow_id.model_id.model)], limit=1)
        obj_main_id = obj_id
        html = u"""<b>{7}<br/><a target="_blank" href={0}/web#id={1}&view_type=form&model={2}&action={3}>{4}</a></b> <b>{5}</b> Төлөвт орлоо {6}""".format(
            base_url, str(obj_main_id.id), str(self.flow_id.model_id.model), str(action_id.id),
            str(obj_main_id.display_name), self.display_name, name, self.flow_id.model_id.display_name)
        return html


class DynamicFlowLineStage(models.Model):
    _name = 'dynamic.flow.line.stage'
    _description = 'Dynamic Flow Line Stage'
    _order = 'name'

    name = fields.Char('Нэр', required=True, translate=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Name must be unique!')
    ]


class dynamic_flow_history(models.Model):
    _name = 'dynamic.flow.history'
    _description = 'Dynamic Flow history'
    _order = 'date desc'

    user_id = fields.Many2one('res.users', 'Өөрчилсөн Хэрэглэгч', index=True)
    date = fields.Datetime('Огноо', default=fields.Datetime.now, index=True)
    flow_line_id = fields.Many2one('dynamic.flow.line', 'Төлөв', index=True)
    model_id = fields.Many2one('ir.model', string="Model name", index=True, store=True, compute='com_flow_line_id')
    spend_time = fields.Float(string='Зарцуулсан цаг',
                              compute='compute_spend_time',
                              store=True,
                              readonly=True, digits=(16, 2), index=True)
    spend_day = fields.Float(string='Зарцуулсан хоног',
                             store=True,
                             compute='compute_spend_time',
                             readonly=True, digits=(16, 0), index=True)
    company_id = fields.Many2one('res.company', string="Компани", default=lambda self: self.env.user.company_id,
                                 store=True)
    job_id  = fields.Many2one('hr.job', string="Албан тушаал", store=True, compute='comp_job_id')
    decision_description = fields.Char(string='Батлагчын тайлбар') 

    @api.depends('user_id')
    def comp_job_id(self):
        if self.user_id:
            for item in self:
                emp_id = self.env['hr.employee'].search([
                        ('user_id', '=', item.user_id.id)], limit=1)
                if emp_id:
                    item.job_id = emp_id.job_id.id
    @api.depends('flow_line_id')
    def com_flow_line_id(self):
        for item in self:
            item.model_id = item.flow_line_id.flow_id.model_id.id or False

    def create_activity(self, html, users, mode_obj, res_id, flow_line_id=False):
        activity_type_id = self.env['ir.config_parameter'].sudo().get_param('mail_activity_type_mw')
        if not activity_type_id:
            activity_type_id = self.env['mail.activity.type'].search([('icon', '=', 'fa-tasks'),('res_model','=',False)], limit=1)
            if activity_type_id:
                activity_type_id = activity_type_id.id
        if activity_type_id:
            activty_type = self.env['mail.activity.type'].browse(activity_type_id)
            for item in users:
                try:
                    vals = {
                        'activity_type_id': activty_type.id,
                        'res_model_id': self.env['ir.model'].search([('model', '=', mode_obj)], limit=1).id,
                        'res_id': res_id,
                        'note': '',
                        # 'note': html or '',
                        'user_id': item.id,
                    }
                    if flow_line_id and not flow_line_id.is_activity_with_mail:
                        a_id = self.env['mail.activity'].with_context(mail_activity_quick_update=True).create(vals)
                    else:
                        a_id = self.env['mail.activity'].create(vals)
                except Exception as e:
                    _logger.info('-------ERROR create_activity_____create_activity--------%s' % e)

    def done_activity(self, mode_obj, res_id):
        for ac in self.env['mail.activity'].search([('res_id', '=', res_id), ('res_model', '=', mode_obj)]):
            ac.action_done()

    # @api.depends('date')
    def compute_spend_time(self, field_name_str, field_id):
        for obj in self.env['dynamic.flow.history'].search([(field_name_str, '=', field_id.id)]):
            domains = []
            if field_name_str and field_id:
                domains = [(field_name_str, '=', field_id.id), ('id', '!=', obj.id), ('date', '<', obj.date)]
            if domains and isinstance(obj.id, int):
                ll = self.env['dynamic.flow.history'].search(domains, order='date desc', limit=1)
                if ll:
                    diff_date = obj.date - ll.date
                    secs = diff_date.total_seconds()
                    obj.spend_time = secs / 3600
                    obj.spend_day = diff_date.days
                else:
                    obj.spend_time = 0
                    obj.spend_day = 0
            else:
                obj.spend_time = 0
                obj.spend_day = 0

    def create_history(self, flow_line_id, field_name_str, field_id):
        # print(assa)
        com_id = self.env.user.company_id.id
        try:
            if field_id.company_id:
                com_id = field_id.company_id.id
        except Exception as e:
            _logger.info('-------ERROR create_history --------%s' % e)

        vals = {
            'user_id': self.env.user.id,
            'date': datetime.now(),
            'flow_line_id': flow_line_id.id,
            'company_id': com_id,
            field_name_str: field_id.id,
        }
        self.compute_spend_time(field_name_str, field_id)
        return self.env['dynamic.flow.history'].create(vals)
