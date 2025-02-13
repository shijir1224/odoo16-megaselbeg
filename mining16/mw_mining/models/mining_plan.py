# -*- coding: utf-8 -*-
import pytz
from datetime import datetime, timedelta
from calendar import monthrange
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
_logger = logging.getLogger(__name__)
from odoo.addons.mw_technic_equipment.models.technic_equipment import TECHNIC_TYPE
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE

class mining_plan(models.Model):
    _name = 'mining.plan'
    _description = 'Mining Plan'

    STATE_SELECTION = [
        ('draft', 'Ноорог'),
        ('approved', 'Батлагдсан'),
    ]
    _inherit = ["mail.thread"]

    def unlink(self):
        for item in self:
            if item.state!='draft':
                raise UserError(u'Ноорог биш баримтыг устгахгүй')
        res = super(mining_plan, self).unlink()
        return res

    @api.model
    def _default_get_type(self):
        type = self.env.context.get('type', False)
        if type=='master':
            return 'master'
        return 'plan'

    @api.depends('date','branch_id','type')
    def _set_name(self):
        for obj in self:
            type_str = str(dict(self._fields['type'].selection).get(obj.type))
            obj.name = '{0} {1} {2}'.format(datetime.strftime(obj.date, '%Y-%m-%d'), obj.branch_id.name,type_str)

    @api.depends('date','branch_id')
    def _progress_rate(self):
        res = {}
        for item in self:
            sum_actual = 0.0
            progress = 0
            if item.sum_forecast_m3>0:
                progress = (100*sum_actual)/item.sum_forecast_m3
            item.actual_m3 = sum_actual
            item.progress_rate =progress

    @api.depends('plan_line.forecast_m3','plan_line.forecast_tn','plan_line.budget_m3','plan_line.budget_tn')
    def _sum_all(self):
        for obj in self:
            bud_m3 = 0.0
            bud_tn = 0.0
            for_m3 = 0.0
            for_tn = 0.0
            bud_min_m3 = 0.0
            for_min_m3 = 0.0
            for item in obj.plan_line:
                bud_m3 += item.budget_m3
                for_m3 += item.forecast_m3
                bud_tn += item.budget_tn
                for_tn += item.forecast_tn
                if item.material_id.mining_product_type == 'mineral':
                    bud_min_m3 += item.budget_m3
                    for_min_m3 += item.forecast_m3
            obj.sum_budget_m3 = bud_m3
            obj.sum_forecast_m3 = for_m3
            obj.sum_budget_tn = bud_tn
            obj.sum_forecast_tn = for_tn
            obj.sum_budget_mineral_m3 = bud_min_m3
            obj.sum_forecast_mineral_m3 = for_min_m3

    name = fields.Char(compute='_set_name', string='Name', readonly=True, store=True)
    date = fields.Date('Date',required=True, states={'approved':[('readonly',True)]}, default=fields.Date.context_today)
    branch_id = fields.Many2one('res.branch','Branch', required=True, states={'approved':[('readonly',True)]})
    plan_line = fields.One2many('mining.plan.line','plan_id','Plan line', states={'approved':[('readonly',True)]})
    plan_technic_line = fields.One2many('mining.plan.technic.line','plan_id','Technic plan line', states={'approved':[('readonly',True)]})
    state = fields.Selection(STATE_SELECTION, 'State', readonly=True, tracking=True, default='draft')
    description = fields.Text('Description', states={'approved':[('readonly',True)]})
    progress_rate = fields.Float(compute="_progress_rate", string='Actual Percent',  group_operator="avg", store=True)
    actual_m3 = fields.Float(compute="_progress_rate", string='Actual m3', store=True)
    sum_budget_m3 = fields.Float(compute="_sum_all", string='Budget m3', tracking=True, store=True)
    sum_forecast_m3 = fields.Float(compute="_sum_all", string='Forecast м3', tracking=True, store=True)
    sum_budget_tn = fields.Float(compute="_sum_all", string='Батлагдсан Төлөвлөгөө тн', store=True)
    sum_forecast_tn = fields.Float(compute="_sum_all", string='Төлөвлөгөө тн', store=True)
    sum_forecast_mineral_m3 = fields.Float(compute="_sum_all", string='Төлөвлөгөө Ашигт Малтмал м3', store=True)
    sum_budget_mineral_m3 = fields.Float(compute="_sum_all", string='Батлагдсан Ашигт Малтмал м3', store=True)
    sum_production = fields.Float(compute="_sum_technic_plan", string='Нийт Техникийг Бүтээл', store=True)
    sum_production_ok = fields.Float(compute="_sum_technic_plan", string='Нийт Техникийг Бүтээлтэй', store=True)
    sum_production_exca = fields.Float(compute="_sum_technic_plan", string='Нийт Экска Бүтээл', store=True)
    sum_production_dump = fields.Float(compute="_sum_technic_plan", string='Нийт Дамп Бүтээл', store=True)
    type = fields.Selection([('master','Master'),
                            ('plan','Monthly'),
                            ('weekly','Weekly')], default=_default_get_type, string='Төрөл')

    @api.depends('plan_technic_line.production')
    def _sum_technic_plan(self):
        for item in self:
            item.sum_production = sum(item.plan_technic_line.mapped('production'))
            item.sum_production_ok = sum(item.plan_technic_line.filtered(lambda r: r.is_production).mapped('production'))
            item.sum_production_dump = sum(item.plan_technic_line.filtered(lambda r: r.technic_id.technic_type=='dump').mapped('production'))
            item.sum_production_exca = sum(item.plan_technic_line.filtered(lambda r: r.technic_id.technic_type=='excavator').mapped('production'))

    def import_technic(self):
        obj = self
        plan_exca = self.env['mining.plan.exca.hour.prod']

        technic_ids = self.env['technic.equipment'].search([('branch_id', '=', obj.branch_id.id),
                                                            ('technic_type', 'in', ['excavator', 'wheel_loader', 'dump'])]).ids
        for item in obj.plan_technic_line:
            if item.technic_id.id in technic_ids:
                technic_ids.remove(item.technic_id.id)

        for technic in technic_ids:
            data = {
                'plan_id': obj.id,
                'technic_id': technic,
            }
            technic_id = self.env['technic.equipment'].browse(technic)
            branch_id = self.branch_id
            date = self.date

            hour_prod = plan_exca.get_hour_production(date, technic_id, branch_id, False)
            if hour_prod:
                m_line_id = self.env['mining.plan.technic.line'].create(data)
                m_line_id.onchage_run_hour()

        self.update_technic()

    def update_technic(self):
        plan_len = len(self.plan_line)
        for item in self.plan_line:
            if plan_len > 0:
                item.forecast_m3 = self.sum_production_ok / plan_len
            else:
                item.forecast_m3 = 0

    def remove_technic(self):
        self.plan_technic_line.unlink()

    def action_to_approved(self):
        obj = self
        self.write({'state': 'approved'})

    def action_to_draft(self):
        self.write({'state': 'draft'})

    _order = 'date asc'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(date,branch_id,type)', 'Date must be unique')
    ]

class mining_plan_line(models.Model):
    _name = 'mining.plan.line'
    _description = 'Mining Plan Line'
    
    @api.depends('plan_id','material_id','level','location_id')
    def _set_name(self):
        for obj in self:
            obj.name = str(obj.plan_id)+'-'+str(obj.material_id.id)+'-'+str(obj.level)+'-'+str(obj.location_id.id)

    @api.depends('budget_m3','material_id','forecast_m3')
    def _sum_all(self):
        for obj in self:
            bud_tn = 0.0
            for_tn = 0.0
            obj.budget_tn = obj.budget_m3*obj.material_id.bcm_coefficient
            obj.forecast_tn = obj.forecast_m3*obj.material_id.bcm_coefficient

    name = fields.Char(compute='_set_name', string='Нэр', readonly=True, store=True)
    plan_id = fields.Many2one('mining.plan','Plan ID', required=True, ondelete='cascade')
    material_id = fields.Many2one('mining.material','Material', required=True)
    location_id = fields.Many2one('mining.location','Block')
    level = fields.Char('Level',size=128)
    budget_m3 = fields.Float('Budget m3')
    is_reclamation = fields.Boolean('Нөхөн сэргээлт эсэх')
    forecast_m3 = fields.Float('Forecast м3')
    budget_tn = fields.Float(compute="_sum_all", string='Budget tn', store=True)
    forecast_tn = fields.Float(compute="_sum_all", string='Forecast tn',  store=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(plan_id, material_id, level, location_id)', 'Материал, Level, Location must be unique')
    ]

class MaintenancePlanLinejjjjjjj(models.Model):
    _inherit = 'maintenance.plan.line'
    
    def action_to_confirm(self):
        # for item in self:
        result = super(MaintenancePlanLinejjjjjjj, self).action_to_confirm() 
        technic_id1 = self.technic_id
        branch = self.branch_id
        date = self.date_required
        time = self.work_time
        
        if technic_id1.technic_type in ['excavator', 'dump']:
            obj = self.env['mining.plan.technic.line']
            ll = self.env['mining.plan.technic.line'].search([('technic_id','=',technic_id1.id),('date','=',date),('branch_id','=',branch.id)])
            if ll:
                ll._compute_run_hour()    
            else:
                obj.create({
                    'branch_id' : branch.id,
                    'technic_id' : technic_id1.id,
                    'repair_hour' : time,
                    'date' : date,
                    'line_type':'plan'
                })

                obj_2 = self.env['mining.plan.technic.line']
                obj_2.create({
                    'branch_id' : branch.id,
                    'technic_id' : technic_id1.id,
                    'repair_hour' : time,
                    'date' : date,
                    'line_type':'weekly'
                })

        return result
        


class mining_plan_technic_line(models.Model):
    _name = 'mining.plan.technic.line'
    _description = 'Mining Plan Technic Line'
    _inherit = ["mail.thread"]
    _order = 'branch_id, date, technic_id'

    @api.depends('technic_id','date','branch_id')
    def _compute_run_hour(self):
        maintenance_plan_obj = self.env['maintenance.plan.line']
        plan_exca = self.env['mining.plan.exca.hour.prod']
        for item in self:
            technic_id = item.technic_id
            branch_id = item.branch_id
            date = item.date
            m_ids = maintenance_plan_obj.sudo().search([
                ('technic_id', '=', technic_id.id),
                ('date_required', '=', date),
                ('branch_id', '=', branch_id.id)])
            sum_repair_hour = sum(m_ids.mapped('work_time'))
            item.maint_plan_ids = m_ids
            horin_duruv = 24
            if sum_repair_hour>=21:
                # 24 bolgochloo
                horin_duruv = 24
                item.repair_hour = horin_duruv
                item.run_hour = horin_duruv - item.repair_hour
            else:
                item.repair_hour = sum_repair_hour
                item.run_hour = horin_duruv - sum_repair_hour
            

    @api.depends('run_hour')
    def _compute_run_hour_util(self):
        for item in self:
            run_hour_util_o = self.env['mining.plan.exca.hour.prod.line'].get_run_hour_util_hasagdah(item.branch_id,item.date)
            util = item.run_hour - run_hour_util_o
            item.run_hour_util = 0 if util<0 else util
    
    @api.depends('repair_hour','run_hour','run_hour_util')
    def _sum_hour_hour(self):
        maintenance_plan_obj = self.env['maintenance.plan.line']
        plan_exca = self.env['mining.plan.exca.hour.prod']
        for obj in self:
            technic_id = obj.technic_id
            branch_id = obj.branch_id
            date = obj.date
            hour_prod = plan_exca.get_hour_production(date, obj.technic_id, branch_id, False)
            obj.production = hour_prod * obj.run_hour_util
            obj.hour_prod = hour_prod
            if technic_id.technic_type=='excavator':
                obj.is_production = True
            else:
                obj.is_production = False
    
    @api.model
    def _default_get_line_type(self):
        return self.env.context.get('line_type', 'plan')
        
    state = fields.Selection([('draft', 'Draft'),('approved', 'Approved'),], 'State', default='draft', readonly=True, tracking=True)
    plan_id = fields.Many2one('mining.plan', 'Plan ID', ondelete='cascade')
    technic_id = fields.Many2one('technic.equipment','Technic', required=True, tracking=True, domain=[('technic_type','in',['dump','excavator'])])
    owner_type = fields.Selection(OWNER_TYPE, string='Owner type',readonly=True, store=True)
    technic_type = fields.Selection(TECHNIC_TYPE, string='Technic type', readonly=True, store=True)
    technic_setting_id = fields.Many2one(related='technic_id.technic_setting_id', string='Technic setting', readonly=True, store=True)
    partner_id = fields.Many2one(related='technic_id.partner_id', string='Technic partner', readonly=True)
    date = fields.Date(string='Date', tracking=True)
    branch_id = fields.Many2one('res.branch', string='Branch', store=True, tracking=True)
    material_id = fields.Many2one('mining.material','Material', tracking=True)
    repair_hour = fields.Float(compute='_compute_run_hour', string='Repair hour', store = True, tracking=True, readonly=False)
    run_hour = fields.Float(string='Availability hour', tracking=True, compute='_compute_run_hour', store=True, readonly=False)
    run_hour_util = fields.Float(string='Utilization hour', tracking=True, compute='_compute_run_hour_util', store=True, readonly=False)
    production = fields.Float(compute='_sum_hour_hour', string='Total Production', store = True, tracking=True)
    hour_prod = fields.Float(compute='_sum_hour_hour', string='Hour Production', store = True, tracking=True)
    is_production = fields.Boolean(compute='_sum_hour_hour', string='Production', store = True, tracking=True)
    digg_or_dump = fields.Char(string='Diggers or Dump', compute='_set_digg_or_dump', store=True)
    line_type = fields.Selection([
                            ('master','Master'),
                            ('plan','Monthly'),
                            ('weekly','Weekly')], default=_default_get_line_type, string='Төрөл', required=True)
    maint_plan_ids = fields.Many2many('maintenance.plan.line', string='Maintenance Plans', compute='_compute_run_hour')
    actual_per_dpr = fields.Float('Actual DPR %', compute='compute_actual_mining_plan', store=True)
    actual_dpr = fields.Float('Actual DPR', compute='compute_actual_mining_plan', store=True)
    actual_per_sur = fields.Float('Actual Survey %', compute='compute_actual_mining_plan', store=True)
    actual_sur = fields.Float('Actual Survey', compute='compute_actual_mining_plan', store=True)

    def update_dummy_force_m(self):
        y = self.date.year
        m = self.date.month
        end_d = monthrange(int(y), int(m))[1]
        s_date = '%s-%s-01'%(y,m)
        e_date = '%s-%s-%s'%(y,m,end_d)
        objs = self.search([('date','>=',s_date),('date','<=',e_date),('branch_id','=',self.branch_id.id),('line_type','=','plan')])
        lens = len(objs)
        i = lens
        for item in objs:
            _logger.info(' mining plan update FORCE month %s of %s ==== %s %s %s'%(i, lens, item.date, item.branch_id.display_name, item.technic_id.display_name))
            i -= 1
            item.update_dummy_force()

    def update_dummy_m(self):
        y = self.date.year
        m = self.date.month
        end_d = monthrange(int(y), int(m))[1]
        s_date = '%s-%s-01'%(y,m)
        e_date = '%s-%s-%s'%(y,m,end_d)
        objs = self.search([('date','>=',s_date),('date','<=',e_date),('branch_id','=',self.branch_id.id),('line_type','=','plan')])
        lens = len(objs)
        i = lens
        for item in objs:
            _logger.info(' mining plan update month %s of %s ==== %s %s %s'%(i, lens, item.date, item.branch_id.display_name, item.technic_id.display_name))
            i -= 1
            item.update_dummy()
            
    def update_dummy_force(self):
        self._compute_run_hour()
        self._sum_hour_hour()
        self._compute_run_hour_util()

    def update_dummy(self):
        self._sum_hour_hour()
        self._compute_run_hour_util()

    @api.depends('production','technic_id','date','branch_id','material_id')
    def compute_actual_mining_plan(self):
        for item in self:
            sum_m3 = sum(self.env['mining.production.entry.line'].search([('date','=',item.date),('production_id.branch_id','=',item.branch_id.id),('material_id','=',item.material_id.id),'|',('excavator_id','=',item.technic_id.id),('dump_id','=',item.technic_id.id)]).mapped('sum_m3'))

            item.actual_dpr = sum_m3
            if item.production>0:
                item.actual_per_dpr = (100*sum_m3)/item.production
            else:
                item.actual_per_dpr = 0
            
            # sur_m3 = sum(self.env['mining.surveyor.measurement'].search([('date','=',item.date),('branch_id','=',item.branch_id.id),('excavator_id','=',item.technic_id.id),('material_id','=',item.material_id.id)]).mapped('total_amount'))

            sur_m3 = sum(self.env['mining.surveyor.measurement.line'].search([('mining_surveyor_measurement_id.date','=',item.date),('mining_surveyor_measurement_id.branch_id','=',item.branch_id.id)
            ,('mining_surveyor_measurement_id.excavator_id','=',item.technic_id.id)
            # ,('material_id','=',item.material_id.id),
            # ,('is_production','=',True)
            ]).mapped('amount_by_measurement_with_diff'))
            item.actual_sur = sur_m3
            if item.production>0:
                item.actual_per_sur = (100*sur_m3)/item.production
            else:
                item.actual_per_sur = 0

    def compute_actual_mining_plan_month(self):
        y = self.date.year
        m = self.date.month
        end_d = monthrange(int(y), int(m))[1]
        s_date = '%s-%s-01'%(y,m)
        e_date = '%s-%s-%s'%(y,m,end_d)
        for item in self.env['mining.plan.technic.line'].search([('date','>=',s_date),('date','<=',e_date)]):
            item.compute_actual_mining_plan()
        
    def import_down_maintenance(self):
        obj = self.env['mining.plan.import']
        y = self.date.year
        m = self.date.month
        end_d = monthrange(int(y), int(m))[1]
        s_date = '%s-%s-01'%(y,m)
        e_date = '%s-%s-%s'%(y,m,end_d)
        # obj.create({
        # date_start
        # date_end
        # branch_id
        # type
        obj_id = obj.create({
            'date_start': s_date,
            'date_end': e_date,
            'branch_id': self.branch_id.id,
            'type': self.line_type
        })
        obj_id.import_plan()

    @api.depends('technic_id')
    def _set_digg_or_dump(self):
        for item in self:
            if item.technic_id.technic_type=='excavator':
                item.digg_or_dump = 'digger'
            else:
                item.digg_or_dump = 'dump'
    
    def view_maint_plan_ids(self):
        self.ensure_one()
        action = self.env.ref('mw_technic_maintenance.action_maintenance_plan_line').read()[0]
        action['domain'] = [('id','=',self.maint_plan_ids.ids)]
        return action
    
    def name_get(self):
        res = []
        for item in self:
            res_name = super(mining_plan_technic_line, item).name_get()
            if item.technic_id:
                res_n = '{0}'.format(self.env['ir.qweb.field.float_time'].value_to_html(item.repair_hour, {}))
                # res_n = '{0} A:{1} U:{2}'.format(item.technic_id.display_name, self.env['ir.qweb.field.float_time'].value_to_html(item.run_hour, {}), self.env['ir.qweb.field.float_time'].value_to_html(item.run_hour_util, {}))
                res.append((item.id, res_n))
            else:
                res.append(res_name[0])
        return res

    def action_to_approved(self):
        obj = self
        self.write({'state': 'approved'})

    def action_to_draft(self):
        self.write({'state': 'draft'})
    
    # @api.constrains('branch_id','date','technic_id')
    # def _validate_mat_bran(self):
    #     for item in self:
    #         if self.env['mining.plan.technic.line'].search([('date','=',item.date),('line_type','=',item.line_type),('technic_id','=',item.technic_id.id),('branch_id','=',item.branch_id.id),('id','!=',item.id)]):
    #             raise UserError((u"%s %s %s давхардахгүй") % (item.date, item.technic_id.display_name, item.branch_id.display_name))

    def init(self):
        if not tools.index_exists(self._cr, 'name_mat_bran_uniq_mw'):
            self.env.cr.execute("CREATE UNIQUE INDEX name_mat_bran_uniq_mw ON %s(branch_id, date, technic_id, line_type, COALESCE(material_id, -1) )"% self._table)


    # _sql_constraints = [
    #     ('name_uniq', 'UNIQUE(plan_id, technic_id)', 'Technic must be unique'),
    #     ('name_mat_bran_uniq', 'UNIQUE INDEX(branch_id, date, technic_id, line_type, COALESCE(material_id, -1) )', 'Technic branch date material unique'),
    # ]

class mining_plan_technic_run_hour(models.Model):
    _name = 'mining.plan.technic.run.hour'
    _description = 'Mining Plan Technic Run Hour'
    _order = 'sequence'

    sequence = fields.Integer('Дараалал', default=1)
    date_start = fields.Date('Эхлэх Огноо', copy=False)
    date_end = fields.Date('Дуусгах Огноо', copy=False)
    branch_id = fields.Many2one('res.branch', 'Branch', required=True)
    run_hour_util = fields.Float(string='Utilization hour auto ХАСАГДАХ', default=2, tracking=True)

class mining_plan_concentrator(models.Model):
    _name = 'mining.plan.concentrator'
    _description = 'Mining Plan Concentrator'

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
    ]
    _inherit = ["mail.thread"]
    _order = 'date asc'

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Date must be unique')
    ]

    @api.depends('date','branch_id')
    def _set_name(self):
        for obj in self:
            obj.name = str(obj.date)+'-'+ obj.branch_id.name

    @api.depends('plan_concentrator_line')
    def _sum_all(self):
        for obj in self:
            plan_m3 = 0.0
            met_kg = 0.0
            for item in obj.plan_concentrator_line:
                plan_m3 += item.plan_m3
                met_kg += item.metal_kg
            obj.sum_plan_m3 = plan_m3
            obj.sum_metal_kg = met_kg

    name = fields.Char(compute='_set_name', string='Нэр', readonly=True, store=True)
    date = fields.Date('Date',required=True, default=fields.Date.context_today, states={'approved':[('readonly',True)]})
    branch_id = fields.Many2one('res.branch','Branch', required=True, states={'approved':[('readonly',True)]})
    plan_concentrator_line = fields.One2many('mining.plan.concentrator.line','plan_concentrator_id','Plan Concentrator Line', states={'approved':[('readonly',True)]})
    state = fields.Selection(STATE_SELECTION, 'State', default='draft', readonly=True, tracking=True)
    sum_plan_m3 = fields.Float(compute="_sum_all", string='Төлөвлөгөө м3', store = True)
    sum_metal_kg = fields.Float(compute="_sum_all", string='Нийт Метал Кг', store = True)

    def action_to_approved(self):
        self.write({'state': 'approved'})

    def action_to_draft(self):
        self.write({'state': 'draft'})

class mining_plan_concentrator_line(models.Model):
    _name = 'mining.plan.concentrator.line'
    _description = 'Mining Plan Concentrator Line'

    @api.depends('plan_m3','average_content')
    def _metal_kg(self):
        for plan in self:
            first = plan.plan_m3*plan.average_content
            second = plan.metal_capture*0.01
            third = first*second
            fourth = third*0.001
            res[plan.id] = fourth

    plan_concentrator_id = fields.Many2one('mining.plan.concentrator','Mining Plan Concentrator ID', required=True, ondelete='cascade')
    concentrator_id = fields.Many2one('mining.concentrator', 'Баяжуулах', required=True)
    location_id = fields.Many2one('mining.location','Блок', required=True)
    average_content = fields.Float(related='location_id.average_content')
    material_id = fields.Many2one('mining.material','Material', required=True)
    plan_m3 = fields.Float('Төлөвлөгөө м3')
    metal_capture = fields.Integer('Метал Барилт %')
    metal_kg = fields.Float(compute='_metal_kg', string='Метал Кг', readonly=True , store=True)

class mining_plan_exca_hour_prod(models.Model):
    _name = 'mining.plan.exca.hour.prod'
    _description = 'Mining Plan Exca Hour Prod'

    description = fields.Char('Тайлбар')
    date_start = fields.Date('Эхлэх Огноо', copy=False)
    date_end = fields.Date('Дуусгах Огноо', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
    ], 'Төлөв', default='draft', readonly=True)
    branch_id = fields.Many2one('res.branch', string=u'Branch', required=True)
    line_ids = fields.One2many('mining.plan.exca.hour.prod.line', 'parent_id', 'Lines', copy=True)

    def get_hour_production(self, date, excavator_id, branch_id, material_id=False):
        if material_id:
            s_lines = self.env['mining.plan.exca.hour.prod.line'].search([
            ('parent_id.date_start','<=',date),
            ('parent_id.date_end','>=',date),
            ('excavator_id','=',excavator_id.id),
            ('parent_id.branch_id','=',branch_id.id),
            ('parent_id.state','=','approved'),

            ('material_id','=',material_id.id),
            ], limit=1)
        else:
            s_lines = self.env['mining.plan.exca.hour.prod.line'].search([
            ('parent_id.date_start','<=',date),
            ('parent_id.date_end','>=',date),
            ('excavator_id','=',excavator_id.id),
            ('parent_id.branch_id','=',branch_id.id),
            ('parent_id.state','=','approved'),

            ], limit=1)
        if s_lines:
            return s_lines.hour_prod
        return 0

    def action_to_approved(self):
        self.write({'state': 'approved'})

    def action_to_draft(self):
        self.write({'state': 'draft'})

    def unlink(self):
        for item in self:
            if item.state!='draft':
                raise UserError(u'Ноорог биш баримтыг устгахгүй')
        res = super(mining_plan_exca_hour_prod, self).unlink()
        return res

class mining_plan_exca_hour_prod_line(models.Model):
    _name = 'mining.plan.exca.hour.prod.line'
    _description = 'Mining Plan Exca Hour Prod Line'

    parent_id = fields.Many2one('mining.plan.exca.hour.prod', string=u'Parent ID', required=True, ondelete='cascade')
    excavator_id = fields.Many2one('technic.equipment', string=u'Эксавтор/Дамп', required=True)
    material_id = fields.Many2one('mining.material', string=u'Material')
    hour_prod = fields.Float('Цагийн Бүтээл')
    run_hour_util_hasagdah = fields.Float(string='Utilization hour auto ХАСАГДАХ', default=2, tracking=True)

    def get_run_hour_util_hasagdah(self, branch_id, date=False):
        if date:
            obj_id = self.env['mining.plan.exca.hour.prod.line'].search([('parent_id.branch_id', '=', branch_id.id),('parent_id.date_start', '<=', date),('parent_id.date_end', '>=', date)], limit=1)
            if obj_id:
                return obj_id.run_hour_util_hasagdah
        return self.env['mining.plan.exca.hour.prod.line'].search([('parent_id.branch_id', '=', branch_id.id)], limit=1).run_hour_util_hasagdah or 0

    @api.constrains('parent_id.date_start', 'parent_id.date_end', 'excavator_id', 'material_id', 'parent_id.branch_id')
    def _validate_range(self):
        for this in self:
            if this.parent_id.branch_id and this.parent_id.date_start and this.parent_id.date_end:
                m_where = ';'
                if this.material_id:
                    m_where = """ and mp.material_id=%s; """%(this.material_id.id)
                SQL = """
                    SELECT
                        mp.id
                    FROM
                    mining_plan_exca_hour_prod_line mp
                    left join mining_plan_exca_hour_prod m on (m.id=mp.parent_id)
                    WHERE
                        DATERANGE(m.date_start, m.date_end, '[]') &&
                            DATERANGE(%s::date, %s::date, '[]')
                        AND mp.id != %s
                        AND mp.excavator_id=%s
                        AND m.branch_id=%s
                        """
                SQL+=m_where
                self.env.cr.execute(SQL, (this.parent_id.date_start,
                                        this.parent_id.date_end,
                                        this.id,
                                        this.excavator_id.id,
                                        this.parent_id.branch_id.id
                                        ))
                res = self.env.cr.fetchall()
                if res:
                    dt = self.browse(res[0][0])
                    raise ValidationError(
                        (u"%s %s хугацааны хооронд %s Эксавтор %s давхцаж байна") % (this.parent_id.date_start, this.parent_id.date_end,this.excavator_id.display_name,(this.material_id.name or '')))

class mining_plan_customer(models.Model):
    _name = 'mining.plan.customer'
    _description = 'Mining plan customer'
    _order = 'date_start desc'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
    ], 'Төлөв', default='draft', readonly=True)

    @api.depends('date_start')
    def _date_end(self):
        for obj in self:
            if obj.date_start:
                year = obj.date_start.year
                month = obj.date_start.month
                days = (monthrange(year, month)[1]-1)
                obj.date_end = obj.date_start + timedelta(days=days)
            else:
                obj.date_end = obj.date_start

    date_start = fields.Date(string=u'Date Start', required=True, states={'approved':[('readonly',True)]})
    date_end = fields.Date(compute="_date_end", string=u"Date End", store=True, states={'approved':[('readonly',True)]})
    branch_id = fields.Many2one('res.branch', string=u'Branch', required=True, states={'approved':[('readonly',True)]})
    material_id = fields.Many2one('mining.material', string=u'Material', required=True, states={'approved':[('readonly',True)]})
    total_amount_m3 = fields.Float(string=u'Toal m3', states={'approved':[('readonly',True)]})
    total_amount_tn = fields.Float(string=u'Total tn', compute='_compute_tn', compute_sudo=True, store=True)

    actual_per_dpr = fields.Float('Actual DPR %', compute='compute_actual', store=True)
    actual_dpr = fields.Float('Actual DPR', compute='compute_actual', store=True)
    actual_per_sur = fields.Float('Actual Survey %', compute='compute_actual', store=True)
    actual_sur = fields.Float('Actual Survey', compute='compute_actual', store=True)

    def update_dummy(self):
        self.compute_actual()

    @api.depends('total_amount_m3','date_start','date_end','branch_id')
    def compute_actual(self):
        for item in self:
            sum_m3 = sum(self.env['mining.production.entry.line'].search([('date','>=',item.date_start),('date','<=',item.date_end),('material_id','=',item.material_id.id),('production_id.branch_id','=',item.branch_id.id)]).mapped('sum_m3'))
            item.actual_dpr = sum_m3
            if item.total_amount_m3>0:
                item.actual_per_dpr = (100*sum_m3)/item.total_amount_m3
            else:
                item.actual_per_dpr = 0
            
            sur_m3 = sum(self.env['mining.surveyor.measurement.line'].search([('mining_surveyor_measurement_id.date','>=',item.date_start),('mining_surveyor_measurement_id.date','<=',item.date_end),('mining_surveyor_measurement_id.branch_id','=',item.branch_id.id),('material_id','=',item.material_id.id)]).mapped('amount_by_measurement_with_diff'))
            item.actual_sur = sur_m3
            if item.total_amount_m3>0:
                item.actual_per_sur = (100*sur_m3)/item.total_amount_m3
            else:
                item.actual_per_sur = 0

    # def compute_actual_mining_plan_month(self):
    #     y = self.date.year
    #     m = self.date.month
    #     end_d = monthrange(int(y), int(m))[1]
    #     s_date = '%s-%s-01'%(y,m)
    #     e_date = '%s-%s-%s'%(y,m,end_d)
    #     for item in self.env['mining.plan.technic.line'].search([('date','>=',s_date),('date','<=',e_date)]):
    #         item.compute_actual_mining_plan()

    @api.depends('total_amount_m3','material_id')
    def _compute_tn(self):
        for item in self:
            item.total_amount_tn = item.total_amount_m3*item.material_id.bcm_coefficient
           
    def name_get(self):
        res = []
        for item in self:
            res_name = super(mining_plan_customer, item).name_get()
            set_name = ''
            if self.user_has_groups('mw_mining.group_mining_mineral_coal') and item.total_amount_tn:
                set_name = '{0:,.0f} m3 {1:,.2f} tn'.format(item.total_amount_m3, item.total_amount_tn)
            else:
                set_name = '{0:,.0f} m3'.format(item.total_amount_m3)
            res.append((item.id, set_name))
        return res

    def action_to_approved(self):
        self.write({'state': 'approved'})

    def action_to_draft(self):
        self.write({'state': 'draft'})

class mining_plan_customer_line(models.Model):
    _name = 'mining.plan.customer.line'
    _description = 'Mining plan customer line'

    @api.depends('plan_id','material_id')
    def _set_name(self):
        for obj in self:
            obj.name = str(obj.plan_id)+'-'+str(obj.material_id.id)

    name = fields.Char(compute='_set_name', string='Нэр', readonly=True, store=True)
    plan_id = fields.Many2one(comodel_name=u'mining.plan.customer', string=u'Plan ID', required=True, ondelete='cascade')
    material_id = fields.Many2one(comodel_name=u'mining.material', string=u'Material', required=True)
    forecast_m3 = fields.Float(string=u'Төлөвлөгөө м3', required=True)

class mining_plan_import(models.TransientModel):
    _name = 'mining.plan.import'
    _description = 'Mining plan import'
    
    @api.depends('date_start')
    def _date_end(self):
        for obj in self:
            if obj.date_start and obj.type == 'plan':
                year = obj.date_start.year
                month = obj.date_start.month
                days = (monthrange(year, month)[1]-1)
                obj.date_end = obj.date_start + timedelta(days=days)
            elif obj.type == 'master':
                date = datetime.now()
                obj.date_start = datetime.strptime('{0}-01-01'.format(date.year))
                obj.date_end = datetime.strptime('{0}-12-31'.format(date.year))
            elif obj.date_start and  obj.type == 'weekly':
                date = datetime.now()
                obj.date_end = obj.date_start + timedelta(days=7)
            else:
                obj.date_end = obj.date_start

    date_start = fields.Date(string=u'Date Start', required=True)
    date_end = fields.Date(compute="_date_end", string=u"Date End", store=True, required=True)
    branch_id = fields.Many2one('res.branch', string="Branch", required=True)
    type = fields.Selection([('master','Master'),
                            ('plan','Monthly'),
                            ('weekly','Weekly')], required=True, string='Plan Type', default='plan')

    def import_plan(self):
        maintenance_plan_obj = self.env['maintenance.plan.line']
        plan_exca = self.env['mining.plan.exca.hour.prod']
        technic_ids = self.env['technic.equipment'].search([('branch_id', '=', self.branch_id.id),
                                                            ('technic_type', 'in', ['excavator', 'wheel_loader', 'dump'])])
        
        delta = timedelta(days=1)
        start_date = self.date_start
        end_date = self.date_end
        branch_id = self.branch_id
        while start_date <= end_date:
            date = str(start_date)
            for technic in technic_ids:
                data = {
                    'date': date,
                    'branch_id': branch_id.id,
                    'technic_id': technic.id,
                    'line_type': self.type,
                }
                hour_prod = plan_exca.get_hour_production(date, technic, branch_id, False)
                if hour_prod:
                    _logger.info(u'+++++YES get_hour_production+++ %s' % (technic.display_name))
                    found = self.env['mining.plan.technic.line'].search([('date','=',date),('line_type','=',self.type),('technic_id','=',technic.id),('branch_id','=',branch_id.id)])
                    if not found:
                        m_line_id = self.env['mining.plan.technic.line'].create(data)
                    else:
                        _logger.info(u'+++++YES found plan+++ %s' % (found.display_name))
                # else:
                #     _logger.info(u'-------NOOOOO get_hour_production------ %s' % (technic.display_name))
                    
            start_date += delta

        


