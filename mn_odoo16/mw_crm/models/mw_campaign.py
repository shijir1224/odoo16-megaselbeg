# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
import base64
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd

class mw_campaign(models.Model):
    _name = 'mw.campaign'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = 'Борлуулалтын аян'
    
    name = fields.Char('Аяны нэр', tracking=True, required=True)
    partner_ids = fields.Many2many('res.partner', 'res_partner_mw_campaign_rel', 'partner_id', 'campaign_id', string='Харилцагчид')
    lead_ids = fields.One2many('crm.lead', 'mw_campaign_id', string='Нийт ажилууд')
    state = fields.Selection([('draft','Шинэ'),('planned','Төлөвлөсөн'),('done','Дууссан')], string='Төлөв', default='draft', tracking=True )
    date_start = fields.Date(string='Эхлэх огноо', tracking=True)
    date_end = fields.Date(string='Дуусгах огноо', tracking=True)
    actual_percent = fields.Float(string='Гүйцэтгэлх %', compute='_compute_actual_percent')
    niit_ajiluud = fields.Float(string='Нийт ажилууд', compute='_compute_actual_percent')
    sanuulsan_ajiluud = fields.Float(string='Сануулсан ажилууд', compute='_compute_actual_percent')
    biyelesen_ajiluud = fields.Float(string='Биелэсэн ажилууд', compute='_compute_actual_percent')
    amjiltgui_ajiluud = fields.Float(string='Амжилтгүй ажилууд', compute='_compute_actual_percent')
    import_file_id = fields.Binary('Импортлох эксел', copy=False)
    user_ids = fields.Many2many('res.users', 'res_user_mw_campaign_rel', 'user_id', 'campaign_id', string='Борлуулагч')
    campaign_activity_type_id = fields.Many2one('mail.activity.type', string='Үйл ажиллагааны Төрөл', tracking=True, default=False)
    lead_type = fields.Selection([('lead', 'Lead'), ('opportunity', 'Opportunity')], default='lead', string="Lead type")
    campaign_type = fields.Selection([('from_partner', 'Байгаа харилцагчаас'), ('from_line', 'Байхгүй харилцагчаас')], default='from_partner', string="Импортлох төрөл")
    sale_type = fields.Selection([('upsale', 'Up sale'), ('crosale', 'Cro sale')], string="Борлуулалтын төрөл")
    import_lines = fields.One2many('mw.campaign.line', 'parent_id', string="Импортлох мөр")
    warning_messages = fields.Html(string='Мэдээлэл', compute='_compute_contract_messages', readonly=True, )
    warning_messages_not = fields.Html(string='Мэдээлэл not', readonly=True, default=' ')
    lead_count = fields.Integer(string="Lead count", compute='_compute_lead_count')
    visible_departments = fields.Many2many('hr.department', string='Харагдах хэлтэсүүд', compute='com_visible_departments')

    def com_visible_departments(self):
        obj = self.env['hr.department']
        for item in self:
            item.visible_departments = obj.sudo().search([('id','child_of',[self.env.user.department_ids.id])])

    def _compute_lead_count(self):
        for item in self:
            item.lead_count = len(item.lead_ids)

    def view_lead(self):
        self.ensure_one()
        if self.lead_type =='lead':
            action = self.env.ref('crm.crm_lead_all_leads').read()[0]
        else:
            action = self.env.ref('crm.crm_lead_opportunities').read()[0]
        action['domain'] = [('id','in',self.lead_ids.ids)]
        return action

    def get_value_str(self):
        return """
                    <span>Харилцагч экселээс оруулах загвар /Эхний шийт дээрээсээ 2 дахь мөрөөс/</span><br/>
                    <table style="width: 70%">
                        <tr>
                            <td>1. ХАРИЛЦАГЧИЙН НЭР</td>
                            <td>2. УТАС</td>
                            <td>3. МАЙЛ/Заавал оруулахгүй байж болно/</td>
                        </tr>
                    </table>
        """
    @api.depends('warning_messages_not')
    def _compute_contract_messages(self):
        for obj in self:
            message = obj.get_value_str()
            obj.warning_messages = message+obj.warning_messages_not
    
    def assign_user(self):
        if self.campaign_type=='from_partner' and not self.partner_ids:
            raise UserError(u'Харилцагч заавал оруулж өгнө')

        elif self.campaign_type=='from_line' and not self.import_lines:
            raise UserError(u'Импортлох мөр заавал оруулна')
        if self.lead_ids:
            raise UserError(u'Оноолт хийгдсэн байна!!!')
        if not self.user_ids:
            raise UserError(u'Борлуулагч сонгоогүй байна!!!')

        lead_obj = self.env['crm.lead']
        import_lines = self.partner_ids
        partner_ok = True
        if self.campaign_type=='from_line':
            import_lines = self.import_lines
            partner_ok = False
        len_p = len(import_lines)
        p_obj = import_lines
        item = 0
        
        def f_create_lead(f_partner_id, f_user, f_p_name, f_p_phone, f_p_mail):
            lead_obj = self.env['crm.lead']
            f_p_n = f_p_name or f_partner_id.name
            print ('>>>>>>>>>>------------------')
            lll = {
                    'mw_campaign_id': self.id,
                    'name': self.name+' '+f_p_n,
                    'partner_id': f_partner_id.id if f_partner_id else False,
                    'user_id': f_user.id,
                    'type': self.lead_type,
                    'phone': f_p_phone,
                    'email_from': f_p_mail,
            }
            return lll
        crm_lead_vals = []
        while item < len_p:
            for user in self.user_ids:
                p_id = p_obj[item] if partner_ok else False
                p_name = p_obj[item].partner_name if not partner_ok else ''
                p_phone = p_obj[item].partner_phone if not partner_ok else ''
                p_mail = p_obj[item].partner_mail if not partner_ok else ''
                crm_lead_vals.append(f_create_lead(p_id, user, p_name, p_phone, p_mail))
                item = item+1
                if item>=len_p:
                    break
            if item>=len_p:
                break
        if crm_lead_vals:
            for cc in crm_lead_vals:
                lead_obj.create(cc)

        for lea in self.lead_ids:
            if self.activity_type_id:
                self.create_activity(lead_id, lea.user_id)
    
    def create_activity(self, lead_id, user):
        self.env['mail.activity'].create({
            'activity_type_id': self.activity_type_id.id,
            'user_id': user.id,
            'date_deadline': lead_id.date_open,
            'summary': lead_id.name,
            'res_id': lead_id.id,
            'res_model': 'crm.lead',
            'res_model_id': self.env['ir.model']._get('crm.lead').id,
        })
    
    def get_value(self, f_value):
        try:
            if type(f_value) in [float, int]:
                f_value = str(int(f_value))
        except Exception as e:
            return ''
        return f_value

    def cold_call_import(self):
        if not self.import_file_id:
            raise UserError(u'Файлаа оруулна уу!!!')
        import_data = self.import_file_id
        fileobj = NamedTemporaryFile('w+b')
        fileobj.write(base64.decodebytes(import_data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise UserError(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        book = xlrd.open_workbook(fileobj.name)
        try :
            sheet = book.sheet_by_index(0)
        except:
            raise osv.except_osv(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
        nrows = sheet.nrows
        p_obj = self.env['res.partner']
        rowi = 2
        p_ids = []
        oldoogui_par = []
        for item in range(rowi,nrows):
            row = sheet.row(item)
            p_name = row[0].value
            p_phone = self.get_value(row[1].value)
            p_mail = ''
            if row[2].value:
                p_mail = row[2].value
            p_id = False
            if p_phone:
                p_id = p_obj.search(['|',('phone','ilike',p_phone),('mobile','ilike',p_phone)],limit=1)
            
            if self.campaign_type=='from_partner':
                if p_id:
                    p_ids.append(p_id.id)
                else:
                    oldoogui_par.append(p_name)
            
            if self.campaign_type=='from_line':
                self.import_lines.create({
                    'partner_name': p_name,
                    'partner_id': p_id.id if p_id else False,
                    'partner_phone': p_phone,
                    'partner_mail': p_mail,
                    'parent_id': self.id,
                })
        if self.campaign_type=='from_partner':
            print ('p_ids',p_ids)
            print ('oldoogui_par',oldoogui_par)
            self.partner_ids = p_ids
            ht = ''
            if oldoogui_par:
                ht = """<span style='color:red;'>Олдоогүй харилцагчид %s</span><br/>"""%(', '.join(oldoogui_par))
                
            print ('ht',ht)
            self.warning_messages_not = ht

    def remove_line(self):
        self.lead_ids.unlink()
        self.partner_ids = False
        self.import_lines.unlink()

    @api.depends('lead_ids')
    def _compute_actual_percent(self):
        for item in self:
            item.niit_ajiluud = 0
            item.sanuulsan_ajiluud = 0
            item.biyelesen_ajiluud = 0
            item.amjiltgui_ajiluud = 0
            item.actual_percent = 0
            # item.niit_ajiluud = len(item.lead_ids)
            # item.sanuulsan_ajiluud = len(item.lead_ids.filtered(lambda r: r.stage_id.state_type not in ['draft','loss','won']))
            # item.biyelesen_ajiluud = len(item.lead_ids.filtered(lambda r: r.stage_id.state_type in ['won']))
            # item.amjiltgui_ajiluud = len(item.lead_ids.filtered(lambda r: r.stage_id.state_type in ['loss']))
            # not_draft = item.sanuulsan_ajiluud+item.biyelesen_ajiluud+item.amjiltgui_ajiluud
            # item.actual_percent = (100*not_draft)/item.niit_ajiluud if item.niit_ajiluud>0 else 0
    
    def action_done(self):
        self.state = 'done'
    
    def action_draft(self):
        self.state = 'draft'
    
    def action_plan(self):
        self.state = 'planned'

    def export_template(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        file_name = 'Аян темплати.xlsx'

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

        # Борлуулагчаар харуулах sheet
        worksheet = workbook.add_worksheet(u'Аян')
        worksheet.write(0,1, u"Аяны импортлох загвар", h1)
        # TABLE HEADER
        row = 1
        worksheet.set_row(row, 20)
        worksheet.write(row, 0, u"Харицлагчийн нэр", header)
        worksheet.set_column('A:A', 18)
        worksheet.write(row, 1, u"Утас", header_wrap)
        worksheet.set_column('B:B', 12)
        worksheet.write(row, 2, u"Майл", header_wrap)
        worksheet.set_column('C:C', 18)
        
        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

        return {
                'type' : 'ir.actions.act_url',
                'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
                'target': 'new',
        }

class mw_campaign_line(models.Model):
    _name = 'mw.campaign.line'
    _description = 'Борлуулалтын аян мөр'

    parent_id = fields.Many2one('mw.campaign', string='Аян', ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Байгаа харилцагч")
    partner_name = fields.Char(string="Харилцагчийн нэр")
    partner_phone = fields.Char(string="Утас")
    partner_mail = fields.Char(string="Майл")
    