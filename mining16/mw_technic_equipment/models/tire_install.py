# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections

class TechnicTireInstall(models.Model):
    _name = 'technic.tire.install'
    _description = 'Technic inspection'
    _order = 'date_install desc, date_record desc'
    _inherit = 'mail.thread'

    @api.model
    def _get_user(self):
        return self.env.user.id

    branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,)

    name = fields.Char(string=u'Дугаар', readonly=True,)
    date_install = fields.Date(string=u'Хийсэн Огноо', required=True, copy=False,
        states={'open': [('readonly', True)],'remove': [('readonly', True)],'done': [('readonly', True)]})
    date_record = fields.Datetime(string=u'Үүсгэсэн огноо', readonly=True, 
        copy=False, default=datetime.now())

    user_id = fields.Many2one('res.users', string=u'Бүртгэсэн', default=_get_user, readonly=True)
    validator_id = fields.Many2one('res.users', string=u'Баталсан', readonly=True, copy=False,)

    technic_id = fields.Many2one('technic.equipment', string=u'Техник', required=True,
        domain=[('rubber_tired','=',True)],
        states={'open': [('readonly', True)],'remove': [('readonly', True)],'done': [('readonly', True)]})
    km_value = fields.Float(string='KM', digits = (16,1), required=True,
        help="Дугуйн ажил хийх үеийн километр цаг",
        states={'remove': [('readonly', True)],'done': [('readonly', True)]})
    odometer_value = fields.Float(string='Мото/ц', digits = (16,1), required=True,
        help="Дугуйн ажил хийх үеийн мото цаг",
        states={'remove': [('readonly', True)],'done': [('readonly', True)]})

    tire_install_line = fields.One2many('technic.tire.install.line', 'parent_id', string='Tire install lines',
        states={'done': [('readonly', True)]})
    tire_remove_line = fields.One2many('technic.tire.remove.line', 'parent_id', string='Tire remove lines',
        states={'remove': [('readonly', True)],'done': [('readonly', True)]})
    
    maintenance_note = fields.Text("Засварын тайлбар",
        states={'open': [('readonly', True)],'remove': [('readonly', True)],'done': [('readonly', True)]})
    shift = fields.Selection([
            ('day', u'Өдөр'),
            ('night', u'Шөнө'),], 
            string=u'Ээлж', required=True,
            states={'done': [('readonly', True)]})
    state = fields.Selection([
            ('draft', u'Draft'), 
            ('open', u'Open'),
            ('remove', u'Removed'),
            ('done', u'Done'),
            ('cancelled', u'Cancelled'),], 
            default='draft', string=u'Төлөв', tracking=True)

    # Overrided methods ================
    def unlink(self):
        for s in self:
            if s.state != 'draft':
                raise UserError(_('Ноорог байх ёстой!'))
        return super(TechnicTireInstall, self).unlink()

    # ==== CUSTOM METHODs ===============
    @api.onchange('technic_id')
    def onchange_technic_id(self):
        self.km_value = self.technic_id.total_km
        self.odometer_value = self.technic_id.total_odometer

    def action_to_draft(self):
        self.state = 'draft'
    
    def action_to_cancel(self):
        self.state = 'cancelled'
    
    def action_to_open(self):
        if not self.name:
            self.name = self.env['ir.sequence'].next_by_code('technic.tire.install')
        if not self.tire_remove_line:
            for tline in self.technic_id.tire_line:
                vals = {
                    'parent_id': self.id,
                    'tire_id': tline.tire_id.id,
                    'odometer_value': tline.tire_id.total_moto_hour if tline.tire_id.odometer_unit == 'motoh' else tline.tire_id.total_km,
                    'position': tline.position,
                    'old_line_id': tline.id,
                }
                self.env['technic.tire.remove.line'].create(vals)
        self.state = 'open'
    
    def action_to_done(self):
        if self.tire_remove_line and self.state == 'open':
            for line in self.tire_remove_line:
                if line.is_remove:
                    # Дугуйны мэдээлэл SET хийх
                    line.tire_id.current_technic_id = False
                    line.tire_id.current_position = 0
                    line.tire_id.technic_odometer = 0
                    line.tire_id.working_type = line.working_type
                    line.tire_id.with_coolant = False
                    line.tire_id.state = 'inactive'
                    # History
                    vals = {
                        'date': self.date_install,
                        'technic_id': self.technic_id.id,
                        'technic_odometer': self.odometer_value if line.tire_id.odometer_unit == 'motoh' else self.km_value,
                        'tire_id': line.tire_id.id,
                        'tire_odometer': line.tire_id.total_moto_hour,
                        'tire_km': line.tire_id.total_km,
                        'tread_percent': line.tire_id.tread_depreciation_percent,
                        'position': line.position,
                        'description': 'Салгасан',
                        'other_notes': self.name,
                    }
                    self.env['tire.used.history'].create(vals)
                    # Delete old line
                    line.old_line_id.unlink()
                self.state = 'remove'
            return True

        if not self.tire_remove_line and not self.tire_install_line:
            raise UserError(_('Угсрах дугуйн мэдээллийг оруулна уу!'))

        if self.tire_install_line:
            if self.technic_id.technic_setting_id.tire_counts < len(self.technic_id.tire_line) + len(self.tire_install_line):
                raise UserError(_('Техникийн нийт дугуйны тоо тохиргооноос их болох гэж байна! (%d)' % self.technic_id.technic_setting_id.tire_counts))

            for line in self.tire_install_line:
                if line.position <= 0:
                    raise UserError(_('%s угсрах байрлал буруу байна!' % line.tire_id.display_name))
                # Одоо байгаа байрлал дээр суурьлуулах гэж байна уу шалгах
                for ll in self.tire_remove_line:
                    if not ll.is_remove and ll.position == line.position:
                        raise UserError(_('%d - байрлал дээр дугуй байна!' % ll.position))
                desc = ''
                # Дугуйн шинэ хуучныг заах төлөв SET хийх
                if line.install_type == 'new':
                    line.tire_id.new_or_old = 'new_tire_set'
                    desc = ', Шинэ дугуй суурьлуулсан'
                else:
                    line.tire_id.new_or_old = 'old_tire_set'
                    desc = ', Хуучин дугуй шилжүүлж суурьлуулсан'
                # History
                vals = {
                    'date': self.date_install,
                    'technic_id': self.technic_id.id,
                    'technic_odometer': self.odometer_value if line.tire_id.odometer_unit == 'motoh' else self.km_value,
                    'tire_id': line.tire_id.id,
                    'tire_odometer': line.tire_id.total_moto_hour,
                    'tire_km': line.tire_id.total_km,
                    'tread_percent': line.tire_id.tread_depreciation_percent,
                    'position': line.position,
                    'description': 'Суурьлуулсан'+desc,
                    'other_notes': self.name,
                }
                self.env['tire.used.history'].create(vals)
                # Technic tire line
                vals = {
                    'date': self.date_install,
                    'technic_id': self.technic_id.id,
                    'technic_odometer': self.odometer_value if line.tire_id.odometer_unit == 'motoh' else self.km_value,
                    'tire_id': line.tire_id.id,
                    'brand': line.tire_id.brand_id.id, 
                    'serial': line.tire_id.serial_number,
                    'odometer_value': line.tire_id.total_moto_hour,
                    'odometer_km': line.tire_id.total_km,
                    'set_tread_depreciation': line.tire_id.tread_depreciation_percent,
                    'position': line.position,
                    'state': 'set',
                }
                self.env['technic.tire.line'].create(vals)
                # Дугуйны мэдээлэл SET хийх
                line.tire_id.current_technic_id = self.technic_id.id
                line.tire_id.current_position = line.position
                line.tire_id.technic_odometer = self.odometer_value
                line.tire_id.with_coolant = line.with_coolant
                line.tire_id.state = 'using'
        self.state = 'done'
        self.validator_id = self.env.user.id
        
class TechnicTireInstallLine(models.Model):
    _name = "technic.tire.install.line"
    _description = "Technic Install Line"

    parent_id = fields.Many2one('technic.tire.install',string='Parent', ondelete='cascade')
    tire_id = fields.Many2one('technic.tire',string='Дугуй/сериал', required=True,
        domain=[('state','in',['new','inactive']),
            ('working_type','in',['normal','use_again'])])
    odometer_unit = fields.Selection(related='tire_id.odometer_unit', string='Гүйлтийн нэгж', 
        readonly=True, store=True)
    odometer_value = fields.Float(related="tire_id.total_moto_hour", string='Гүйлт', digits = (16,1), readonly=True,)
    position = fields.Integer('Байрлал', required=True)
    with_coolant = fields.Boolean('Coolant-тай эсэх?', default=False)
    install_type = fields.Selection([
        ('new','Шинэ'),
        ('old','Хуучин')], string=u'Нэмэх үйлдэл', required=True,)

class TechnicTireRemoveLine(models.Model):
    _name = "technic.tire.remove.line"
    _description = "Technic Remove Line"

    parent_id = fields.Many2one('technic.tire.install',string='Parent', ondelete='cascade')
    tire_id = fields.Many2one('technic.tire',string='Дугуй/сериал', readonly=True, )
    odometer_unit = fields.Selection(related='tire_id.odometer_unit', string='Гүйлтийн нэгж', 
        readonly=True, store=True)
    odometer_value = fields.Float(string='Гүйлт', digits = (16,1), readonly=True,)
    position = fields.Integer('Байрлал', readonly=True, )
    is_remove = fields.Boolean('Салгах эсэх?', default=False)
    working_type = fields.Selection([
        ('normal',u'Хэвийн'),
        ('use_again',u'Дахин ашиглах'),
        ('available_repair',u'Засагдах боломжтой'),
        ('rear_used','Арын тэнхлэгт шилжүүлсэн'),
        ('burny','Халсан'),
        ('exploded','Буудсан'),
        ('shapeless','Хэлбэр алдсан'),
        ('dont_use',u'Ашиглах боломжгүй')], string=u'Ажиллагаа', )
    old_line_id = fields.Many2one('technic.tire.line',string='Old line id')
    