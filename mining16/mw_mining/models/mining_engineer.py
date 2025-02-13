# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from calendar import monthrange
##########################


TYPE_SELECTION = [('mining', 'Mining')
                  ,('repair', 'Repair')
                  ,('env', 'Environmental')
                  ,('engineer', 'Engineer work')
                  ,('other', 'Other')]

class mining_pile_measurement(models.Model):
    _name = 'mining.pile.measurement'
    _description = 'Mining Pile Measurement'
    _inherit = ['mail.thread']

    # by Bayasaa Өдөрөөр салгах

    @api.depends('balance_by_measurement_m3','material_id')
    def _set_all(self):
        for obj in self:
            obj.balance_by_measurement_tn = obj.balance_by_measurement_m3 * obj.material_id.lcm_coefficient


    @api.depends('mining_pile_id')
    def _set_report(self):
        for obj in self:
            obj.report_m3 = obj.mining_pile_id.balance_by_report_m3
            obj.report_tn = obj.mining_pile_id.balance_by_report_tn

    mining_pile_id = fields.Many2one('mining.pile','Piles', required=True)
    branch_id = fields.Many2one('res.branch','Branch', required=True, states={'draft': [('readonly',False)]} )
    date = fields.Datetime('Огноо', required=True)
    balance_by_measurement_m3 = fields.Float('Хэмжилтээр м3', required=True, tracking=True)
    balance_by_measurement_tn = fields.Float(string='Хэмжилтээр тонн', compute='_set_all', readonly=True, store=True)
    material_id = fields.Many2one('mining.material', related='mining_pile_id.material_id', readonly=True)
    location = fields.Char(related='mining_pile_id.pile_location', readonly=True)
    report_m3 = fields.Float(string='Мэдээгээр м3', compute='_set_report', readonly=True, store=True)
    report_tn = fields.Float(string='"Мэдээгээр тонн', compute='_set_report', eadonly=True, store=True)
    is_replace =  fields.Boolean('Орлуулах', help=u'Үүнийг сонгосон дохиолдолд тухайн овоолгын ДИСПЕТЧЕР мэдээний үлдэгдэл сонгосон өдрөөс эхлэн тооцогдож эхлэнэ!!!')
    user_id = fields.Many2one('res.users','Бүртгэсэн', default=lambda self: self.env.user)

    _order = "date desc"
    _sql_constraints = [
        ('mppid_pid_uniq', 'UNIQUE(mining_pile_id,date)', 'Date and pile  must be unique!')
    ]


class mining_surveyor_measurement(models.Model):
    _name = 'mining.surveyor.measurement'
    _description = 'Mining Surveyor Measurement'
    _inherit = ['mail.thread']
    _order = 'date desc, branch_id, material_id, excavator_id'

    # @api.onchange('branch_id')
    # def onchange_project(self, cr, uid, ids, branch_id, context={}):
    #     res = {}
    #     idd = []
    #     branch_ids = self.pool.get('res.branch').search(cr,uid,[('id','=',branch_id)])
    #     for project in self.pool.get('res.branch').browse(cr,uid,branch_ids,context=context):
    #         for line in res.branch_product_category:
    #             idd.append(line.id)
    #         res['value'] = {'cats':idd}
    #     return res

    def adjust_grid(self, row_domain, column_field, column_value, cell_field, change):
        if column_field != 'date' or cell_field != 'total_amount':
            raise ValueError(
                "{} can only adjust unit_amount (got {}) by date (got {})".format(
                    self._name,
                    cell_field,
                    column_field,
                ))

        additionnal_domain = self._get_adjust_grid_domain(column_value)
        domain = expression.AND([row_domain, additionnal_domain])
        line = self.search(domain)

        day = column_value.split('/')[0]
        if len(line) > 1:  # copy the last line as adjustment
            line[0].copy({
                'name': 'Pit update',
                column_field: day,
                cell_field: change
            })
        elif len(line) == 1:  # update existing line
            line.write({
                cell_field: line[cell_field] + change
            })
        else:  # create new one
            self.search(row_domain, limit=1).copy({
                'name': _('Timesheet Adjustment'),
                column_field: day,
                cell_field: change
            })
        return False
        
    def _get_adjust_grid_domain(self, column_value):
        # span is always daily and value is an iso range
        day = column_value.split('/')[0]
        return [('date', '=', day)]

    @api.depends('line_ids','month_diff')
    def _total_amount(self):
        for plan in self:
            total = 0.0
            total_tn = 0.0
            total_soil_m3 = 0.0
            avg_bcm = 0.0
            bcm_count = 0
            for line in plan.line_ids:
                if line.is_production:
                    total +=line.amount_by_measurement
                    total_tn += line.amount_by_measurement_tn
                    if line.material_id.mining_product_type !='mineral':
                        total_soil_m3 += line.amount_by_measurement

                    if line.material_id.mining_product_type =='mineral':
                        avg_bcm += line.bcm_coefficient
                        bcm_count += 1
            if bcm_count!=0:
                avg_bcm = avg_bcm/bcm_count
            plan.total_amount = total + plan.month_diff
            plan.total_amount_tn = total_tn
            plan.total_amount_soil_m3 = total_soil_m3
            plan.avg_bcm_coefficient = avg_bcm


    date = fields.Date('Date', states={'draft': [('readonly',False)]} )
    date_start = fields.Date(string='Start date',)
    date_end = fields.Date(stirng='End date',)
    branch_id = fields.Many2one('res.branch','Branch', required=True, states={'draft': [('readonly',False)]}, default=lambda self: self.env.user.branch_id)
    line_ids = fields.One2many('mining.surveyor.measurement.line', 'mining_surveyor_measurement_id', 'Mining Surveyor Measurement Lines', readonly=True, states={'draft':[('readonly',False)]} )
    state = fields.Selection([('draft', 'Ноорог'),('approved', 'Батлагдсан')], 'State',  default='draft', readonly=True, tracking=True)
    description = fields.Text('Тайлбар')
    total_amount = fields.Float(compute="_total_amount", string='Total m3', store=True)
    total_amount_tn = fields.Float(compute="_total_amount", string='Total tn', store=True)
    total_amount_soil_m3 = fields.Float(compute="_total_amount", string='Total soil m3', store=True)
    avg_bcm_coefficient = fields.Float(compute="_total_amount", string='Дундаж BCM Коэффициент', group_operator="avg")
    excavator_id =fields.Many2one('technic.equipment', 'Exac', states={'draft': [('readonly',False)]})
    technic_type =fields.Char('Technic Type',readonly=True, compute='_compute_type', store=True)
    owner_type =fields.Char('Owner Type',readonly=True, compute='_compute_type', store=True)
    technic_partner_id =fields.Many2one('res.partner', 'Technic Partner',readonly=True, compute='_compute_type', store=True)
    user_id = fields.Many2one('res.users','Бүртгэсэн', default=lambda self: self.env.user)
    actual_dpr = fields.Float(compute="_total_actual_dpr", string='Actual DPR')
    diff_dpr = fields.Float(compute="_total_actual_dpr", string='DIFF DPR')
    month_diff = fields.Float(string='Month DIFF')
    total_amount_month = fields.Float(string='Total m3 MONTH')
    material_id = fields.Many2one('mining.material','Material', compute='com_material_id', store=True)

    @api.depends('line_ids')
    def com_material_id(self):
        for item in self:
            if item.line_ids:
                item.material_id = item.line_ids[0].material_id.id
            else:
                item.material_id = False
    
    @api.constrains('line_ids')
    def check_material(self):
        for item in self:
            if len(item.line_ids)>1:
                raise UserError('Нэг мөр хэмжилтийн мөр оруулах ёстой')

    @api.depends('date','total_amount','excavator_id','branch_id')
    def _total_actual_dpr(self):
        for item in self:
            sum_m3 = sum(self.env['mining.production.entry.line'].search([('excavator_id','=',item.excavator_id.id),('date','=',item.date),('production_id.branch_id','=',item.branch_id.id)]).mapped('sum_m3'))
            item.actual_dpr = sum_m3
            item.diff_dpr = item.actual_dpr - item.total_amount

    def update_month(self):
        y = self.date.year
        m = self.date.month
        end_d = monthrange(int(y), int(m))[1]
        s_date = '%s-%s-01'%(y,m)
        e_date = '%s-%s-%s'%(y,m,end_d)
        bran_sur_ids = self.env['mining.surveyor.measurement'].search([('date','>=',s_date),('date','<=',e_date),('branch_id','=',self.branch_id.id)])
        bran_sur_ids.update({'month_diff':0})
        tot_m3 = sum(bran_sur_ids.mapped('total_amount'))
        tot_len =len(bran_sur_ids)
        
        if self.total_amount_month>0:
            diff = (self.total_amount_month - tot_m3)
            line_diff = 0
            if diff:
                line_diff = diff/tot_len
            if line_diff:
                for item in bran_sur_ids:
                    item.month_diff = line_diff
        

    @api.depends('excavator_id')
    def _compute_type(self):
        for item in self:
            item.technic_type = item.excavator_id.technic_type
            item.owner_type = item.excavator_id.owner_type
            item.technic_partner_id = item.excavator_id.partner_id.id

    #     ('date_project_uniq', 'UNIQUE(date,branch_id)', 'Date and Салбар  must be unique!')
    # ]

    def name_get(self):
        res = []
        for item in self:
            # res_name = super(mining_surveyor_measurement, item).name_get()
            res_n = '{0:,.0f} m3'.format(item.total_amount)
            res.append((item.id, res_n))
        return res

    def confirm(self):
        return self.write({'state': 'approved'})


    def refuse(self):
        return self.write({'state': 'draft'})

    @api.constrains('date', 'branch_id','excavator_id','material_id')
    def _check_daily_surveyor_measurement_by_material(self):
        if self.env['mining.surveyor.measurement'].search([('date','=',self.date),('branch_id','=',self.branch_id.id),('excavator_id','=',self.excavator_id.id),('material_id','=',self.material_id.id),('id','!=',self.id)]) and self.date and self.branch_id and self.excavator_id and self.material_id:
            raise ValidationError(('{0} өдрийн {1} салбар дахь {2} экскаваторын {3} материалын бүртгэл давхардаж байна.').format(self.date,self.branch_id.name,self.excavator_id.name,self.material_id.name))


class mining_surveyor_measurement_line(models.Model):
    _name = 'mining.surveyor.measurement.line'
    _description = 'Mining Surveyor Measurement Line'


    @api.depends('material_id','amount_by_measurement')
    def _sum_all(self):
        for obj in self:
            if obj.material_id:
                obj.bcm_coefficient = obj.material_id.bcm_coefficient
                if obj.bcm_coefficient:
                    obj.amount_by_measurement_tn = obj.amount_by_measurement*obj.bcm_coefficient
                else:
                    obj.amount_by_measurement_tn = 0
            else:
                obj.amount_by_measurement_tn = 0


    mining_surveyor_measurement_id = fields.Many2one('mining.surveyor.measurement','Маркшейдерын Хэмжилт', required=True, ondelete='cascade')
    material_id = fields.Many2one('mining.material','Material', required=True)
    amount_by_measurement = fields.Float('Measurement result')
    amount_by_measurement_tn = fields.Float(compute="_sum_all", string='By measurement тн', store=True)
    is_production = fields.Boolean('Бүтээлд', default=True)
    location_id = fields.Many2one('mining.location','Блок')
    is_reclamation = fields.Boolean('Нөхөн сэргээлт эсэх')
    bcm_coefficient = fields.Float(compute='_sum_all', string='BCM Коэффициент', group_operator="avg", store=True, digits=(16,5))
    month_diff_line = fields.Float(string='Month DIFF Line', compute='com_month_diff_line')
    amount_by_measurement_with_diff = fields.Float(string='Measurement result with Diff', compute='com_month_diff_line')

    @api.depends('amount_by_measurement','mining_surveyor_measurement_id.month_diff')
    def com_month_diff_line(self):
        for item in self:
            line_len = len(item.mining_surveyor_measurement_id.line_ids.filtered(lambda r:r.is_production))
            item.month_diff_line = (item.mining_surveyor_measurement_id.month_diff)/line_len if line_len else 0
            item.amount_by_measurement_with_diff = item.amount_by_measurement + item.month_diff_line

    _sql_constraints = [
        ('product_uniq', 'UNIQUE(mining_surveyor_measurement_id,material_id,location_id)', 'Product and Location must be unique!')
    ]

class res_branch(models.Model):
    _inherit = "res.branch"


    project_type = fields.Selection([('mining_project','Mining Салбар'),('plan','Plan')],'Салбар Type')
    mineral_type = fields.Selection([('gold','Gold'),('coal','Coal'),('ore','Ore')],'Mineral Type')
    #     project_product_category': fields.many2many('product.category', 'project_product_category_rel', 'branch_id', 'category_id','Mining Categories'),
    #     'project_sequence': fields.Integer('Салбар Sequence'),
    # }
