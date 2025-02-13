# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools
from odoo.exceptions import ValidationError,UserError
from odoo.tools.translate import _

class power_implements(models.Model):
    _name = 'power.implements'
    _inherit = ['mail.thread']
    _description = 'power implements'
    _order = 'name, asset_id, group_id, categ_id'
    
    image = fields.Binary(string='Logo', required=True, attachment=True,
        help="This field holds the image used as logo for the brand, limited to 1024x1024px.")
    image_medium = fields.Binary("Medium-sized image", attachment=True,
        help="Medium-sized logo of the brand. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized image", attachment=True,
        help="Small-sized logo of the brand. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
    name = fields.Char('Тоноглолын Нэр', required=True, track_visibility='onchange')
    number = fields.Char('Дугаар', track_visibility='onchange')
    mark = fields.Char('Марк', track_visibility='onchange')
    coefficient = fields.Char('Коэффициент', track_visibility='onchange')
    level_id = fields.Many2one('power.selection',domain="[('type','=','power_level')]", string='Хүчдлийн түвшин', track_visibility='onchange')
    categ_id = fields.Many2one('power.category', string='Ангилал', domain=[('main_type','=','categ')], track_visibility='onchange')
    asset_id = fields.Many2one('power.category', string='Хөрөнгө', domain=[('main_type','=','asset')], track_visibility='onchange')
    group_id = fields.Many2one('power.category', string='Станц', domain=[('main_type','=','group')], track_visibility='onchange')
    
    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        return super(power_implements, self).create(vals)

    def write(self, vals):
        tools.image_resize_images(vals)
        return super(power_implements, self).write(vals)

    def name_get(self):
        res = []
        for item in self:
            res_name = super(power_implements, item).name_get()
            if item.number:
                res_name = u''+res_name[0][1]+u' ['+item.number+']'
                res.append((item.id, res_name))
            else:
                res.append(res_name[0])
        return res

    def while_main_type(self, main_type, asset_id):
        categ_ids = self.env['power.category'].search([])
        parent_id = asset_id.parent_id
        if parent_id.main_type==main_type:
            return parent_id
        while parent_id.main_type!=main_type:
            parent_id = parent_id.parent_id
            if not parent_id:
                return False
        return parent_id

    @api.onchange('asset_id')
    def onch_asset_id(self):
        if self.asset_id:
            g_id = self.while_main_type('group', self.asset_id)
            self.group_id = g_id.id if g_id else False
            g_id = self.while_main_type('categ', self.asset_id)
            self.categ_id = g_id.id if g_id else False
        else:
            self.group_id = False
            self.categ_id = False
    
    

class power_category(models.Model):
    _name = 'power.category'
    _description = 'power category'
    _inherit = ['mail.thread']
    # _rec_name = 'complete_name'
    _order = 'complete_name'

    def _get_default_main_type(self):
        return self.env.context.get('main_type', False)
        
    image = fields.Binary(string='Logo', required=True, attachment=True,
        help="This field holds the image used as logo for the brand, limited to 1024x1024px.")
    image_medium = fields.Binary("Medium-sized image", attachment=True,
        help="Medium-sized logo of the brand. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized image", attachment=True,
        help="Small-sized logo of the brand. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
    name = fields.Char('Нэр', required=True, track_visibility='onchange')
    main_type = fields.Selection([
        ('categ','Ангилал'),
        ('asset','Хөрөнгө'),
        ('group','Станц'),
        ], 'Төрөл', required=True, track_visibility='onchange', default=_get_default_main_type)
        
    complete_name = fields.Char(
        'Бүтэн Нэр', compute='_compute_complete_name',
        store=True)
    parent_id = fields.Many2one('power.category', 'Дээд ангилал', index=True, ondelete='cascade', track_visibility='onchange')
    child_id = fields.One2many('power.category', 'parent_id', 'Доод ангилалууд')
    implements_count = fields.Integer('Тоноглолын тоо', compute='_compute_implements_count')
    is_hats = fields.Boolean(string='Хацд Сонгогдох Эсэх', default=False)
    orolt = fields.Selection([('6','6 Оролт'),('35','35 Оролт')], string='Хацд Сонгогдох Эсэх Оролт Эсэх', default=False)

    eo_device_ids = fields.One2many('power.workorder','power_device_id',sting='EO')
    eo_asset_ids = fields.One2many('power.workorder','asset_id',sting='EO')
    
    eo_count = fields.Integer('Electrical Orders', compute='_compute_eo_count')

    def _compute_eo_count(self):
        for item in self:
            item.eo_count = len(item.eo_device_ids) + len(item.eo_device_ids)

    def view_eo(self):
        action = self.env.ref('mw_power.action_power_workorder_tree')
        obj_ids = []
        if self.eo_count:
            obj_ids = self.eo_device_ids.ids + self.eo_device_ids.ids
        vals = action.read()[0]
        vals['domain'] = [('id','in',obj_ids)]
        vals['context'] = {'search_default_gr_month': True, 'search_default_gr_start': True,'search_default_gr_day': True}
        return vals

    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        return super(power_category, self).create(vals)

    def write(self, vals):
        tools.image_resize_images(vals)
        return super(power_category, self).write(vals)

    def _compute_implements_count(self):
        for item in self:
            cnt = 0
            if item.main_type=='categ':
                cnt = len(self.env['power.implements'].search([('categ_id','=',item.id)]))
            elif item.main_type=='asset':
                cnt = len(self.env['power.implements'].search([('asset_id','=',item.id)]))
            elif item.main_type=='group':
                cnt = len(self.env['power.implements'].search([('group_id','=',item.id)]))
            item.implements_count = cnt

    def view_implements(self):
        action = self.env.ref('mw_power.action_power_implements_tree')
        obj_ids = []
        if self.main_type=='categ':
            obj_ids = self.env['power.implements'].search([('categ_id','=',self.id)]).ids
        elif self.main_type=='asset':
            obj_ids = self.env['power.implements'].search([('asset_id','=',self.id)]).ids
        elif self.main_type=='group':
            obj_ids = self.env['power.implements'].search([('group_id','=',self.id)]).ids
        vals = action.read()[0]
        vals['domain'] = [('id','in',obj_ids)]
        return vals

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive categories.'))
        return True

    @api.depends('name', 'parent_id.complete_name', 'main_type')
    def _compute_complete_name(self):
        for category in self:
            cname = ''
            if category.parent_id:
                cname = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                cname = category.name
            if category.main_type:
                cname = '%s [%s]'%(cname, dict(self._fields['main_type'].selection).get(category.main_type))
            category.complete_name = cname

    def name_get(self):
        res = []
        for item in self:
            res_name = super(power_category, item).name_get()
            if item.main_type:
                cname = '%s [%s]'%(res_name[0][1], dict(self._fields['main_type'].selection).get(item.main_type))
                res.append((item.id, cname))
            else:
                res.append(res_name[0])
        return res
    
    @api.onchange('main_type')
    def onch_main_type(self):
        res = {'domain': {'parent_id': [('main_type', '=', 'bblbl')]}}
        if self.main_type=='asset':
            res['domain']['parent_id'] = [('main_type', '=', 'categ')]
        elif self.main_type=='categ':
            res['domain']['parent_id'] = [('main_type', '=', 'group')]
        return res

    def unlink(self):
        for s in self:
            if s.implements_count>0:
                raise UserError('Тоноглолын бүртгэлд сонгогдсон байна Устгах боломжгүй')
        return super(power_category, self).unlink()

class power_selection(models.Model):
    _name = 'power.selection'
    _description = 'power selection'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char('Нэр', required=True, track_visibility='onchange')
    number = fields.Char('Дугаар', size=10, track_visibility='onchange')
    type = fields.Selection([
        ('work_secure','Ажилласан хамгаалалт'),
        ('down_type','Тасралтын Ангилал'),
        ('work_type','Ажлын ангилал'),
        ('power_level','Хүчдэлийн түвшин /В/'),
        ('technic','Экска болон тоног төхөөрөмж'),
        ('breakdown','Эвдрэл'),
        ('company_department','Байгууллага Хэлтэс'),
        ('call_type','Дуудлагын Ангилал'),
        ('daily_work_type','Өдөр тутмын Ажлын ангилал'),
        ('object','Объект'),
        ('location','Байрлал'),
        ('tavil','Тавил'),
        ],
        string='Ангилалууд', required=True, track_visibility='onchange')
    department_id = fields.Many2one('power.selection', domain="[('type','=','company_department')]", string='Хэлтэс', track_visibility='onchange')
    technic_id = fields.Many2one('technic.equipment', string='Техник', track_visibility='onchange')
    hr_department_id = fields.Many2one('hr.department', string='НR Хэлтэс', track_visibility='onchange')
    is_hats = fields.Boolean(string='Хацд Сонгогдох Эсэх', default=False)

    @api.constrains('technic_id','hr_department_id')
    def _check_technic_id(self):
        if self.search([('id','!=',self.id),('technic_id','!=',False),('technic_id','=',self.technic_id.id)]):
            raise UserError('Энэ техник сонгогдсон байна давхар сонгогдохгүй %s '%(self.technic_id.display_name))
        
        if self.search([('id','!=',self.id),('hr_department_id','!=',False),('hr_department_id','=',self.hr_department_id.id)]):
            raise UserError('Энэ хэлтэс сонгогдсон байна давхар сонгогдохгүй %s '%(self.hr_department_id.display_name))

    @api.onchange('technic_id')
    def onch_technic_id(self):
        if self.technic_id:
            self.name = self.technic_id.display_name

    @api.onchange('hr_department_id')
    def onch_hr_department_id(self):
        if self.hr_department_id:
            self.name = self.hr_department_id.display_name

    def name_get(self):
        res = []
        for item in self:
            res_name = super(power_selection, item).name_get()
            nn = ''
            if item.number:
                nn = u'['+item.number+'] '
            if item.department_id:
                nn = nn + res_name[0][1]+u' /'+item.department_id.name+'/'
                res.append((item.id, nn))
            elif nn:
                res_name = nn+res_name[0][1]
                res.append((item.id, res_name))
            else:
                res.append(res_name[0])
        return res

    # def unlink(self):
    #     for s in self:
    #         if s.implements_count>0:
    #             raise UserError('Тоноглолын бүртгэлд сонгогдсон байна Устгах боломжгүй')
    #     return super(power_selection, self).unlink()

class power_warehouse_config(models.Model):
    _name = 'power.warehouse.config'
    _description = 'power warehouse config'
    _rec_name = 'warehouse_id'
    
    warehouse_id = fields.Many2one('stock.warehouse', string='Агуулах', required=True)
    type = fields.Selection([
        ('workorder','Work order'),
        ],
        string='Төрөл', required=True)

    def send_chat(self, html, partner_ids):
        if not partner_ids:
            if self.type=='none':
                return True
            raise UserError(u'Мэдэгдэл хүргэх харилцагч байхгүй байна')
        
        channel_obj = self.env['mail.channel']
        for item in partner_ids:
            if self.env.user.partner_id.id!=item.id:
                channel_ids = channel_obj.search([
                    ('channel_partner_ids', 'in', [item.id])
                    ,('channel_partner_ids', 'in', [self.env.user.partner_id.id])
                    ]).filtered(lambda r: len(r.channel_partner_ids) == 2).ids
                if not channel_ids:
                    vals = {
                        'channel_type': 'chat', 
                        'name': u''+item.name+u', '+self.env.user.name, 
                        'public': 'private', 
                        'channel_partner_ids': [(4, item.id), (4, self.env.user.partner_id.id)], 
                        'email_send': False
                    }
                    new_channel = channel_obj.create(vals)
                    notification = _('<div class="o_mail_notification">created <a href="#" class="o_channel_redirect" data-oe-id="%s">#%s</a></div>') % (new_channel.id, new_channel.name,)
                    new_channel.message_post(body=notification, message_type="notification", subtype="mail.mt_comment")
                    channel_info = new_channel.channel_info('creation')[0]
                    self.env['bus.bus'].sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id), channel_info)

                    channel_ids = [new_channel.id]

                self.env['mail.message'].create({
                        'message_type': 'comment', 
                        'subtype_id': 1,
                        'body': html,
                        'channel_ids':  [(6, 0, channel_ids),]
                        })

class stock_warehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    power_config_ids = fields.One2many('power.warehouse.config', 'warehouse_id', string='Power Config')

class power_eo_user(models.Model):
    _name = 'power.eo.user'
    _description = 'power eo user'
    
    user_ids = fields.Many2many('res.users', string='Батлах', required=True)
    type = fields.Selection([
        ('chairman','УД'),
        ('chairman_deputy','УОД'),
        ],
        string='Төрөл', required=True)
