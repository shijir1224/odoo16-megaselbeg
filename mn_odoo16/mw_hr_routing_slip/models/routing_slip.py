from odoo import api, fields, models, _
from odoo.exceptions import UserError

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
class RoutingSlipHr(models.Model):
    _name = "routing.slip.hr"
    _description = 'Routing Slip'
    _inherit = ['mail.thread']
    _order = 'resigned_date desc'

    def unlink(self):
        for bl in self:
            if bl.state_type != 'draft':
                raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
        return super(RoutingSlipHr, self).unlink()

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    def name_get(self):
        res = []
        for item in self:
            if item.res_company_id:
                res_name = ' [' + \
                    item.res_company_id.display_name+']' + '' + item.employee_id.name
                res.append((item.id, res_name))
            else:
                res.append(res_name[0])
        return res

    @api.model
    def _line_item(self):
        cons = self.env['routing.slip.hr.line.item'].search([])
        w = []
        for cc in cons:
            vals = {
                'item_id': cc.id
            }
            w.append(vals)
        return w

    employee_id = fields.Many2one(
        'hr.employee', 'Ажилтны нэр', required=True, default=_default_employee)
    department_id = fields.Many2one(
        'hr.department', 'Алба нэгж',required=True)
    job_id = fields.Many2one('hr.job', 'Албан тушаал',required=True)
    company_id = fields.Many2one('res.company')
    res_company_id = fields.Many2one('res.company', 'Компани', related='employee_id.company_id', store=True, tracking=True)
    num_employee_id = fields.Many2one('hr.employee', 'Ажил хүлээлцэх ажилтан', tracking=True)
    num_department_id = fields.Many2one('hr.department', 'Алба нэгж')
    num_job_id = fields.Many2one('hr.job', 'Албан тушаал')
    engagement_in_company = fields.Date('Ажилд орсон огноо', required=True)
    resigned_date = fields.Date(
        'Ажлаас гарсан огноо', tracking=True, required=True)
    resigned_desc = fields.Text('Ажлаас гарсан шалтгаан', required=True, tracking=True)
    resigned_type = fields.Selection([('type1', 'Ажил олгогчийн санаачилгаар'), ('type2', 'Ажилтны санаачилгаар')], 'Шалтгаан', required=True, tracking=True)
    resigned_type_p = fields.Char(string='Шалтгаан')
    line_ids = fields.One2many('routing.slip.hr.line', 'parent_id', string='Routing slip', default=_line_item)
    employee_lastname = fields.Char(string='Ажилтны овог')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id
            self.engagement_in_company = self.employee_id.engagement_in_company
            self.resigned_date = self.employee_id.work_end_date
            self.resigned_type = self.employee_id.resigned_type
            self.employee_lastname = self.employee_id.last_name[:1]

    @api.onchange('num_employee_id')
    def onchange_num_employee_id(self):
        if self.num_employee_id:
            self.num_department_id = self.num_employee_id.department_id.id
            self.num_job_id = self.num_employee_id.job_id.id
    
    @api.onchange('resigned_type')
    def onchange_resigned_type(self):
        if self.resigned_type:
                if self.resigned_type == 'type1':
                    self.resigned_type_p = 'Ажил олгогчийн санаачилгаар'
                elif self.resigned_type == 'type2':
                    self.resigned_type_p = 'Ажилтны санаачилгаар'

# Dynamic flow - ==================================================

    def _get_dynamic_flow_line_id(self):
        return self.flow_find().id

    def _get_dynamic_flow_next_line_id(self):
        return self.flow_find()._get_next_flow_line()

    def _get_default_flow_id(self):
        search_domain = []
        search_domain.append(('model_id.model', '=', 'routing.slip.hr'))
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    confirm_user_ids = fields.Many2many(
        'res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True, readonly=True)

    flow_id = fields.Many2one('dynamic.flow', string='Урсгал', tracking=True,
                              default=_get_default_flow_id, copy=False,
                              domain="[('model_id.model', '=', 'routing.slip.hr')]")

    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
                                   default=_get_dynamic_flow_line_id, copy=False,
                                   domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'routing.slip.hr')]")
    flow_line_next_id = fields.Many2one(
        'dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True)

    branch_id = fields.Many2one(
        'res.branch', 'Салбар', default=lambda self: self.env.user.branch_id)
    stage_id = fields.Many2one(
        'dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='State', store=True)
    state_type = fields.Char(
        string='State type', compute='_compute_state_type', store=True)
    next_state_type = fields.Char(
        string='Дараагийн төлөв', compute='_compute_next_state_type')
    flow_line_back_id = fields.Many2one(
        'dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
    history_ids = fields.One2many(
        'dynamic.flow.history', 'routing_slip_id', 'Түүхүүд')

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
        if self.num_employee_id and self.state_type == 'draft':
            self.send_chat_num_employee()
        if next_flow_line_id:
            if next_flow_line_id._get_check_ok_flow(self.employee_id.sudo().department_id, self.employee_id.user_id):
                self.flow_line_id = next_flow_line_id
                self.env['dynamic.flow.history'].create_history(
                    next_flow_line_id, 'routing_slip_id', self)
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
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        action_id = self.env.ref('mw_hr_routing_slip.open_view_routing_slip_hr_action').id
        html = u"""<span style='font-size:10pt; color:green;'><b><a target="_blank" href=%s/web#id=%s&view_type=form&model=routing.slip.hr&action=%s>%s</a></b> - ажилтан тойрох хуудас илгээлээ.""" % (
            base_url, self.id, action_id, self.employee_id.name)
        # self.flow_line_id.send_chat(html, partner_ids)

    def send_chat_employee(self, partner_ids):
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        action_id = self.env.ref('mw_hr_routing_slip.open_view_routing_slip_hr_action').id
        html = u'<b>Танд энэ өдрийн мэнд хүргэе.</b><br/><i style="color: red">%s</i> Employeeы үүсгэсэн </br>' % (
            self.employee_id.name)
        html += u"""<b><a target="_blank"  href=%s/web#id=%s&view_type=form&model=routing.slip.hr&action=%s></a></b>тойрох хуудас ирлээ""" % (
            base_url, self.id, action_id)
        # self.flow_line_id.send_chat(html, partner_ids, True)

    def send_chat_num_employee(self):
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        action_id = self.env.ref('mw_hr_routing_slip.open_view_routing_slip_hr_action').id
        html = u'<b>Танд энэ өдрийн мэнд хүргэе.</b><br/><i style="color: red">%s</i> Employeeы үүсгэсэн </br>' % (
            self.employee_id.name)
        html += u"""<b><a target="_blank"  href=%s/web#id=%s&view_type=form&model=routing.slip.hr&action=%s></a></b>тойрох хуудас ирлээ""" % (
            base_url, self.id, action_id)
        # self.flow_line_id.send_chat(
        #     html, self.num_employee_id.partner_id, True)

    def action_back_stage(self):
        back_flow_line_id = self.flow_line_id._get_back_flow_line()
        next_flow_line_id = self.flow_line_id._get_next_flow_line()
        if back_flow_line_id and next_flow_line_id:
            if next_flow_line_id._get_check_ok_flow(self.employee_id.department_id, self.employee_id.user_id):
                self.flow_line_id = back_flow_line_id
                # History uusgeh
                self.env['dynamic.flow.history'].create_history(
                    back_flow_line_id, 'routing_slip_id',self)
                # self.send_chat_employee(self.employee_id.user_id.partner_id)
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
            search_domain.append(
                ('flow_id.model_id.model', '=', 'routing.slip.hr'))
        return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1)

    @api.onchange('flow_id')
    def _onchange_flow_id(self):
        if self.flow_id:
            if self.flow_id:
                self.flow_line_id = self.flow_find().id
        else:
            self.flow_line_id = False
            
    # def write(self,val):
    #     res = super(RoutingSlipHr,self).write(self,val)
    #     i = 0
    #     for line in self.line_ids:
    #         i+=1
    #         line.sequence = i
    #     return res

    def get_user_signature(self, ids):
        report_id = self.browse(ids)
        html = '<table>'
        print_flow_line_ids = report_id.flow_id.line_ids.filtered(
            lambda r: r.is_print)
        history_obj = self.env['dynamic.flow.history']
        for item in print_flow_line_ids:
            his_id = history_obj.search(
                [('flow_line_id', '=', item.id), ('routing_slip_id', '=', report_id.id)], limit=1)
            image_str = '________________________'
            if his_id.user_id.digital_signature:
                image_buf = (his_id.user_id.digital_signature).decode('utf-8')
                image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,%s" />' % (
                    image_buf)
            user_str = '________________________'
            if his_id.user_id:
                user_str = his_id.user_id.name
            html += u'<tr><td><p>%s</p></td><td>%s</td><td> <p>/%s/</p></td></tr>' % (
                item.name, image_str, user_str)
        html += '</table>'
        return html
    # Print

    def get_print_lines(self, ids):
        headers = [
            u'<p style="text-align: center;font-weight: bold; font-size: 17px" >''№'u'</p>',
            u'<p style="text-align: center;font-weight: bold; font-size: 17px" >''Ажил хүлээлцсэн байдал'u'</p>',
            u'<p style="text-align: center;font-weight: bold; font-size: 17px">''Тооцоотой эсэх'u'</p>',
            u'<p style="text-align: center;font-weight: bold; font-size: 17px">''Огноо'u'</p>',
        ]
        datas = []
        report_id = self.browse(ids)
        i = 1
        in_sel = ''
        for line in report_id.line_ids:
            if line.item_id:
                if line.in_sel == 'yes':
                    in_sel = 'Тооцоотой'
                elif line.in_sel == 'no':
                    in_sel = 'Тооцоогүй'
                temp = [
                    u'<p style="text-align: center; font-size: 17px">' +
                    str(i)+u'</p>',
                    u'<p style="text-align: left;font-size: 17px">' +
                    str(line.item_id.name) or '' + u'</p>',
                    u'<p style="text-align: center; font-size: 17px">' +
                    str(in_sel) or '' + u'</p>',
                    u'<p style="text-align: center;font-size: 17px">' +
                    str(line.date) or '' + u'</p>',
                ]
                datas.append(temp)
                i += 1
        res = {'header': headers, 'data': datas}
        return res
class DynamicFlowHistory(models.Model):
    _inherit = 'dynamic.flow.history'

    routing_slip_id = fields.Many2one(
        'routing.slip.hr', 'Routing Slip Hr', ondelete='cascade', index=True)
class RoutingSlipLine(models.Model):
    _name = "routing.slip.hr.line"
    _description = 'Routing Slip Line'

    item_id = fields.Many2one(
        'routing.slip.hr.line.item', 'Ажил хүлээлцсэн байдал')
    in_sel = fields.Selection(
        [('yes', 'Тооцоотой'), ('no', 'Тооцоогүй')], 'Тооцоотой эсэх')
    in_sel_p = fields.Char('Хэвлэлт')
    date = fields.Date('Огноо')
    desc = fields.Char('Тэмдэглэл')
    parent_id = fields.Many2one('routing.slip.hr', 'Parent')
    company_id = fields.Many2one('res.company', string='Компани',
                                 default=lambda self: self.env.user.company_id, readonly=True)
    sequence = fields.Integer(string='Дугаарлалт')
    
    @api.onchange('in_sel')
    def onchange_in_sel(self):
        if self.in_sel:
            if self.in_sel == 'yes':
                self.in_sel_p = 'Тооцоотой'
            elif self.in_sel == 'no':
                self.in_sel_p = 'Тооцоогүй'

class RoutingSlipLineItem(models.Model):
    _name = "routing.slip.hr.line.item"
    _description = 'Routing Slip Line Item'
    _inherit = ['mail.thread']
    _order = 'name desc'

    name = fields.Char('Ажил хүлээлцсэн байдал', tracking=True)
    company_id = fields.Many2one('res.company', string='Компани',
                                 default=lambda self: self.env.user.company_id, readonly=True, tracking=True)
