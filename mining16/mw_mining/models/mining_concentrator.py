# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
##########################


class mining_concentrator_production(models.Model):
    _name = 'mining.concentrator.production'
    _description = 'Mining Concentrator Production'
    _inherit = ["mail.thread"]

    @api.depends('date','shift')
    def _set_name(self):
        for obj in self:
            obj.name = str(obj.date)+obj.shift

    @api.depends('line_ids')
    def _total_production(self):
        for plan in self:
            total = 0.0;
            for line in plan.line_ids:
                total += line.production_amount
            plan.total_production = total

    # by Bayasaa
    @api.depends('line_ids')
    def _total_hour(self):
        for plan in self:
            run = 0.0
            stop = 0.0
            for line in plan.line_ids:
                if line.state == 'running':
                    run +=line.total_hour
                else:
                    stop += line.total_hour
            plan.total_worked_hour = run
            plan.total_stop_hour = stop

    # by Bayasaa
    @api.depends('engineer_work_line')
    def _total_engineer_hour(self):
        for plan in self:
            total = 0.0
            for line in plan.engineer_work_line:
                total += line.hours_worked
            obj.total_engineer_work_hour = total



    branch_id = fields.Many2one('res.branch','Branch', required=True, help='The Branch',tracking=True, states={'approved': [('readonly',True)]})
    name = fields.Char(compute='_set_name', string='Нэр', readonly=True, store=True)
    date = fields.Date('Огноо',required=True, states={'approved': [('readonly',True)]})
    shift = fields.Selection([('day', 'Day'),('night', 'Night')], 'Shift', required =True, states={'approved': [('readonly',True)]})
    line_ids = fields.One2many('mining.concentrator.production.line', 'mining_concentrator_production_id', 'Mining Concentrator Production Lines', readonly=True, states={'draft': [('readonly',False)]} )
    state = fields.Selection([('draft', 'New'),('approved', 'Approved')], 'State', readonly=True, tracking=True)
    # cats = fields.related('branch_id', 'project_product_category', string='Cates', type='many2many', obj='product.category')
    total_production = fields.Float(compute='_total_production', string='Total productivity', readonly=True)
    total_worked_hour = fields.Float(compute='_total_hour', digits=(16,2), string='Total hours worked' )
    total_stop_hour = fields.Float(compute='_total_hour', multi='hours',digits=(16,2), string='Total downtime')
    total_engineer_work_hour = fields.Float(compute='_total_engineer_hour', string='Total engineering hours worked')

    master_id =fields.Many2one('res.users', 'Master', required=True, states={'approved': [('readonly',True)]})
    description =fields.Text('Тайлбар',states={'approved': [('readonly',True)]})
    engineer_work_line = fields.One2many('mining.concentrator.engineer.work.line', 'mining_concentrator_production_id', 'Mining Concentrator Engineer Work Lines', states={'draft':[('readonly',False)]} )

    _sql_constraints = [
        ('date_shift_uniq', 'UNIQUE(name)', 'Date and Shift must be unique!')
    ]

    def confirm(self):
        obj = self
        if (obj.total_worked_hour+obj.total_stop_hour)!=12.0:
                raise UserError(_('Warning!'), _(u'Зогссон Ажилласан цагийн нийлбэр 12 байна'))
        return self.write({'state': 'approved'})
    def refuse(self):
        return self.write({'state': 'draft'})


class mining_concentrator_production_line(models.Model):
    _name = 'mining.concentrator.production.line'
    _description = 'Mining Concentrator Production Line'

    @api.model
    def create(self, values):
        start = values['start_time']
        end = values['end_time']
        if (start < 0) or (start >= 24):
            raise UserError(_('Warning!'), _(u'Эхэлсэн цаг зөв форматаар оруулаагүй байна! формат нь ##:## байх ёстой ба, 00:00-с их 24:00-с бага байна.'))
        if (end < 0) or (end >= 24):
            raise UserError(_('Warning!'), _(u'Дууссан цаг зөв форматаар оруулаагүй байна! формат нь ##:## байх ёстой ба, 00:00-с их 24:00-с бага байна.'))
        if values['state'] == 'running':
            values['production_cause_id'] = 0
        else:
            values['excavator_id'] = 0
            values['production_amount'] = 0.0
        return super(mining_concentrator_production_line, self).create(values)

    def write(self, values):
        line = self

        if 'start_time' in values:
            start = values['start_time']
        else:
            start=line.start_time
        if 'end_time' in values:
            end = values['end_time']
        else:
            end = line.end_time

        if (start < 0) or (start >=24):
            raise UserError(_('Warning!'), _(u'Эхэлсэн цаг зөв форматаар оруулаагүй байна! формат нь ##:## байх ёстой ба, 00:00-с их 24:00-с бага байна.'))
        if (end < 0) or (end >=24):
            raise UserError(_('Warning!'), _(u'Дууссан цаг зөв форматаар оруулаагүй байна! формат нь ##:## байх ёстой ба, 00:00-с их 24:00-с бага байна.'))
        if hasattr(values,'state'):
            state = values['state']
        else:
            state =line.state
        if state == 'running':
            values['production_cause_id'] = 0
        else:
            values['excavator_id'] = 0
            values['production_amount'] = 0.0
        return super(mining_concentrator_production_line, self).write(values)

    @api.depends('end_time','start_time')
    def _total_hour(self):
        for pline in self:
            end_time = pline.end_time
            start_time = pline.start_time
            if end_time < start_time:
                end_time = end_time+24
            pline.total_hour = end_time-start_time

    @api.depends('excavator_id','production_count')
    def _production_amount(self, cr, uid, ids, name, args, context=None):
        for pline in self:
            technic_ids = self.env['technic.equipment'].search([('id','=',pline.excavator_id.id)])
            if technic_ids :
                for technic in technic_ids:
                    amount = technic.mining_capacity * pline.production_count
            else:
                amount = 0
            pline.production_amount = amount

    @api.depends('start_time')
    def _set_start_time(self):
        for obj in self:
            time = obj.start_time
            if obj.mining_concentrator_production_id.shift=='night' and time<19:
                time += 24.0
            obj.r_start_time = time


    mining_concentrator_production_id = fields.Many2one('mining.concentrator.production','Concentrator Production', required=True)
    mining_concentrator_id = fields.Many2one('mining.concentrator', 'Баяжуулах үйлдвэр', required=True)
    date = fields.Date(related='mining_concentrator_production_id.date', store=True)
    shift = fields.Selection(related='mining_concentrator_production_id.shift')
    pile_id = fields.Many2one('mining.pile', 'Овоолго')
    start_time = fields.Float('Start time',digits=(16,2), required=True)
    end_time = fields.Float('Stop time', digits=(16,2),required=True)
    r_start_time = fields.Float(compute="_set_start_time", digits=(16,2), string='Real working hours', readonly=True, store=True)
    state = fields.Selection([('running','Running'),('stop','Stop')], 'State', required=True, default='running')
    excavator_id =fields.Many2one('technic.equipment','Excavator', domain=[('technic_type', '=', 'excavator')])
    production_count = fields.Integer('Number of buckets')
    cause_id = fields.Many2one('mining.concentrator.cause', 'Cause type')
    total_hour = fields.Float(string='Total hours',compute='_total_hour', digits=(16,2), readonly=True, store=True)
    production_amount = fields.Float(string='Production', compute='_production_amount', readonly=True, store=True)


    _order = 'r_start_time asc'

class mining_concentrator_engineer_work_line(models.Model):
    _name = 'mining.concentrator.engineer.work.line'
    _description = 'Mining concentrator engineer work line'


    mining_concentrator_production_id = fields.Many2one('mining.concentrator.production','Баяжуулахын Бүтээл', required=True)
    worked = fields.Reference(selection=[('technic.equipment', 'hr.employee')])
    hours_worked = fields.Float('Hours working (time min)')
    description_of_work = fields.Text('Description of the work performed', required=True)



