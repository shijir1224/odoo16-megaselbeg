# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import requests
from odoo.exceptions import UserError, ValidationError
import logging
from io import BytesIO
from tempfile import NamedTemporaryFile
import base64
import xlrd
import xlsxwriter
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar

_logger = logging.getLogger(__name__)


class crm_stage(models.Model):
    _inherit = 'crm.stage'

    anhaar_honog = fields.Integer('Анхааруулах хоног')
    state_type = fields.Selection([('draft','Draft'),('prosfect','Prospect'),('won','Won'),('loss','Loss')], string='Статик төрөл')

class crm_team(models.Model):
    _inherit = 'crm.team'

    company_type = fields.Selection([('company','Компани'),('person','Хүвь хүн')], string='Харилцагчийн төрөл', tracking=True)

class crm_lead(models.Model):
    _inherit = 'crm.lead'

    def _default_company_type(self, user_id):
        first_team = self.env['crm.team']._get_default_team_id(user_id=user_id, domain=[])
        if first_team:
            return first_team.company_type
        return False
                            
    activity_type1_id = fields.Many2one('mw.crm.activity.type', 'Ү.А чиглэл / Ажил эрхлэлт', tracking=True)
    activity_type = fields.Char(related='activity_type1_id.activity_type', string='Ү.А дэд төрөл', readonly=True)
    owner_type = fields.Selection([
        ('llc','ХХК'),
        ('lc','ХК'),
        ('turiin','Төрийн байгууллага'),
        ('turiin_bus','Төрийн бус байгууллага'),
        ('gadaad','Гадаадын хөрөнгө оруулалт'),
        ('other','Бусад')], 'Өмчлөлийн хэлбэр', tracking=True)
    probability = fields.Float('Probability', group_operator="avg", copy=False, tracking=True)
    company_type = fields.Selection([('company','Компани'),('person','Хүвь хүн')], string='Харилцагчийн төрөл',  tracking=True, default=lambda self: self._default_company_type(self.env.uid))
    mw_campaign_id = fields.Many2one('mw.campaign', 'Аян', tracking=True, domain=[('state','in',['draft','planned'])])
    vat = fields.Char('Регистр', tracking=True)
    state_type = fields.Selection(related='stage_id.state_type', readonly=True)
    birthday = fields.Date(string='Төрсөн байгуулагдсан', tracking=True, store=True, compute='_compute_gender_birth')
    gender = fields.Selection([('male','Эр'),('female','Эм')], string='Хүйс', tracking=True, store=True, compute='_compute_gender_birth')
    sale_share_ids = fields.One2many('crm.lead.sale.share', 'lead_id', string='Хуваах борлуулагчид')
    sale_type = fields.Selection([
        ('old', 'Сунгалтын гэрээ'), 
        ('new1', 'Шинэ гэрээ'), 
        ('old+', 'Нэмэлт гэрээ')
    ], default='old', string="Борлуулалтын төрөл")
    call_count = fields.Integer('# Утасдсан тоо', compute='_compute_activity_count', store=True)
    mail_count = fields.Integer('# Имэйл тоо', compute='_compute_activity_count', store=True)
    # meeting_count = fields.Integer('# Meetings', compute='_compute_meeting_count', store=True)
    res_partner_ranking_id = fields.Many2one('res.partner.rank',string="Харилцагчийн зэрэглэл", compute="compute_rank", readonly=True, store=True)
    history_ids = fields.One2many('crm.stage.history', 'lead_id', string='Төлөвийн түүх', readonly=True)
    current_spend_day = fields.Float(string='Зарцуулсан хоног', compute='compute_current_spend_day', 
    readonly=True, digits=(16,0))
    current_spend_day_str = fields.Char(string='Зарцуулсан хоног str', compute='compute_current_spend_day', 
    readonly=True)
    anhaar_honog = fields.Integer(related='stage_id.anhaar_honog', readonly=True)
    
    
    @api.depends('history_ids','stage_id')
    def compute_current_spend_day(self):
        for item in self:
            cur_day = item.history_ids.filtered(lambda r: r.stage_id==item.stage_id)
            item.current_spend_day = cur_day[0].spend_day if cur_day else 0
            item.current_spend_day_str = '%sс'%(int(item.current_spend_day/30)) if item.current_spend_day>30 else '%sх'%(int(item.current_spend_day))

    def write(self, vals):
        res = super(crm_lead, self).write(vals)
        if 'stage_id' in vals:
            self.env['crm.stage.history'].create_history(vals['stage_id'], self)
        return res
    
    @api.model
    def create(self, vals):
        res = super(crm_lead, self).create(vals)
        if 'stage_id' in vals:
            self.env['crm.stage.history'].create_history(vals['stage_id'], res)
        return res

    @api.onchange('partner_id')
    def compute_rank(self):
        for item in self:
            item.res_partner_ranking_id = item.partner_id.rank_partner_id.id if item.partner_id.rank_partner_id else False

    def get_partner_vatpayer(self, number):
        '''
            ebarimt сайтруу хандаж нөат төлөгч эсэхийг шалгагч
        '''
        url="http://info.ebarimt.mn/rest/merchant/info?regno="+str(number)+""
        vat=''
        try:
            r = requests.get(url)
            n = r.json()
            vat = n['name']
        except Exception:
            r=' '
            vat=False
            return ''
        return vat
    
    @api.onchange('vat')
    def onchange_vat_set(self):
        for item in self:
            if item.vat and not item.name:
                name = self.get_partner_vatpayer(item.vat)
                item.name=name

    def view_call_count(self):
        return True
    
    def view_mail_count(self):
        return True

    @api.depends('message_ids','activity_ids')
    def _compute_activity_count(self):
        for item in self:
            item.call_count = len(item.message_ids.filtered(lambda r: r.mail_activity_type_id.act_type=='call'))+len(item.activity_ids.filtered(lambda r: r.activity_type_id.act_type=='call'))
            item.mail_count = len(item.message_ids.filtered(lambda r: r.mail_activity_type_id.act_type=='mail'))+len(item.activity_ids.filtered(lambda r: r.activity_type_id.act_type=='mail'))
            
    @api.model
    def default_get(self, fields_list):
       res = super(crm_lead, self).default_get(fields_list)
       vals = [(0, 0, {'user_id': self.env.user.id, 'percent': 100})]
       res.update({'sale_share_ids': vals})
       return res

    @api.constrains("sale_share_ids")
    def check_sale_share_ids(self):
        for item in self:
            if item.sale_share_ids and sum(item.sale_share_ids.mapped('percent'))!=100:
                raise UserError(u'Хуваах борлуулагчидийн 100% хүрэхгүй байна!!')

    @api.depends('vat', 'company_type')
    def _compute_gender_birth(self):
        for item in self:
            vat_gender = False
            vat_birthday = None
            if item.vat and item.company_type=='person':
                if len(item.vat)>=9:
                    try:
                        lan2 = item.vat[len(item.vat)-2]
                        if (int(lan2) % 2) == 0:
                            vat_gender = 'female'
                        else:
                            vat_gender = 'male'
                    except Exception as e:
                        _logger.info('gender aldaa %s'%(e))
                        pass
                    try:
                        vat_birthday = self.env['res.partner'].get_birthday(item.vat)
                    except Exception as e:
                        _logger.info('birthday aldaa %s'%(e))
                        pass

            item.gender = vat_gender
            item.birthday = vat_birthday

    @api.onchange('stage_id')
    def onch_stage(self):
        if self.stage_id.state_type=='prospect':
            self.set_prospect()
            # self.stage_id.state_type =

    def set_prospect(self):
        print ("('contact_name', 'ilike', self")

    def _onchange_partner_id_values(self, partner_id):
        res = super(crm_lead, self)._onchange_partner_id_values(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            res['vat'] = partner.vat
            res['company_type'] = partner.company_type
            res['activity_type1_id'] = partner.activity_type1_id.id
            res['owner_type'] = partner.owner_type
        return res

    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        res = super(crm_lead, self)._create_lead_partner_data(name, is_company, parent_id)
        res['vat'] = self.vat
        res['company_type'] = self.company_type
        res['activity_type1_id'] = self.activity_type1_id.id
        res['owner_type'] = self.owner_type
        return res

    def create_res_partner_hand(self):
        created_partner = self._create_lead_partner()
        if created_partner:
            self.partner_id = created_partner.id
        
    def action_set_lost(self, **additional_values):
        res = super(crm_lead, self).action_set_lost(**additional_values)
        for item in self:
            stage_id = item._stage_find(domain=[('state_type', '=', 'loss')])
            item.stage_id = stage_id.id
        return res
    
class crm_lead_sale_share(models.Model):
    _name = 'crm.lead.sale.share'
    _description = 'Борлуулалтын үнийн хуваалт'

    lead_id = fields.Many2one('crm.lead', 'Lead', ondelete='cascade')
    user_id = fields.Many2one('res.users', 'Борлуулалтын ажилтан', required=True)
    percent = fields.Float('Хувь')

class crm_lead_to_opper_field(models.Model):
    _name = 'crm.lead.to.opper.field'
    _description = 'CRM lead to opper zaaval bugluh talbar'

    field_id = fields.Many2one('ir.model.fields', string='Талбарын нэр', domain=[('model_id.model','=','crm.lead'),('store','=',True)])

class Lead2OpportunityPartner(models.TransientModel):

    _inherit = 'crm.lead2opportunity.partner'
    
    def _convert_opportunity(self, vals):
        self.ensure_one()
        res = super(Lead2OpportunityPartner, self)._convert_opportunity(vals)
        crm_id = self
        obj = self.env['crm.lead.to.opper.field']
        f_ids = obj.search([]).mapped('field_id.name')
        leads = self.env['crm.lead'].browse(vals.get('lead_ids'))
        buglugduugui_ids = []
        for lead in leads:
            lead_name = lead.read(f_ids)[0]
            for item in f_ids:
                if not lead_name[item]:
                    buglugduugui_ids.append(
                        """LEAD NAME %s %s"""%(lead.display_name, obj.search([('field_id.name','=',item)], limit=1).field_id.display_name))
        if buglugduugui_ids:
            raise UserError('Заавал бөглөх талбарууд %s '%(', '.join(buglugduugui_ids)))
        return res
    
    def get_field_value(self, f_id, f_value):
        model_name = 'crm.lead'
        
        if f_id.ttype=='date':
            if type(f_value) in [float, int]:
                f_value = (f_value - 25569) * 86400.0
                date_time = datetime.utcfromtimestamp(f_value)
                return str(date_time)
            else:
                return f_value
        elif f_id.ttype=='many2one':
            obj = self.env[f_id.relation]
            if type(f_value) in [float, int]:
                f_value = str(int(f_value))
            value_ids = obj.sudo()._name_search(f_value, operator='=',limit=100)
            if len(value_ids)>1:
                raise UserError('%s Талбарын утга %s 1-ээс олон ирээд байна'%(f_id.display_name, f_value))
            if value_ids:
                return value_ids[0][0]
            elif f_id.relation == 'res.partner':
                # hariltsagch davhar haiv
                value_ids = obj.sudo().search([('vat','=',f_value)], limit=1)
                if not value_ids:
                    print('value_ids',value_ids)
                    raise UserError('%s талбарын %s регистр-тэй Харицлагч олдсонгүй'%(f_value,f_id.display_name))
                return value_ids.id
            else:
                return False
        elif f_id.ttype in ['char','text'] and type(f_value) in [float, int]:
            f_value = str(int(f_value))
            return f_value
        elif f_id.ttype == 'selection':
            if not f_id.selection_ids:
                raise UserError('%s Selection утга оруулаагүй байна',f_id.display_name)
            found_it = False
            if type(f_value) in [float, int]:
                f_value = str(int(f_value))
            for sel in f_id.selection_ids:
                if sel.value==f_value or sel.name==f_value:
                    found_it = sel.value
                    break
            if not found_it and f_value:
                raise UserError('%s ТАЛБАРЫН %s Selection field-ийн утга буруу байна олдсонгүй %s'%(f_id.display_name, f_value,', '.join(f_id.selection_ids.mapped('name'))))
            return found_it
        else:
            return f_value

    class crm_sales_plan(models.Model):
        _name = 'crm.sales.plan'

        user_id = fields.Many2one('res.users', string="Төлөвлөгөө өгөх ажилтан", required=True)
        planned_sales = fields.Integer(string="Борлуулалтын төлөвлөгөө", required=True, compute="compute_qty")
        year = fields.Integer(string="Жил", required=True)
        crm_sales_plan_line_id = fields.One2many("crm.sales.plan.line","sales_plan_id", string="Борлуулалтын төлөвлөгөөний мөрүүд", copy=True)
        excel_data = fields.Binary(string='Excel file', )
        state = fields.Selection([("open", "Ноорог"), ("done", "Баталсан")], string="Төлөв", default="open",)

        @api.depends('crm_sales_plan_line_id.sale_qty')
        def compute_qty(self):
            for item in self:
                ll = 0
                for ss in item.crm_sales_plan_line_id:
                    ll+= ss.sale_qty
                item.planned_sales = ll

        def import_from_excel(self):
            fileobj = NamedTemporaryFile('w+b')
            fileobj.write(base64.decodebytes(self.excel_data))
            fileobj.seek(0)
            book = xlrd.open_workbook(fileobj.name)
            try :
                 sheet = book.sheet_by_index(0)
            except:
                 raise UserError(u'Warning', u'Wrong Sheet number.')
            # ДАТА унших
            temp_datas = {}
            nrows = sheet.nrows
            ncols = sheet.ncols
            s_obj = self.env['crm.stage']
            for r in range(2, nrows):
                row = sheet.row(r)
                stage = row[0].value
                months = row[1].value
                sale_qty = row[2].value if row[2].value else 0
                ss_id = s_obj.search([('name','=',stage)], limit=1)
                if not ss_id:
                    raise UserError(u'Үе шатын нэр алдаатай байна.')
                vals = {
                    'sales_plan_id' : self.id,
                    'stage_id' : ss_id.id,
                    'month': str(int(months)),
                    'sale_qty': sale_qty,
                    }
                self.env['crm.sales.plan.line'].create(vals)

        def export_template(self):
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            file_name = 'CRM төлөвлөгөө темплати.xlsx'       
            h1 = workbook.add_format({'bold': 1})
            h1.set_font_size(12)     
            header = workbook.add_format({'bold': 1})
            header.set_font_size(9)
            header.set_align('center')
            header.set_align('vcenter')
            header.set_border(style=1)
            header.set_bg_color('#6495ED')       
            header_wrap = workbook.add_format({'bold': 1})
            header_wrap.set_text_wrap()
            header_wrap.set_font_size(9)
            header_wrap.set_align('center')
            header_wrap.set_align('vcenter')
            header_wrap.set_border(style=1)
            header_wrap.set_bg_color('#6495ED')      
            contest_center = workbook.add_format()
            contest_center.set_text_wrap()
            contest_center.set_font_size(9)
            contest_center.set_align('center')
            contest_center.set_align('vcenter')
            contest_center.set_border(style=1)       
            # Борлуулагчаар харуулах sheet
            worksheet = workbook.add_worksheet(u'Төлөвлөгөө')
            worksheet.write(0,0, u"Борлуулалтын төлөвлөгөө импортлох загвар", h1)
            # TABLE HEADER
            row = 1
            worksheet.set_row(row, 20)
            worksheet.write(row, 0, u"Үе шатын нэр", header)
            worksheet.set_column('A:A', 18)
            worksheet.write(row, 1, u"Сар", header_wrap)
            worksheet.set_column('B:B', 18)
            worksheet.write(row, 2, u"Тоо, хэмжээ", header_wrap)
            worksheet.set_column('C:C', 18)
            row += 1
            print("$$$$$$$$$$$$$$$$$$$", row)
            for item in self.crm_sales_plan_line_id:
                worksheet.write(row, 0, item.stage_id.name or '', contest_center)
                worksheet.write(row, 1, item.month or '', contest_center)
                worksheet.write(row, 2, item.sale_qty or '', contest_center)
                row += 1
            workbook.close()
            out = base64.encodebytes(output.getvalue())
            excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
            return {
                    'type' : 'ir.actions.act_url',
                    'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
                    'target': 'new',}


                

    class crm_sales_plan_line(models.Model):
        _name = 'crm.sales.plan.line'

        stage_id = fields.Many2one('crm.stage', string="Үе шат")
        sale_qty = fields.Integer('Тоо хэмжээ', required=True)
        sales_plan_id = fields.Many2one("crm.sales.plan", string="Төлөвлөгөө", ondelete='cascade')
        daily_qtys = fields.Char("1 өдрийн төлөвлөгөө", compute="compute_daily_qtys", store=True)
        plan_start_date = fields.Date("Эхлэх огноо", compute="compute_daily_qtys", store=True)
        plan_end_date = fields.Date("Дуусах огноо", compute="compute_daily_qtys", store=True)

        month = fields.Selection([
			('1', u'1-сар'),
			('2', u'2-сар'),
			('3', u'3-сар'),
			('4', u'4-сар'),
			('5', u'5-сар'),
			('6', u'6-сар'),
			('7', u'7-сар'),
			('8', u'8-сар'),
			('9', u'9-сар'),
			('10', u'10-сар'),
			('11', u'11-сар'),
			('12', u'12-сар'),], 
		string=u'Сар', copy=True)

        @api.onchange('sale_qty','month')
        def compute_daily_qtys(self):
            for item in self:
                if item.sales_plan_id.year !=0:
                    if item.month:
                        print('item.sales_plan_id.year',item.sales_plan_id.year,'    ',item.month)   
                        st_date = str(item.sales_plan_id.year)+'-'+str(item.month)+'-01'
                        st_date = datetime.strptime(st_date,'%Y-%m-%d')
                        item.plan_start_date = st_date
                        print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^', item.sales_plan_id.year, item.month )
                        count_days = calendar.monthrange(item.sales_plan_id.year, int(item.month))[1]
                        item.daily_qtys = item.sale_qty/count_days
                        plan_end_date = st_date + timedelta(days=(count_days)-1)
                        print('$$$$$$$$$$$$$$$$$$$$$',plan_end_date)
                        item.plan_end_date = plan_end_date
                        print('$$$$$$$$$$$$$', item.daily_qtys, count_days,item.plan_start_date,  item.plan_end_date)
                    else:
                        item.plan_start_date = fields.Date.today()
                        item.daily_qtys = 0
                        item.plan_end_date = fields.Date.today()
                else:
                    item.plan_start_date = fields.Date.today()
                    item.daily_qtys = 0
                    item.plan_end_date = fields.Date.today()






    class crm_sales_plan_wizard(models.TransientModel):
        _name = "crm.sales.plan.wizard"
        _description = "CRM sales plan wizard"

        date_start = fields.Date(string=u'Эхлэх огноо', compute="compute_date", readonly=False)
        date_end = fields.Date(string=u'Дуусах огноо', default=fields.Date.context_today)
        by_department = fields.Many2many('hr.department',string="Хэлтэс")
        by_teams = fields.Many2many('crm.team',string="Борлуулалтын баг")
        by_employee = fields.Many2many('res.users',string="Ажилтан")
        

        report_interval = fields.Selection([
			('week','7 хоног'),
			('month','Сар'),
			('season','Улирал'),
			('year','Жил')], 
		string=u'Хугацаа', copy=True)
        
        @api.onchange('report_interval')
        def compute_date(self):
            for item in self:
                if item.report_interval == 'week':
                    item.date_start = item.date_end - timedelta(days=6)
                elif item.report_interval == 'month':
                    item.date_start = item.date_end - relativedelta(months=+1)
                elif item.report_interval == 'season':
                    item.date_start = item.date_end - relativedelta(months=+3)
                elif item.report_interval == 'year':
                    item.date_start = item.date_end - relativedelta(years=+1)

        def download_excel(self):
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            file_name = 'Борлуулалтын тайлан.xlsx'
            # Толгой 
            header = workbook.add_format({'bold': 1})
            header.set_font_size(12)
            header.set_font('Times new roman')
            header.set_align('center')
            header.set_align('vcenter')
            header.set_border(style=1)
            header.set_bg_color('#6495ED')

            header2 = workbook.add_format({'bold': 1})
            header2.set_font_size(9)
            header2.set_font('Times new roman')
            header2.set_align('left')
            header2.set_align('vcenter')
            header2.set_border(style=1)
            header2.set_bg_color('#6495ED')

            header3 = workbook.add_format({'bold': 1})
            header3.set_font_size(9)
            header3.set_font('Times new roman')
            header3.set_align('center')
            header3.set_align('vcenter')
            header3.set_border(style=1)

            contest_center = workbook.add_format()
            contest_center.set_text_wrap()
            contest_center.set_font_size(9)
            contest_center.set_font('Times new roman')
            contest_center.set_align('center')
            contest_center.set_align('vcenter')
            contest_center.set_border(style=1)

            contest_center_b = workbook.add_format({'bold': 1})
            contest_center_b.set_text_wrap()
            contest_center_b.set_font_size(9)
            contest_center_b.set_font('Times new roman')
            contest_center_b.set_align('center')
            contest_center_b.set_align('vcenter')
            contest_center_b.set_border(style=1)

            sheet = workbook.add_worksheet(u'Борлуулалт')
            row = 0
            sheet.merge_range(row, 0, row, 5, u'БОРЛУУЛАЛТЫН ГҮЙЦЭТГЭЛИЙН ТАЙЛАН', header)
            row += 1
            sheet.merge_range(row, 0, row, 5, u'Тайлант хугацаа: %s - %s'%(str(self.date_start),str(self.date_end)), header2)
            # Ерөнхий 
            row += 1
            sheet.merge_range(row, 0, row, 5, u'Ерөнхий', header3)
            row += 1
            sheet.merge_range(row, 0, row+1, 0, u'№', contest_center_b)
            sheet.merge_range(row, 1, row+1, 1, u'Үзүүлэлт', contest_center_b)
            sheet.set_column('B:B', 25)
            sheet.merge_range(row, 2, row, 3, u'Зорилт', contest_center_b)
            sheet.merge_range(row, 4, row, 5, u'Гүйцэтгэл', contest_center_b)
            row += 1
            sheet.write(row, 2, u'Тоо', contest_center_b)
            sheet.write(row, 3, u'Хувь', contest_center_b)
            sheet.write(row, 4, u'Тоо', contest_center_b)
            sheet.write(row, 5, u'Хувь', contest_center_b)
            row += 1

            sheet.write(row, 1, u'Нийт үүсгэсэн сэжим', contest_center_b)
            lead_obj = self.env['crm.lead']
            plan_obj = self.env['crm.sales.plan.line']
            objs = lead_obj.search([('create_date','>=',self.date_start),('create_date','<=',self.date_end)])
            com_days = (self.date_end-self.date_start).days
            plan_days = plan_obj.search([('plan_start_date','>=',self.date_end)]).mapped('stage_id')
            sheet.write(row, 2, u'34343', contest_center_b)
            sheet.write(row, 3, u'100%', contest_center_b)
            sheet.write(row, 4, u'%s'%(len(objs)), contest_center_b)
            sheet.write(row, 5, u'100%', contest_center_b)
            print('############', com_days, len(plan_days), plan_days)
            kk=0
            for xx in plan_days:
                ss = xx.name
                print("@@@@@@@@@@@@@@@",plan_days, ss)
                if ss:
                    row +=1
                    kk += 1
                    sheet.write(row, 1, ss, contest_center)
                    sheet.write(row, 0, kk, contest_center)
 
            

            workbook.close()
            out = base64.encodebytes(output.getvalue())
            excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})



            return {
                    'type' : 'ir.actions.act_url',
                    'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
                    'target': 'new',
            }


