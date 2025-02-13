# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
    
class power_down(models.Model):
    _name = 'power.down'
    _description = 'power down'
    
    notes_id = fields.Many2one('power.notes', 'Шуурхайн Бүртгэлд Тасралт', ondelete='cascade')
    notes_order_id = fields.Many2one('power.notes', 'Шуурхайн Бүртгэлд Захиалга', ondelete='cascade')
    notes_plan_id = fields.Many2one('power.notes', 'Шуурхайн Бүртгэлд Төлөвлөгөө', ondelete='cascade')
    notes_call_id = fields.Many2one('power.notes', 'Шуурхайн Бүртгэлд Дуудлагаар', ondelete='cascade')
    notes_daily_id = fields.Many2one('power.notes', 'Шуурхайн Бүртгэлд Өдөр тутмын', ondelete='cascade')
    station_id = fields.Many2one('power.category', domain="[('main_type','in',['categ','asset'])]", string='Станц')
    level_id = fields.Many2one('power.selection', domain="[('type','=','power_level')]",  string='Хүчдлийн түвшин')
    fider_id = fields.Many2one('power.category', domain="[('main_type','in',['asset'])]", string='Фидер')
    work_secure_id = fields.Many2one('power.selection', domain="[('type','=','work_secure')]",  string='Ажилласан хамгаалалт')
    down_nominal = fields.Char('Тасарсан үеийн номинал гүйдэл /А/')
    down_time = fields.Float('Тасарсан хугацаа /Эхлэх/')
    plug_time = fields.Float('Залгасан хугацаа /Дуусах/')
    break_time = fields.Float('Тасралтын хугацаа /мин/', compute='_compute_diff_time', store=True)
    incomplete_power = fields.Char('Дутуу эрчим хүч /кВт.ц/')
    down_type_id = fields.Many2one('power.selection', domain="[('type','=','down_type')]",  string='Тасралтын Ангилал')
    cause = fields.Char('Шалтгаан')
    actions_taken = fields.Char('Авсан арга хэмжээ')
    work_user_ids = fields.Many2many('res.users', 'power_down_work_res_users_rel', 'power_id', 'user_id', string='Ажилласан бригад')
    description = fields.Text('Тайлбар')
    type = fields.Selection([
        ('down','Тасралт'),
        ('order','Захиалгат'),
        ('plan','Төлөвлөгөөт'),
        ('call','Дуудлагаар'),
        ('daily','Өдөр тутмын'),
        ], string='Төрөл', compute='_compute_parent', store=True)
    
    date = fields.Date(string='Огноо', compute='_compute_parent', store=True)
    cnt = fields.Integer(string='Бүртгэлд', default=1, readonly=True)
    shift = fields.Selection([('night','Шөнө'),('day','Өдөр')], string='Ээлж', compute='_compute_parent', store=True)
    dispatcher_id = fields.Many2one('res.users', 'Ээлжинд диспетчер техникч', compute='_compute_parent', store=True)
    master_id = fields.Many2one('res.users', 'Ээлжинд мастер', compute='_compute_parent', store=True)
    product_expense_ids = fields.One2many('power.product', 'down_id',string='Ашигласан Бараа Материал')
    
    # down_partner_id = fields.Many2one('res.partner',  string='Захиалга өгсөн байгууллга, алба хэлтэс')
    down_partner_id = fields.Many2one('power.selection', domain="[('type','=','company_department')]",string='Захиалга өгсөн байгууллга, алба хэлтэс')
    aan_naryad = fields.Char('ААН-ны Наряд шийдвэрийн дугаар')
    partner_job_position = fields.Char('Захиалга өгсөн хүний нэр албан тушаал')
    partner_notes = fields.Char('Захиалгын утга')
    confirm_user_id = fields.Many2one('res.users', 'Захиалга батласан албан тушаалтан')
    
    work_type_id = fields.Many2one('power.selection', domain="[('type','=','work_type')]",  string='Ажлын ангилал')
    daily_work_type_id = fields.Many2one('power.selection', domain="[('type','=','daily_work_type')]",  string='Өдөр тутмын Ажлын ангилал')
    work_name = fields.Char('Ажлын нэр')
    work_user_id = fields.Many2one('res.users', string='Ажил гүйцэтгэгч')
    
    down_time_plan = fields.Float('Төлөвлөгөө Эхлэх')
    plug_time_plan = fields.Float('Төлөвлөгөө Дуусгах')
    # break_time = fields.Float('Тасралтын хугацаа /мин/', compute='_compute_diff_time', store=True)
    break_time_plan = fields.Float('Төлөвлөгөө Тасралт', compute='_compute_diff_time_plan', store=True)
    diff_plan_actual = fields.Float('Төлөвлөгөө гүйцэтгэлийн зөрүү /мин/', compute='_compute_diff_time_plan', store=True)

    call_department_id = fields.Many2one('hr.department', 'Дуудлага өгсөн хэлтэс')
    call_partner_id = fields.Many2one('res.partner', 'Дуудлага өгсөн хүний нэр')
    call_partner_name = fields.Char('Дуудлага өгсөн хүний нэр')
    call_type_id = fields.Many2one('power.selection', domain="[('type','=','call_type')]",  string='Дуудлага ангилал')
    call_notes = fields.Char('Дуудлагын Агуулга')
    call_time_start = fields.Float('Дуудлага бүртгэж авсан цаг')
    call_time_end = fields.Float('Дуудлага барагдуулсан цаг')
    call_fix_time = fields.Float('Дуудлага барагдуулсан хугацаа', compute='_compute_diff_time_call', store=True, readonly=True)
    call_taken = fields.Char('Дуудлагаар авсан арга хэмжээ')
    call_taken_user_id = fields.Many2one('res.users', 'Дуудлага барагдуулсан монтёр')
    
    start_time = fields.Float('Эхлэх хугацаа')
    end_time = fields.Float('Дуусах хугацаа')
    diff_time = fields.Float('Хугацаа /мин/', compute='_compute_diff_time_work', store=True)
    work_actual = fields.Float('Ажлын хувь /0-100%/')
    eo_ids = fields.One2many('power.workorder', 'down_id', string='Цахилгааны EO', readonly=True)

    @api.depends('date','shift','type')
    def name_get(self):
        result = []
        for s in self:
            name = ''
            if s.type:
                type_name = dict(self._fields['type'].selection).get(s.type)
                name += type_name+' / '
            if s.date:
                name += str(s.date)+' / '
            if s.shift:
                type_name = dict(self._fields['shift'].selection).get(s.shift)
                name += type_name+' / '
            result.append((s.id, name))
        return result
        
    def create_eo(self):
        if self.eo_ids:
            eo_ids = self.eo_ids
            action = self.env.ref('mw_power.action_power_workorder_tree').read()[0]
            action['domain'] = [('id', 'in', eo_ids.ids)]
            return action
            
        parent_id = False
        customer_department_id = False
        device_type = 'device'
        completed_repairs = ''
        time_start = 0
        origin = self.display_name
        work_type_id = False
        level_id = False
        if self.type=='order':
            parent_id = self.notes_order_id
            customer_department_id = self.down_partner_id.id
            completed_repairs = self.partner_notes
            time_start = self.down_time
            if self.aan_naryad:
                origin += ' / '+(self.aan_naryad or '')
            if self.partner_job_position:
                origin += ' / '+(self.partner_job_position or '')
        elif self.type=='plan':
            parent_id = self.notes_plan_id
            work_type_id = self.work_type_id.id
            level_id = self.level_id.id
            # customer_department_id = self.down_partner_id.id
            completed_repairs = self.work_name
            time_start = self.down_time_plan
            if self.aan_naryad:
                origin += ' / '+(self.aan_naryad or '')
            
        elif self.type=='call':
            parent_id = self.notes_call_id
            work_type_id = self.work_type_id.id
            level_id = self.level_id.id
            customer_department_id = self.env['power.selection'].search([('type','=','company_department'),('hr_department_id','=',self.call_department_id.id)], limit=1).id
            completed_repairs = self.call_notes
            time_start = self.call_time_start
            
        elif self.type=='daily':
            parent_id = self.notes_daily_id
            completed_repairs = self.work_name
            time_start = self.start_time
           
        if parent_id:
            obj = self.env['power.workorder']
            origin = self.display_name
            vals = {
                'origin': origin,
                'down_id': self.id,
                'date': self.date,
                'shift': self.shift,
                'customer_department_id': customer_department_id,
                'completed_repairs': completed_repairs,
                'time_start': time_start,
                'level_id': level_id,
                'work_type_id': work_type_id,
            }
            obj.create(vals)
    @api.depends('end_time','start_time','shift')
    def _compute_diff_time_work(self):
        for item in self:
            if item.shift=='night' and item.end_time<item.start_time:
                item.diff_time = item.end_time+24-item.start_time
            else:
                item.diff_time = item.end_time-item.start_time
    @api.depends('plug_time_plan','down_time_plan','break_time','shift')
    def _compute_diff_time_plan(self):
        for item in self:
            if item.shift=='night' and item.plug_time_plan<item.down_time_plan:
                item.break_time_plan = item.plug_time_plan+24-item.down_time_plan
            else:
                item.break_time_plan = item.plug_time_plan-item.down_time_plan
            
            if item.shift=='night' and item.break_time_plan<item.break_time:
                item.diff_plan_actual = item.break_time_plan+24-item.break_time
            else:
                item.diff_plan_actual = item.break_time_plan-item.break_time

    @api.depends('call_time_start','call_time_end','shift')
    def _compute_diff_time_call(self):
        for item in self:
            if item.shift=='night' and item.call_time_end<item.call_time_start:
                item.call_fix_time = item.call_time_end+24-item.call_time_start
            else:
                item.call_fix_time = item.call_time_end-item.call_time_start

    @api.depends('plug_time','down_time','shift')
    def _compute_diff_time(self):
        for item in self:
            if item.shift=='night' and  item.plug_time<item.down_time:
                item.break_time = item.plug_time+24-item.down_time
            else:
                item.break_time = item.plug_time-item.down_time

    @api.depends('notes_id','notes_order_id','notes_plan_id','notes_call_id','notes_daily_id')
    def _compute_parent(self):
        for item in self:
            notes_id = item.notes_plan_id or item.notes_order_id or item.notes_id or item.notes_call_id or item.notes_daily_id
            if item.notes_plan_id:
                item.type = 'plan'
            elif item.notes_order_id:
                item.type = 'order'
            elif item.notes_call_id:
                item.type = 'call'
            elif item.notes_daily_id:
                item.type = 'daily'
            else:
                item.type = 'down'

            if notes_id:
                item.date = notes_id.date
                item.shift = notes_id.shift
                item.dispatcher_id = notes_id.dispatcher_id.id
                item.master_id = notes_id.master_id.id
            
    @api.onchange('call_time_end','call_time_start')
    def onch_time_call(self):
        if self.eo_ids:
            self.eo_ids.write({
                'time_end': self.call_time_end,
                'time_start': self.call_time_start
            })

    @api.onchange('plug_time','down_time')
    def onch_time_down(self):
        if self.eo_ids:
            self.eo_ids.write({
                'time_end': self.plug_time,
                'time_start': self.down_time
            })

    @api.onchange('plug_time_plan','down_time_plan')
    def onch_time_plan(self):
        if self.eo_ids:
            self.eo_ids.write({
                'time_end': self.plug_time_plan,
                'time_start': self.down_time_plan
            })

    @api.onchange('start_time','end_time')
    def onch_time_daily(self):
        if self.eo_ids:
            self.eo_ids.write({
                'time_end': self.end_time,
                'time_start': self.start_time
            })
    