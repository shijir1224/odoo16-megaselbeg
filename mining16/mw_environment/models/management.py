# -*- coding: utf-8 -*-
from odoo import models, fields,api
from datetime import datetime
from odoo.addons.base.models.res_partner import ADDRESS_FIELDS
from collections import defaultdict

# Subset of partner fields: sync all or none to avoid mixed addresses
PARTNER_ADDRESS_FIELDS_TO_SYNC = [
    'street',
    'street2',
    'city',
    'zip',
    'state_id',
    'country_id',
]   
class mw_environment_mining_line(models.Model):
    _name = 'env.mining.line'
    _description = "Environmental Monitor Locations"
    _order = 'monitor_category ASC, code ASC'

    @api.model
    def _get_default_address_format(self):
        return "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"

    def _display_address_depends(self):
        # field dependencies of method _display_address()
        return self._formatting_address_fields() + [
            'country_id',
            'state_id',
        ]

    mining_id = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', ondelete=False)
    name = fields.Char('Нэр', required=True)
    code = fields.Char('Код', required=True)
    monitor_category = fields.Selection([
        ('monitor3', 'Агаар'),
        ('monitor1', 'Ус'),
        ('monitor2', 'Хөрс'),
        ('monitor4', 'Амьтан'),
        ('monitor5', 'Ургамал'),
        ('monitor7', 'Дуу чимээ')], string='Хяналт шинжилгээний төрөл', required=True)
    partner_id = fields.Many2one('res.partner', string='Харилцагч')
    latitude = fields.Float(string='Өргөрөг', digits=(9, 6), readonly=False)
    longitude = fields.Float(string='Уртраг', digits=(9, 6), readonly=False)
    marker_color = fields.Integer(string='Marker color')
    height = fields.Integer('Өндөр /д.т.д/')
    surface = fields.Char('Газрын гадарга')
    bad_monitor = fields.Boolean('Bad monitor exist', default=False)
    is_active = fields.Selection([
        ('active', 'Идэвхтэй'),
        ('inactive', 'Идэвхгүй')], string='Идэвхтэй эсэх', default='active', required=True)

    def name_get(self):
        result = []
        for point in self:
            # result.append((point.id, point.code + ' (' + point.name + ')'))
            result.append((point.id, point.code))
        return result

    @api.model
    def _get_address_format(self):
        return (self.country_id.address_format or self._get_default_address_format())

    @api.depends('partner_id')
    def _compute_customer_geo(self):
        for lead in self:
            if lead.partner_id:
                lead.latitude = lead.partner_id.partner_latitude
                lead.longitude = lead.partner_id.partner_longitude
            else:
                lead.latitude = 0.0
                lead.longitude = 0.0

    @api.model
    def _address_fields(self):
        return list(ADDRESS_FIELDS)

    @api.model
    def _formatting_address_fields(self):
        return self._address_fields()

    def update_address(self, vals):
        addr_vals = {
            key: vals[key] for key in self._address_fields() if key in vals
        }
        if addr_vals:
            return super(mw_environment_mining, self).write(addr_vals)

    def _display_address(self, without_company=False):
        address_format, args = self._prepare_display_address(without_company)
        return address_format % args


    def _prepare_address_values_from_partner(self, partner):
        if any(partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC):
            values = {f: partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
        else:
            values = {f: self[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
        return values
    
    @api.model
    def _geo_localize(self, street='', zip='', city='', state='', country=''):
        geo_obj = self.env['base.geocoder']
        search = geo_obj.geo_query_address(
            street=street,
            zip=zip,
            city=city,
            state=state,
            country=country,
        )
        result = geo_obj.geo_find(search, force_country=country)
        if result is None:
            search = geo_obj.geo_query_address(
                city=city, state=state, country=country
            )
            result = geo_obj.geo_find(search, force_country=country)
        return result

    def geo_localize(self):
        for lead in self.with_context(lang='en_US'):
            result = self._geo_localize(
                lead.street,
                lead.zip,
                lead.city,
                '',
                '',
            )

            if result:
                lead.write(
                    {
                        'latitude': result[0],
                        'longitude': result[1],
                    }
                )
        return True

class mw_environment_mining(models.Model):
    _name = 'env.mining'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Environmental Үйлдвэр, Уурхай"
    _order = 'department_id ASC'
    

    @api.model
    def _get_default_address_format(self):
        return "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"

    def _display_address_depends(self):
        # field dependencies of method _display_address()
        return self._formatting_address_fields() + [
            'country_id',
            'state_id',
        ]

    name = fields.Char('Нэр', required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    partner_id = fields.Many2one('res.partner', string='Харилцагч')
    is_active = fields.Selection([
        ('active', 'Идэвхтэй'),
        ('inactive', 'Идэвхгүй')], string='Идэвхтэй эсэх', default='active', required=True)
    line_ids = fields.One2many('env.mining.line', 'mining_id', string='Monitor Location')
    type = fields.Selection([
        ('mining', 'Уурхай'),
        ('project', 'Төсөл')], string='Төрөл', default='mining', required=True)
    company_id = fields.Many2one('res.company', string='Компани', required=True)
    branch_id = fields.Many2one('res.branch', string='Салбар', required=True)


    @api.model
    def _get_address_format(self):
        return (
            self.country_id.address_format
            or self._get_default_address_format()
        )

    @api.depends('partner_id')
    def _compute_customer_geo(self):
        for lead in self:
            if lead.partner_id:
                lead.customer_latitude = lead.partner_id.partner_latitude
                lead.customer_longitude = lead.partner_id.partner_longitude
            else:
                lead.customer_latitude = 0.0
                lead.customer_longitude = 0.0

    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return list(ADDRESS_FIELDS)

    @api.model
    def _formatting_address_fields(self):
        """Returns the list of address fields usable to format addresses."""
        return self._address_fields()

    def update_address(self, vals):
        addr_vals = {
            key: vals[key] for key in self._address_fields() if key in vals
        }
        if addr_vals:
            return super(mw_environment_mining, self).write(addr_vals)

    def _get_country_name(self):
        return self.country_id.name or ''

    def _prepare_display_address(self, without_company=False):
        # get the information that will be injected into the display format
        # get the address format
        address_format = self._get_address_format()
        args = defaultdict(
            str,
            {
                'state_code': self.state_id.code or '',
                'state_name': self.state_id.name or '',
                'country_code': self.country_id.code or '',
                'country_name': self._get_country_name(),
            },
        )
        for field in self._formatting_address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''

        return address_format, args

    def _display_address(self, without_company=False):
        '''copied from res.partner'''
        address_format, args = self._prepare_display_address(without_company)
        return address_format % args

    @api.depends(lambda self: self._display_address_depends())
    def _compute_customer_address(self):
        for lead in self:
            lead.customer_address = lead._display_address()

    customer_latitude = fields.Float(
        string='Customer latitude',
        digits=(6, 5),
        compute='_compute_customer_geo',
        readonly=False,
        store=True,
    )
    customer_longitude = fields.Float(
        string='Customer longitude',
        digits=(6, 5),
        compute='_compute_customer_geo',
        readonly=False,
        store=True,
    )
    customer_address = fields.Char(
        compute='_compute_customer_address', string='Complete Address'
    )
    marker_color = fields.Integer(string='Marker color')
    state_id = fields.Many2one(
        "res.country.state", string='State',
        compute='_compute_partner_address_values', readonly=False, store=True,
        domain="[('country_id', '=?', country_id)]")
    
    country_id = fields.Many2one(
        'res.country', string='Country',
        compute='_compute_partner_address_values', readonly=False, store=True)

    def _prepare_address_values_from_partner(self, partner):
        # Sync all address fields from partner, or none, to avoid mixing them.
        if any(partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC):
            values = {f: partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
        else:
            values = {f: self[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
        return values
    
    @api.model
    def _geo_localize(self, street='', zip='', city='', state='', country=''):
        geo_obj = self.env['base.geocoder']
        search = geo_obj.geo_query_address(
            street=street,
            zip=zip,
            city=city,
            state=state,
            country=country,
        )
        result = geo_obj.geo_find(search, force_country=country)
        if result is None:
            search = geo_obj.geo_query_address(
                city=city, state=state, country=country
            )
            result = geo_obj.geo_find(search, force_country=country)
        return result

    def geo_localize(self):
        for lead in self.with_context(lang='en_US'):
            result = self._geo_localize(
                lead.street,
                lead.zip,
                lead.city,
                '',
                '',
            )

            if result:
                lead.write(
                    {
                        'customer_latitude': result[0],
                        'customer_longitude': result[1],
                    }
                )
        return True

    @api.depends('partner_id')
    def _compute_partner_address_values(self):
        for lead in self:
            lead.update(lead._prepare_address_values_from_partner(lead.partner_id))

    street = fields.Char('Street', compute='_compute_partner_address_values', readonly=False, store=True)
    street2 = fields.Char('Street2', compute='_compute_partner_address_values', readonly=False, store=True)
    zip = fields.Char('Zip', change_default=True, compute='_compute_partner_address_values', readonly=False, store=True)
    city = fields.Char('City', compute='_compute_partner_address_values', readonly=False, store=True)


class mw_environment_parameter(models.Model):
    _name = 'env.parameter'
    _description = "Environmental Parameters"
    _order = 'type ASC, category ASC, name ASC'

    name = fields.Char('Нэр', required=True)
    type = fields.Selection([
        ('training', 'Сургалтын сэдэв'),
        ('violation', 'Зөрчил дутагдал'),
        ('location', 'Зөрчлийн байршил'),
        ('dedication', 'Усны зориулалт'),
        ('source', 'Усны эх үүсвэр'),
        ('waste_type', 'Хог хаягдлын төрөл'),
        ('rehab_type', 'Нөхөн сэргээлтийн төрөл'),
        ('rehab_location', 'Нөхөн сэргээлтийн байршил'),
        ('animal', 'Ан амьтан'),
        ('animal_location', 'Амьтны байршил'),
        ('monitor_type', 'Орчны хяналт шинжилгээ'),
        ('expense_type', 'Бараа материал, Үйлчилгээний төрөл'),
        ('garden_activity', 'Ногоон байгууламжийн арчилгаа'),
        ('tree', 'Мод бутны нэр')], string='Төрөл', default='animal', required=True)

    category = fields.Selection([
        ('waste1', 'Ахуйн'),
        ('waste2', 'Дахин боловсруулах'),
        ('waste3', 'Аюултай'),
        ('waste4', 'Дахин ашиглах'),
        ('waste5', 'Дахин ашиглах боломжгүй'),
        ('rehab1', 'Биологийн нөхөн сэргээлт'),
        ('rehab2', 'Техникийн нөхөн сэргээлт'),
        ('monitor1', 'Ус'),
        ('monitor2', 'Хөрс'),
        ('monitor3', 'Агаар'),
        ('monitor4', 'Амьтан'),
        ('monitor5', 'Ургамал'),
        ('monitor7', 'Дуу чимээ'),
        ('expense1', 'Хуулийн нийцлийг хангах'),
        ('expense2', 'Ногоон байгууламж'),
        ('expense3', 'Нөхөн сэргээлт'),
        ('expense4', 'Бусад ажлууд'),
        ('expense5', 'Сургалт, сурталчилгаа'),
        ('expense6', 'Томилолт'),
        ('expense7', 'Үйл ажиллагаа сайжруулах'),
        ('expense8', 'Бохир соруулсан төлбөр'),
        ('expense9', 'Тоолуур баталгаажуулсан төлбөр'),
        ('expense10', 'Тоолуур суурилуулсан төлбөр'),
        ('expense11', 'Багаж, тоног төхөөрөмж засуулсан'),
        ('expense12', 'Орон нутагттай хамтран ажиллах гэрээний төлбөр'),
        ('expense13', 'Ажлын багаж хэрэгсэл худалдан авах'),
        ('expense14', 'Усалгааны шугам хоолой худалдан авах'),
        ('expense15', 'Хашаа худалдан авах'),
        ('expense16', 'Хэмжилтийн багаж хэрэгслүүд худалдан авах'),
        ('animal1', 'Хөхтөн'),
        ('animal2', 'Шувуу'),
        ('animal3', 'Мөлхөгчид'),
        ('animal4', 'Шавьж'),
        ('garden1', 'га'),
        ('garden2', 'метр3'),
        ('garden3', 'ширхэг'),
        ('garden4', 'метр2')], default='waste1', string='Ангилал')
    is_active = fields.Selection([
        ('active', 'Идэвхтэй'),
        ('inactive', 'Идэвхгүй')], string='Идэвхтэй эсэх', default='active', required=True)
    price = fields.Integer(string='Нэгж үнэ')
    image = fields.Image(string='Зураг')


class mw_environment_standard(models.Model):
    _name = 'env.standard'
    _description = "Environmental Standard"
    _order = 'name ASC'

    name = fields.Char('Нэр', required=True)
    category = fields.Selection([
        ('monitor1', 'Ундны ус'),
        ('monitor6', 'Бохир ус'),
        ('monitor3', 'Агаар'),
        ('monitor2', 'Хөрс'),
        ('monitor4', 'Амьтан'),
        ('monitor5', 'Ургамал'),
        ('monitor7', 'Дуу чимээ')], string='Ангилал', required=True)

    uom = fields.Char('Хэмжих нэгж', required=True)
    normal_start = fields.Float('Эхлэх хязгаар', required=True)
    normal_end = fields.Float('Дуусах хязгаар', required=True)
    is_active = fields.Selection([
        ('active', 'Идэвхтэй'),
        ('inactive', 'Идэвхгүй')], string='Идэвхтэй эсэх', default='active', required=True)