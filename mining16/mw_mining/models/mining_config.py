# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class mining_default_hour(models.Model):
    _name = 'mining.default.hour'
    _description = 'Mining repair default hour'
    _inherit = ['mail.thread']

    start_date = fields.Date('Start date', tracking=True, )
    end_date = fields.Date('End date', tracking=True, )
    technic_id = fields.Many2one('technic.equipment', string='Technic', tracking=True)
    cause_id = fields.Many2one('mining.motohours.cause','Cause', required=True, tracking=True, domain="[('is_repair','=',True)]")
    repair_system_id = fields.Many2one('maintenance.damaged.type', string='Зогссон систем', domain="[('parent_id','=',False)]", store=True, tracking=True)

    def get_default_cause(self, technic_id, date):
        obj_id = self.env['mining.default.hour'].search([('start_date','<=',date),('end_date','>=',date),('technic_id','=',technic_id.id)], limit=1, order='start_date desc')
        if not obj_id:
            obj_id = self.env['mining.default.hour'].search([('start_date','=',False),('end_date','=',False),('technic_id','=',technic_id.id)], limit=1)
        if obj_id:
            return {'cause_id': obj_id.cause_id, 'repair_system_id': obj_id.repair_system_id}
        return False

class miningLocationType(models.Model):
    _name = 'mining.location.type'
    _description = 'mining location type'

    name = fields.Char(string="Уурхай")
    branch_id = fields.Many2one('res.branch',string="Салбар")

# by Bayasaa Байрлалын бүртгэл
class mining_location(models.Model):
    _name = 'mining.location'
    _description = 'Mining location'
    _inherit = ['mail.thread']

    # # by Bayasaa байрлалын үлдэгдэл тооцоолох
    # def _set_balance_m3(self, cr, uid, ids, name, args, context=None):
    #     res = {}
    #     for obj in self.browse(cr, uid, ids):
    #         diff_soil = 0.0
    #         add_soil = 0.0
    #         diff_coal = 0.0
    #         add_coal = 0.0
    #         blasted_min_date = False
    #         for item in obj.for_blast_line:
    #             add_soil += item.blast_soil_m3
    #             add_coal += item.blast_coal_m3
    #             if not blasted_min_date:
    #                 blasted_min_date = item.date
    #             if item.date < blasted_min_date:
    #                 blasted_min_date = item.date

    #         if blasted_min_date:
    #             for item in obj.from_production_line:
    #                 if item.date >= blasted_min_date:
    #                     if item.material_id.mining_product_type == 'mineral':
    #                         diff_coal += item.sum_m3
    #                     else:
    #                         diff_soil += item.sum_m3
    #         for item in obj.for_production_line:
    #             if item.material_id.mining_product_type == 'mineral':
    #                 add_coal += item.sum_m3
    #             else:
    #                 add_soil += item.sum_m3
    #         res[obj.id] = {'balance_soil_m3': (add_soil - diff_soil),'balance_coal_m3': (add_coal - diff_coal)}
    #     return res
    # # by Bayasaa диспетчерийн мэдээнээс өөрлөгдсөн блокыг ID буцаах
    # def _get_production_entry_line(self, cr, uid, entry_ids, context=None):
    #     entry = self.pool.get('mining.production.entry.line').browse(cr, uid, entry_ids, context=context)
    #     res_id = []
    #     for item in entry:
    #         if item.the_from == 'location':
    #             res_id.append(item.from_location.id)
    #         if item.the_for == 'location':
    #             res_id.append(item.for_location.id)
    #     return res_id

    # def _get_daily_entry_line(self, cr, uid, entry_ids, context=None):
    #     entry = self.pool.get('mining.daily.entry').browse(cr, uid, entry_ids, context=context)
    #     res_id = []
    #     for item in entry:
    #         for line in item.production_line:
    #             if line.the_from == 'location':
    #                 res_id.append(line.from_location.id)
    #             if line.the_for == 'location':
    #                 res_id.append(line.for_location.id)
    #     return res_id
    # def _get_blast_entry(self, cr, uid, entry_ids, context=None):
    #     entry = self.pool.get('mining.blast').browse(cr, uid, entry_ids, context=context)
    #     res_id = []
    #     for item in entry:
    #         for line in item.blast_line:
    #             res_id.append(line.location_id.id)
    #     return res_id
    # # by Bayasaa диспетчерийн мэдээнээс өөрлөгдсөн блокыг ID буцаах
    # def _get_blast_entry_line(self, cr, uid, entry_ids, context=None):
    #     entry = self.pool.get('mining.blast.line').browse(cr, uid, entry_ids, context=context)
    #     res_id = []
    #     for item in entry:
    #         res_id.append(item.location_id.id)
    #     return res_id

    name = fields.Char('Name', size=50, required=True, tracking=True)
    where = fields.Char('Where locate', size=128)
    branch_id = fields.Many2one('res.branch','Branch', required=True)
    average_content = fields.Float('Average Content')
    burden = fields.Float('Burden')
    spacing = fields.Float('Spacing')
    bit_size = fields.Float('Bit size')
    is_drilling = fields.Boolean('Drilling', default=False)
    is_blasting = fields.Boolean('Blasting', default=False)

    @api.constrains('branch_id', 'name')
    def _check_name(self):
        if self.env['mining.location'].search([('branch_id','=',self.branch_id.id),('name','=',self.name),('id','!=',self.id)]):
            raise ValidationError(('Салбард блокын нэр давхцахгүй дээр давхцахгүй'))


    # 'for_blast_line = fields.One2many('mining.blast.line','location_id','Location', readonly=True, order='date desc'),
    # 'balance_soil_m3 = fields.function(_set_balance_m3, string='Balance Soil m3', type='Float', multi='balance',
    #         store={
    #                 'mining.daily.entry': (_get_daily_entry_line, ['date'], 20),
    #                 'mining.production.entry.line': (_get_production_entry_line, ['from_pile','for_pile','body_capacity','res_count','sum_soil'], 20),
    #                 'mining.blast': (_get_blast_entry, ['date'], 20),
    #                 'mining.blast.line': (_get_blast_entry_line, ['location_id','blast_coal_m3','blast_soil_m3'], 20),
    #         }),
    # 'balance_coal_m3 = fields.function(_set_balance_m3, string='Balance Coal m3',type='Float', multi='balance',
    #     store={
    #                 'mining.daily.entry': (_get_daily_entry_line, ['date'], 20),
    #                 'mining.production.entry.line': (_get_production_entry_line, ['from_pile','for_pile','body_capacity','res_count','sum_soil'], 20),
    #                 'mining.blast': (_get_blast_entry, ['date'], 20),
    #                 'mining.blast.line': (_get_blast_entry_line, ['location_id','blast_coal_m3','blast_soil_m3'], 20),
    #         }),
    # _sql_constraints = [
    #                     ('name_uniq', 'unique(branch_id,name)', 'Reference must be unique per Name!'),
    # ]

class mining_hole(models.Model):
    _name = 'mining.hole'
    _description = 'Mining Hole'
    _order = 'name'

    name = fields.Char('Name', required=True)
    branch_id = fields.Many2one('res.branch', 'Branch', required=True)
    location_id = fields.Many2one('mining.location', 'Location', required=True)
    tusliin_gun_m = fields.Float('Tusliin gun m', required=True)
    # drilling_line_ids = fields.One2many('mining.drilling.line', 'hole_id', 'Drilling Line')

    # # by Bayasaa тэвшний багтаамж өөрчлөгдөх
    # def on_change_branch_id(self, cr, uid, ids, branch_id, context=None):
    #     value = {
    #         'location_id': False,
    #     }
    #     if ids != []:
    #         self.write(cr, uid, ids, value)
    #     return {
    #         'value':value
    #     }
    # _sql_constraints = [
    #                     ('name_uniq', 'unique(branch_id,location_id,name)', 'Reference must be unique per Name Location! '),
    # ]

class mining_material(models.Model):
    _name = 'mining.material'
    _description = 'Mining material'
    _order = 'name'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code')
    branch_id = fields.Many2one('res.branch', 'Branch')
    mining_product_type = fields.Selection([('soil', 'Хөрс'),('mineral', 'Ашигт малтмал'),('mineral_reprocess', 'Ашигт Малтмал /Дахин Боловсруулах/'),('engineering_work', 'Инженерийн Ажил')], 'Материал ангилал')
    is_productivity = fields.Boolean('Бүтээлд Тооцох Эсэх', help="If checked, It's productivity mining product.")
    bcm_coefficient = fields.Float('BCM Коэффициент', digits=(16,5))
    lcm_coefficient = fields.Float('LCM Коэффициент')
    product_id = fields.Many2one('product.product', string="Бараа")

class mining_hab_category(models.Model):
    _name = 'mining.hab.category'
    _description = 'Mining hab category'
    _oder = 'sequence'

    sequence = fields.Integer('Sequence', default=1)
    name = fields.Char('Name', required=True)
    branch_id = fields.Many2one('res.branch','Branch', required=True)

class mining_dpr_logo(models.Model):
    _name = 'mining.dpr.logo'
    _description = 'Mining dpr logo'
    _oder = 'sequence'

    branch_id = fields.Many2one('res.branch','Branch', required=True)
    logo = fields.Binary('Logo', required=True)


class mining_hab_line(models.Model):
    _name = 'mining.hab.line'
    _description = 'Mining hab line'
    _oder = 'sequence'
    
    sequence = fields.Integer('Sequence', default=1)
    daily_id = fields.Many2one('mining.daily.entry','Daily entry', ondelete='cascade')
    categ_id = fields.Many2one('mining.hab.category','Ажилах хүч', required=True)
    qty = fields.Integer('Тоо', default=1)

# by Bayasaa Техник тохиргоо техникийн тэвшний багтаамжийг зааж өгөх
class mining_technic_configure(models.Model):
    _name = 'mining.technic.configure'
    _description = 'Mining Technic Configure'

    # by Bayasaa Тэвшний багтаамж тонн-оор бодох
    @api.depends('body_capacity_m3','material_id','material_id.mining_product_type')
    def _set_capacity_tn(self):
        for obj in self:
            if obj.material_id.mining_product_type == 'mineral':
                obj.body_capacity_tn = obj.body_capacity_m3 * obj.material_id.bcm_coefficient
            else:
                obj.body_capacity_tn= 0.0

    technic_setting_id = fields.Many2one('technic.equipment.setting', 'Technic Setting', required=True)
    carrying_capacity = fields.Float(related='technic_setting_id.carrying_capacity', string="Struck", readonly=True)
    material_id = fields.Many2one('mining.material','Material', copy=False)
    branch_id = fields.Many2one('res.branch','Branch', required=True)
    body_capacity_m3 = fields.Float('Heaped m3', required=True)
    body_capacity_tn = fields.Float(string='Heaped tn', compute='_set_capacity_tn')

    _sql_constraints = [
        ('name_uniq', 'unique(technic_setting_id, branch_id, material_id)', 'Reference must be unique per Technic Configure, Материал, Салбар!'),
    ]

# by Bayasaa Мотоцагын шалгаан
class mining_motohours_cause(models.Model):
    _name = 'mining.motohours.cause'
    _description = 'Mining Motohours Cause'

    cause_name = fields.Char('Cause name',size=100, required=True)
    name = fields.Char('Cause code', size=10, required=True)
    cause_type = fields.Many2one('mining.motohours.cause.type','Cause type', required=True)
    concentrator_name = fields.Char('Баяжуулах үйлдвэр', size=40)
    color = fields.Selection(related='cause_type.color', string='Color', readonly=True)
    calc_production =fields.Boolean('Бүтээлд Тооцох')
    calc_actual =fields.Boolean('Гүйцэтгэлд тооцох')
    is_repair =fields.Boolean('Is repair')
    is_injury =fields.Boolean('Is injury')
    is_middle = fields.Boolean('Дундын Шалтгаан эсэх', default=False)
    branch_id = fields.Many2one('res.branch',string='Салбар')

    _sql_constraints = [
                        ('name_uniq', 'unique(name)', 'Reference must be unique per Code!'),
    ]
    _order = 'name asc, cause_type asc'

    def name_get(self):
        res = []
        for item in self:
            res_name = super(mining_motohours_cause, item).name_get()
            if item.cause_name and item.name:
                res_name = qty_str = '{0} {1}'.format(item.name, item.cause_name)
                res.append((item.id, res_name))
            else:
                res.append(res_name[0])
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """ search full name and barcode """
        if args is None:
            args = []
        recs = self.search(['|', ('name', operator, name), ('cause_name', operator, name)] + args, limit=limit)
        return recs.name_get()

# by Bayasaa Мотоцагын шалгааны төрөл
class mining_motohours_cause_type(models.Model):
    _name = 'mining.motohours.cause.type'
    _description = 'Mining Motohours Cause'
    TYPE_SELECTION = [('smu', u'АСААЛТТАЙ МОТОЦАГ ГҮЙНЭ'),('non_smu', u'УНТРААСТАЙ МОТОЦАГ ГҮЙХГҮЙ')]

    # by Bayasaa Нэр оноох
    @api.depends('type_name','type')
    def _name_set_fnc(self):
        for obj in self:
            test = dict(self.TYPE_SELECTION)
            obj.name = obj.type_name+' /'+test[str(obj.type)]+'/'


    name =fields.Char(string='Name', compute='_name_set_fnc', store=True)
    type_name = fields.Char('Name', size=100, required=True)
    type = fields.Selection(TYPE_SELECTION, 'Type', default='non_smu', required=True)
    color = fields.Selection([('green', 'Green'),('blue', 'Blue'),('darkblue', 'Dark Blue'),('gold', 'Yellow'),('darkorange', 'Orange'),('red', 'Red'),('brown', 'Brown'),('purple', 'Purple'),('magenta', 'Magenta'),('darkseagreen', 'Darkseagreen')], 'Color', required=True)
    level =fields.Char('Level',required=True)

    _order = 'name asc, type asc'

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Reference must be unique per Name!'),
    ]
# by Bayasaa Баяжуулах үйлдвэрийн бүртгэл
class mining_concentrator(models.Model):
    _name = 'mining.concentrator'
    _description = 'Mining Concentrator'

    name = fields.Char('Name',size = 30, required=True)
    hour_productivity = fields.Float('Time productivity',required=True)
    write_date = fields.Date('Edited date', readonly=True)
    branch_id = fields.Many2one('res.branch','Branch', required=True)

    _sql_constraints = [
                        ('name_uniq', 'unique(name,branch_id)', u'Reference must be unique per Name, Салбар!'),
    ]
# by Bayasaa Баяжуулах үйлдвэрийн шалтгаан
class mining_concentrator_cause(models.Model):
    _name = 'mining.concentrator.cause'
    _description = 'Mining Concentrator Cause'

    cause_name = fields.Char('Cause name',size=100, required=True)
    name = fields.Char('Cause code', size=30, required=True)

    _sql_constraints = [
                        ('name_uniq', 'unique(name)', ''),
    ]


# by Bayasaa Техник
class technic_equipment(models.Model):
    _inherit = 'technic.equipment'

    hour_productivity = fields.Float('Time productivity')
    mining_capacity = fields.Float('Capacity м3')
    default_hour_ids = fields.One2many('mining.default.hour','technic_id', string='Засварын удаан зогсох цаг',groups="mw_mining.group_mining_user")

    # ТББК ыг авах
    def get_technic_tbbk(self, date_from, date_to):
        mh_ids = self.env['mining.motohour.entry.line'].sudo().search(
                        [('date','>=',date_from),
                         ('date','<=',date_to),
                         ('technic_id','=',self.id)])
        # Нийт засварын цаг
        repair_time = sum(mh_ids.mapped('repair_time'))
        # ТББК бодох
        start_date = datetime.strptime(date_from, "%Y-%m-%d")
        end_date = datetime.strptime(date_to, "%Y-%m-%d")
        days = (end_date-start_date).days + 1
        norm = self.technic_setting_id.work_time_per_day or 1

        tbbk = 100 - (repair_time*100)/(norm*days)
        res = { 'tbbk': tbbk, 'repair_time': repair_time }
        return res

class mining_pile(models.Model):
    _name = "mining.pile"
    _description = "Mining Pile"
    _inherit = ['mail.thread']

    # by Bayasaa нэр олгох
    @api.depends('name','branch_id')
    def _set_name(self):
        for obj in self:
            obj.location_name = obj.name+u' '+obj.branch_id.name

    # @api.model
    # def create(self, values):
    #     stock_value = {}
    #     if 'is_warehouse' in values:
    #         if values['is_warehouse']:
    #             account = self.pool.get('account.account').search(cr,uid,[],context=context)
    #             stock_value['name'] = values['name']
    #             stock_value['account_expense_id'] = account[0]
    #             stock_value['account_income_id'] = account[0]
    #             stock_value['stock_account_input_id'] = account[0]
    #             stock_value['stock_account_output_id'] = account[0]
    #             stock_value['stock_valuation_account_id'] = account[0]

    #             journal = self.pool.get('account.journal').search(cr,uid,[],context=context)
    #             stock_value['stock_journal_id'] = journal[0]

    #             stock_value['address'] = 'stock'
    #             stock_value['department_id'] = self.pool.get('res.branch')._get_project_department(cr,uid,values['branch_id'])
    #             stock_id = self.pool.get('stock.warehouse').create(cr,uid,stock_value,context=context)
    #     return super(mining_pile, self).create(cr, uid, values, context=context)

    # by Bayasaa овоолгын үлдэгдэл тооцоолох
    @api.depends('measurement_line.balance_by_measurement_m3', 'measurement_line.is_replace','from_concentrator_line','for_production_line')
    def _set_balance_by_report(self):
        for obj in  self:
            max_date = False
            balance_m3 = 0.0
            balance_tn = 0.0
            add_m3 = 0.0
            add_tn = 0.0
            diff_tn = 0.0
            diff_m3 = 0.0

            # for line in obj.measurement_line:
            #     if max_date < line.date and line.is_replace:
            #         max_date = line.date
            #         balance_m3 = line.balance_by_measurement_m3
            #         balance_tn = line.balance_by_measurement_tn

            # if max_date:
            #     add_m3 = balance_m3
            #     add_tn = balance_tn
            # for item in obj.from_production_line:
            #     if max_date<=item.date:
            #         diff_m3 += item.sum_m3
            #         diff_tn += item.sum_tn

            # for item in obj.from_concentrator_line:
            #     if max_date<=item.date:
            #         diff_m3 += item.production_amount

            # for item in obj.from_coal_sales_line:
            #     if max_date<=item.date:
            #         diff_m3 += item.sales_amount_m3
            #         diff_tn += item.sales_amount_tn

            # for item in obj.for_production_line:
            #     if max_date<=item.date:
            #         add_m3 += item.sum_m3
            #         add_tn += item.sum_tn
            obj.balance_by_report_m3 = add_m3-diff_m3
            obj.balance_by_report_tn = add_tn-diff_tn

    @api.depends('measurement_line.balance_by_measurement_m3', 'measurement_line.is_replace')
    def _set_balance_by_measurement(self):

        # res[obj.id] = obj.balance_by_measurement_m3 * obj.material_id.lcm_coefficient
        for obj in  self:
            max_date = False
            user_id = False
            balance = 0.0
            # for line in obj.measurement_line:
            #     if maxx_date < line.date:
            #         max_date = line.date
            #         balance = line.balance_by_measurement_m3
            #         user_id = line.user_id.name
            obj.balance_by_measurement_m3 = balance
            obj.balance_by_measurement_tn = balance*obj.material_id.lcm_coefficient
            obj.measurement_date = max_date
            obj.replace_measurement_uid = user_id



    # by Bayasaa Confirm
    def action_to_closed(self):
        self.write({'state': 'closed'})

    # by Bayasaa Цуцлах
    def action_to_opened(self):
        self.write({'state': 'opened'})

    name = fields.Char('Нэр', size=128,required=True, tracking=True)
    location_name = fields.Char(string='Блок Нэр', store=True, compute='_set_name')
    material_id = fields.Many2one('mining.material', 'Material', required=True, tracking=True)
    material_type = fields.Selection(related='material_id.mining_product_type')
    branch_id = fields.Many2one('res.branch','Branch', required=True, tracking=True)
    pile_location = fields.Char('Stockpile location', size=128, tracking=True)
    balance_by_report_m3 = fields.Float(string='Мэдээгээр м3', compute='_set_balance_by_report', store=True)
    balance_by_report_tn = fields.Float(string='Мэдээгээр тонн', compute='_set_balance_by_report', store=True)
    balance_by_measurement_m3 = fields.Float(string='Хэмжилтээр м3', compute='_set_balance_by_measurement', store=True)
    balance_by_measurement_tn = fields.Float(string='Хэмжилтээр тонн', compute='_set_balance_by_measurement', store=True)
    measurement_date = fields.Date(string='Хэмжилт Хийгдсэн Өдөр', compute='_set_balance_by_measurement', store=True)
    replace_measurement_uid = fields.Char(string='Хэмжилт Хийсэн', compute='_set_balance_by_measurement', store=True)
    state = fields.Selection([('opened', 'Opened'),('closed', 'Closed')], 'Төлөв', default='opened', tracking=True)
    haul_distance = fields.Float(string='Талын зай', default=0)
    from_production_line = fields.One2many('mining.production.entry.line','from_pile','Овоолгоос', readonly=True, order='date asc')
    for_production_line = fields.One2many('mining.production.entry.line','for_pile','Овоолгоруу', readonly=True, order='date asc')
    from_concentrator_line = fields.One2many('mining.concentrator.production.line','pile_id','Pile ID', readonly=True, order='date asc')
    from_coal_sales_line = fields.One2many('mining.coal.sales.line','pile_id','Pile ID', readonly=True, order='date asc')
    measurement_line = fields.One2many('mining.pile.measurement','mining_pile_id','Pile ID', readonly=True, order='date desc')
    is_concentrator = fields.Boolean('Is Concentrator?')
    concentrator_id = fields.Many2one('mining.concentrator','Баяжуулах үйлдвэр')


    _sql_constraints = [
        # ('pile_balance','CHECK(balance_by_report_m3 >= 0)','Error ! Pile Balance Not Enough'),
        ('pile_name_uniq', 'UNIQUE(location_name,branch_id)', 'Pile name must be unique!')
    ]

    # _defaults = {
    #     'created_date': fields.Date.context_today,
    #     'state': 'opened'
    # }


class mining_dispatcher_import_config(models.Model):
    _name = "mining.dispatcher.import.config"
    _description = "mining dispatcher import config"

    type = fields.Selection([('motoh', 'Motoh'),('prod', 'Prod')], 'Type')
    technic_name_col = fields.Integer('Technic name col Dump Prod', default=2)
    exca_name_row = fields.Integer('Exca name row', default=2)
    exca_name_col = fields.Integer('Exca name col', default=7)
    last_motoh_col = fields.Integer('Last motoh col', default=9)
    last_km_col = fields.Integer('Last km col', default=12)
    lastname_col = fields.Integer('Lastname col', default=8)
    firstname_col = fields.Integer('Firstname col', default=7)
    lines = fields.One2many('mining.dispatcher.import.config.line','parent_id',string='Parent')
    block_col = fields.Integer('block col', default=1)
    level_col = fields.Integer('level col', default=1)
    block_row = fields.Integer('block row', default=4)
    level_row = fields.Integer('level row', default=5)
    pile_col = fields.Integer('pile col', default=7)
    haul_distance_col = fields.Integer('haul distance col', default=6)
    branch_id = fields.Many2one('res.branch', string='Салбар')

class mining_dispatcher_import_config_line(models.Model):
    _name = "mining.dispatcher.import.config.line"
    _description = "mining dispatcher import config line"
    _order = 'sequence'
    sequence = fields.Integer('Seq', default=1)
    parent_id = fields.Many2one('mining.dispatcher.import.config', 'Parent', ondelete='cascade')
    cause_id = fields.Many2one('mining.motohours.cause','Cause')
    material_id = fields.Many2one('mining.material','Material')
    col = fields.Integer('Col')
