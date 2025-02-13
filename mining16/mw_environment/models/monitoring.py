# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

class MwEnviromentMonitorComponent(models.Model):
    _name = 'env.monitor.component'
    _description = 'Environmental Monitor Line'
    _rec_name = 'info'

    monitor_id = fields.Many2one('env.monitor', string='Monitor', ondelete='cascade')

    @api.depends('indicator')
    def _get_info(self):
        for item in self:
            if item.indicator:
                item.info = str(item.indicator.normal_start)+" - "+str(item.indicator.normal_end) + " " + item.indicator.uom
            else:
                item.info = False
    info = fields.Char('Байх ёстой хэмжээ', compute=_get_info, store=True)
    is_exist = fields.Selection([
        ('yes', 'Илэрсэн'),
        ('no', 'Илрээгүй')], string='Илэрсэн эсэх')
    amount = fields.Float('Гарсан хэмжээ')
    indicator = fields.Many2one('env.standard', string='Үзүүлэлт')
    enter_type = fields.Boolean(string='Тоо хэмжээгээр бүртгэх', default=True)
    is_suspicious = fields.Boolean(string='Зөрчилтэй эсэх', default = False, readonly=True)

    def get_breaches(self, mlocation):
        self._cr.execute("""
                        SELECT distinct on (c.indicator) c.indicator, m.monitor_date, COALESCE(c.enter_type,true) AS enter_type,
                        c.info, p.name monitor_type, s.name indicator_name, c.amount, s.uom, c.is_exist
                        FROM env_monitor_component c
                        LEFT JOIN env_monitor m ON c.monitor_id=m.id
                        LEFT JOIN env_standard s ON c.indicator=s.id
                        LEFT JOIN env_parameter p ON m.monitor_type=p.id
                        WHERE m.monitor_location=""" + str(mlocation) + """ AND
                        (((c.enter_type=true OR c.enter_type IS NULL) AND (c.amount<s.normal_start OR c.amount>s.normal_end))
                        OR (c.enter_type=false AND c.is_exist='yes'))
                        ORDER BY indicator, m.monitor_date DESC
                        """)
        rows = self._cr.dictfetchall()
        if rows:
            strTable = "<table border='1'><tr><th>Үзүүлэлт</th><th>Байх ёстой хэмжээ</th><th>Тоо хэмжээ</th></tr>"
            for row in rows:
                if row["enter_type"]:
                    strTable +="<tr><td>" + (row["indicator_name"] if row["indicator_name"] else " ") +"</td><td>"+(row["info"] if row['info'] else " ")+"</td><td>"+str(row["amount"]) + row["uom"] + "</td></tr>"
                else:
                    strTable += "<tr><td>" + (row["indicator_name"] if row["indicator_name"] else " ") + "</td><td>" + (row["info"] if row['info'] else " ") + "</td><td>Илэрсэн</td></tr>"
            strTable += "</table>"
            return strTable
        else:
            return ""

    @api.onchange('enter_type')
    def typeonchange(self):
        if self.enter_type:
            self.amount = 0
            self.is_exist = False
        else:
            self.amount = False
            self.is_exist = 'no'

    @api.model
    def create(self, vals):
        res = super(MwEnviromentMonitorComponent, self).create(vals)
        location = self.env['env.mining.line'].search([('id','=', res.monitor_id.monitor_location.id)], limit=1)
        breaches = self.get_breaches(res.monitor_id.monitor_location.id)
        location.write({
            'bad_monitor': False if breaches == "" else True
        })
        # check if current element's amount is not iin acceptable range
        parent_record = self.env['env.monitor'].search([('id', '=', res.monitor_id.id)], limit=1)
        if res.amount:
            if (res.amount < res.indicator.normal_start):
               print("the amount is less than normal start")
            if (res.amount > res.indicator.normal_end):
               print("the amount is greater than normal start")
        # *************************************************************

        return res

    @api.model
    def write(self, vals):
        res = super(MwEnviromentMonitorComponent, self).write(vals)
        location = self.env['env.mining.line'].search([('id', '=', self.monitor_id.monitor_location.id)], limit=1)

        breaches = self.get_breaches(self.monitor_id.monitor_location.id)
        location.write({
            'bad_monitor': False if breaches == "" else True
        })
        # check if current element's amount is not iin acceptable range
        parent_record = self.env['env.monitor'].search([('id', '=', self.monitor_id.id)], limit=1)
        for rec in self:
            if rec.amount:
                if (rec.amount < rec.indicator.normal_start):
                    vals.update({'is_suspicious': True})
                    rec = super(MwEnviromentMonitorComponent, self).write(vals)
                    # if (parent_record.is_error_inspected == False):
                    #parent_record.write({'is_error_inspected':True})

                if rec.amount and rec.indicator.normal_start:
                    # (rec.amount > rec.indicator.normal_end)
                    vals.update({'is_suspicious': True})
                else:
                    vals.update({'is_suspicious': False})

                rec = super(MwEnviromentMonitorComponent, self).write(vals)
                    # if (parent_record.is_error_inspected == False):
                    #parent_record.write({'is_error_inspected':True})
        # *************************************************************
            else:
                False

        return res

class mw_enviroment_monitor_animal(models.Model):
    _name = 'env.monitor.animal'
    _description = 'Environmental Animal Monitor Line'

    monitor_id = fields.Many2one('env.monitor', string='Monitor', ondelete='cascade')
    animal = fields.Many2one('env.parameter', string='Ан амьтан', required=True, domain="[('type','=','animal'),('is_active','=', 'active')]")
    animal_category = fields.Selection('Амьтны ангилал', related='animal.category', store=True, readonly=True)
    
    animal_place = fields.Char(string='Байршил')
    animal_number = fields.Float(string='Тоо')
    species_type = fields.Selection([
        ('plenty', 'Элбэг'),
        ('rare', 'Ховор'),
        ('toorare', 'Нэн ховор')], string='Харагдсан тоо')
    gender = fields.Selection([
        ('male', 'Эр'),
        ('female', 'Эм'),], string='Хүйс')

class mw_enviroment_monitor_plant(models.Model):
    _name = 'env.monitor.plant'
    _description = 'Environmental Plant Monitor Line'

    monitor_id = fields.Many2one('env.monitor', string='Monitor', ondelete='cascade')
    #plant = fields.Many2one('env.parameter', string='Plant', required=True, domain="[('type','=','plant'),('is_active','=', 'active')]")
    plant = fields.Char(string='Ургамал', required=True)
    species_type = fields.Selection([
        ('plenty', 'Элбэг'),
        ('rare', 'Ховор'),
        ('toorare', 'Нэн ховор')], string='Төлөв')
    drude_scaling = fields.Selection([
        ('soc', 'soc (100%)'),
        ('cop3', 'cop3 (50%-100%)'),
        ('cop2', 'cop2 (25%-50%)'),
        ('cop1', 'cop1 (10%-25%)'),
        ('sparsae', 'sparsae (1%-10%)'),
        ('sol', 'sol (0.1%-1%)'),
        ('rr', 'rr (Ганц нэг)'),
        ('un', 'un (Цорын ганц)')
    ], string='Арви', required=True)
    amount = fields.Float(string="Бүрхэц", required=True)

class mw_enviroment_monitor_plant_detail(models.Model):
    _name = 'env.monitor.plant.detail'
    _description = 'Environmental Plant Detail Monitor Line'

    grind_level = fields.Selection([
        ('low', 'Бага'),
        ('medium', 'Дунд зэрэг'),
        ('high', 'Их')], string='Талхлагдлын зэрэг')
    tusgag =fields.Char(string='Тусгаг бүрхэц')
    biomass = fields.Float('Биомасс (гр/м2)') # 1m2/g
    plant_height = fields.Char('Ургамлын өндөр')
    properties = fields.Text('Төлөв байдал')
    impact = fields.Text('Нөлөөлөл')

    @api.model
    def create(self, vals):
        if vals:
            res = super(mw_enviroment_monitor_plant_detail, self).create(vals)
        else:
            res = self.search([('id', '>=', 1)], limit=1)
            if not res:
                res = super(mw_enviroment_monitor_plant_detail, self).create(vals)
        return res

class mw_environment_monitor(models.Model):
    _name = 'env.monitor'
    _description = "Environmental Monitoring"
    _inherits = {'env.monitor.plant.detail': "detail_id"}
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'monitor_date DESC'
    _rec_name = "monitor_date"

    def default_location(self):
        location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
        if location:
            return location.id
        else:
            return False

    state = fields.Selection([('draft', 'Ноорог'),('done', 'Батлагдсан')], 'Төлөв', readonly=True, tracking=True, default='draft')
    mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', required=True, domain="[('is_active','=', 'active')]", defautl=default_location)
    monitor_category = fields.Selection([
        ('monitor3', 'Агаар'),
        ('monitor1', 'Ус'),
        ('monitor2', 'Хөрс'),
        ('monitor4', 'Амьтан'),
        ('monitor5', 'Ургамал'),
        ('monitor7', 'Дуу чимээ')], string='Шинжилгээний ангилал', required=True)
    monitor_date = fields.Date('Шинжилсэн огноо', required=True,  default=fields.Datetime.now)
    monitor_location = fields.Many2one('env.mining.line', string='Шинжилгээний цэг', required=True, domain="[('mining_id','=',mining_location),('monitor_category','=',monitor_category),('is_active','=', 'active')]")
    monitor_type = fields.Many2one('env.parameter', string='Шинжлүүлсэн үзүүлэлт', required=True)
    monitor_lab = fields.Selection([
        ('internal', 'Дотоодын лаб'),
        ('external', 'Гадны лаб')], string='Шинжилсэн газар', default='internal', required=True)
    water_type = fields.Selection([
        ('monitor1', 'Ундны ус'),
        ('monitor8', 'Гүний ус'),
        ('monitor6', 'Бохир ус'),
    ], string='Усны төрөл')
    component_ids = fields.One2many('env.monitor.component', 'monitor_id', string='Indicators')
    animal_ids = fields.One2many('env.monitor.animal', 'monitor_id', string='Animals')
    plant_ids = fields.One2many('env.monitor.plant', 'monitor_id', string='Plants')
    detail_id = fields.Many2one('env.monitor.plant.detail', string='Plants detail', required=True, ondelete='cascade')
    vegetation_area = fields.Char(string='Ургамлын бичиглэл хийсэн талбай')


    def action_to_done(self):
        self.write({'state': 'done'})

    def action_to_draft(self):
        self.write({'state': 'draft'})


    # @api.model
    # def create(self, vals):
    #     if 'water_type' in vals and vals['water_type'] == 'monitor6':
    #             vals['component_ids'] = vals['component_ids2']
    #             vals.pop('component_ids2', None)

    #     res = super(mw_environment_monitor, self).create(vals)
    #     return res


    # @api.model
    # def write(self, vals):
    #     if 'component_ids2' in vals and vals['component_ids2']:
    #         vals['component_ids'] = vals['component_ids2']
    #         vals.pop('component_ids2', None)
    #     res = super(mw_environment_monitor, self).write(vals)
    #     return res

    def name_get(self):
        result = []
        for obj in self:
            result.append(
                (obj.id, obj.monitor_date.strftime('%Y-%m-%d') + ' (' + obj.monitor_type.name + ')'))
        return result

    def fields_get(self, allfields=None, attributes=None):
        res = super(mw_environment_monitor, self).fields_get(allfields, attributes=attributes)
        fields = set(res.keys())
        for field in fields:
            if field in ('create_uid', 'create_date', 'write_uid', 'write_date', 'monitor_category', 'water_type', 'component_ids', 'animal_ids', 'plant_ids', 'detail_id'):
                res[field]['selectable'] = False  # to hide in Add Custom filter view
                res[field]['sortable'] = False  # to hide in group by view
                res[field]['exportable'] = False  # to hide in export list
                res[field]['store'] = False  # to hide in 'Select Columns' filter in tree views
        return res

    def action_fetch_elements(self):
        for monitoring in self:
            monitoring_items_lines = self.env['env.monitoring.items.line'].search([
                ('monitor_type', '=', monitoring.monitor_type.id),
                ('monitor_category', '=', monitoring.monitor_category)
            ])
            if monitoring_items_lines:
                for monitoring_items_line in monitoring_items_lines:
                    data = {
                        'monitor_id': monitoring.id,
                        'indicator': monitoring_items_line.monitor_element.id,
                    }
                    self.env['env.monitor.component'].create(data)

    @api.depends('indicator')
    def _get_info(self):
        for item in self:
            if item.indicator:
                item.info = str(item.indicator.normal_start) + " - " + str(
                    item.indicator.normal_end) + " " + item.indicator.uom
            else:
                item.info = False

    info = fields.Char('Normal Range', compute=_get_info, store=True)
    is_exist = fields.Selection([
        ('yes', 'Илэрсэн'),
        ('no', 'Илрээгүй')], string='Exist')
    amount = fields.Float('Amount')
    indicator = fields.Many2one('env.standard', string='Үзүүлэлт')
    enter_type = fields.Boolean(string='Enter Amount', default=True)

    def check_error_inspected(self):
       for rec in self:
            component_suspicious = self.env['env.monitor.component'].search(
                [('monitor_id', '=', rec.id), ('is_suspicious', '=', True)])

            if component_suspicious:
                err_inspected = True
            else:
                err_inspected = False

            rec.is_error_inspected = err_inspected
        #     *********

    is_error_inspected = fields.Boolean(string='Зөрчилтэй эсэх', readonly=True, compute="check_error_inspected")
class mw_environment_monitoring_items(models.Model):
    _name = 'env.monitoring.item'
    _description = "Environmental Monitoring Item"
    _rec_name = "monitor_category"


    monitor_category = fields.Selection([
        ('monitor3', 'Агаар'),
        ('monitor1', 'Ус'),
        ('monitor2', 'Хөрс'),
        ('monitor4', 'Амьтан'),
        ('monitor5', 'Ургамал'),
        ('monitor7', 'Дуу чимээ')], string='Шинжилгээний ангилал', required=True)

    monitor_type = fields.Many2one('env.parameter', string='Шинжилгээний төрөл', required=True, domain="[('category','=',monitor_category),('is_active','=', 'active'),('type','=', 'monitor_type')]")
    element_line_ids = fields.One2many('env.monitoring.items.line', 'monitor_item_id')

    @api.model
    def create(self, vals):
        value = self.search(
            [('monitor_category', '=', vals['monitor_category']), ('monitor_type', '=', vals['monitor_type'])])
        if value:
            raise Warning(u'Анхааруулга!! Сонгосон шинжилгээний үзүүлэлт үүссэн байгаа тул дахин үүсгэх боломжгүй.')
        else:
            res = super(mw_environment_monitoring_items, self).create(vals)
            return res
class mw_environment_monitoring_item_line(models.Model):
    _name = 'env.monitoring.items.line'
    _description = "Environmental Monitoring Items Line"

    monitor_item_id = fields.Many2one('env.monitoring.item', string='Monitoring Item', ondelete='cascade')
    monitor_category = fields.Selection([
        ('monitor3', 'Агаар'),
        ('monitor1', 'Ус'),
        ('monitor2', 'Хөрс'),
        ('monitor4', 'Амьтан'),
        ('monitor5', 'Ургамал'),
        ('monitor7', 'Дуу чимээ')], string='Шинжилгээний ангилал', required=True)

    monitor_type = fields.Many2one('env.parameter', string='Шинжилгээний төрөл', required=True, domain="[('category','=',monitor_category),('is_active','=', 'active'),('type','=', 'monitor_type')]")
    monitor_element = fields.Many2one('env.standard', string='Шинжилгээний элемент', required=True, domain="[('category','=',monitor_category),('is_active','=', 'active')]")

    @api.depends('monitor_element')
    def _get_info(self):
        for item in self:
            if item.monitor_element:
                item.info = str(item.monitor_element.normal_start) + " - " + str(
                    item.monitor_element.normal_end) + " " + item.monitor_element.uom
            else:
                item.info = False

    info = fields.Char('Normal Range', compute=_get_info, store=True)