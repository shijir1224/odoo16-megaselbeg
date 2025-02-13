# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anusha @cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import datetime
from odoo import api, fields, models, _


class Orientation(models.Model):
    _name = 'employee.orientation'
    _description = "Employee Orientation"
    _inherit = 'mail.thread'

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    
    @api.model
    def _line_item(self):
        cons = self.env['rate.question'].search([])
        w = []
        for cc in cons:
            vals = {
                'question_id': cc.id
            }
            w.append(vals)
        return w
    
    name = fields.Char(string='Employee Orientation', readonly=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',required=True)
    date = fields.Datetime(string="Date",default=lambda self: datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    responsible_user_id = fields.Many2one('res.users', string='Responsible User',related='responsible_employee_id.user_id')
    responsible_employee_id = fields.Many2one('hr.employee', string='Responsible Employee')
    responsible_job_id = fields.Many2one('hr.job', string='Responsible Employee Job',related='responsible_employee_id.job_id')
    responsible_department_id = fields.Many2one('hr.department', string='Responsible Employee Department',related='responsible_employee_id.department_id')
    employee_company_id = fields.Many2one('res.company', string='Company', required=True,
                                          default=lambda self: self.env.user.company_id)
    parent_id = fields.Many2one('hr.employee', string='Manager', related='employee_id.parent_id')
    create_employee = fields.Many2one('hr.employee',string='Created Employee',default=_default_employee)
    job_id = fields.Many2one('hr.job', string='Job Title', related='employee_id.job_id',
                             domain="[('department_id', '=', department_id)]")
    orientation_id = fields.Many2one('orientation.checklist', string='Orientation Checklist',
                                     domain="[('checklist_department_ids','in', department_id)]", required=True)
    note = fields.Text('Description')
    purpose = fields.Text('Purpose')
    orientation_request_ids = fields.One2many('orientation.request', 'request_orientation_id', string='Orientation Request')
    rate_ids = fields.One2many('orientation.rate.line', 'rate_id', string='Rate question',default=_line_item)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Canceled'),
        ('complete', 'Completed'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    def confirm_orientation(self):
        self.write({'state': 'confirm'})
        for values in self.orientation_id.checklist_line_ids:
            self.env['orientation.request'].create({
                'request_name': values.line_name,
                'stage':values.stage,
                'request_orientation_id': self.id,
                'partner_id': values.responsible_user_id.id,
                'request_date': self.date,
                'employee_id': self.employee_id.id,
                'note':values.note,
            })

    def cancel_orientation(self):
        for request in self.orientation_request_ids:
            request.state = 'cancel'
        self.write({'state': 'cancel'})

    def waiting_orientation(self):
        self.write({'state': 'waiting'})

    def complete_orientation(self):
        force_complete = False
        for request in self.orientation_request_ids:
            if request.state == 'new':
                force_complete = True
        if force_complete:
            return {
                'name': 'Complete Orientation',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'orientation.force.complete',
                'type': 'ir.actions.act_window',
                'context': {'default_orientation_id': self.id},
                'target': 'new',
            }
        self.write({'state': 'complete'})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('employee.orientation')
        result = super(Orientation, self).create(vals)
        return result
