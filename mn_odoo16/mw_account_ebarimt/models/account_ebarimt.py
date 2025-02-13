# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from dateutil.relativedelta import relativedelta

from io import BytesIO
import base64
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd


import logging
_logger = logging.getLogger(__name__)

class AccountEbarimtCalc(models.Model):
    _name = "account.ebarimt.calculation"
    _description = "Ebarimt calculation"

    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=lambda self: self.env.user.company_id)
    date = fields.Date('End date', required=True)
    line_ids = fields.One2many('account.ebarimt.calculation.line', 'parent_id', 'Lines')
    state = fields.Selection([('draft', 'Open'), ('done', 'Closed')], 'Status', default="draft", copy=False)
#     import_data_id = fields.Many2many('ir.attachment', 'mw_ebarimt_import_data_rel', 'data_id', 'attach_id', 'Файл', copy=False)
    import_data = fields.Binary('Exsel file')
    file_fname = fields.Char(string='File name')

    account_id = fields.Many2one('account.account', u'Хэрэгжсэн данс')
    from_account_id = fields.Many2one('account.account', u'Хэрэгжээгүй данс')
    journal_id = fields.Many2one('account.journal', u'Журнал')
    move_id = fields.Many2one('account.move', u'Ажил гүйлгээ')

    is_postpone = fields.Boolean('Хойшлуулах?', default=True)
    group_line_ids = fields.One2many('account.ebarimt.calculation.group.line', 'parent_id', 'Lines')
    account_line_ids = fields.One2many('account.ebarimt.calculation.account.line', 'parent_id', 'Lines')


    _order = "date"
    

    @api.onchange('import_data')
    @api.depends('import_data','file_fname')
    def check_file_type(self):
        if self.import_data:
            filename,filetype = os.path.splitext(self.file_fname)
    

    def get_partner_search(self, name,regno):
        partner_obj = self.env['res.partner']
        partner_id = partner_obj.search([('name','=',name)], limit=1)
        if not partner_id and regno:
            partner_id = partner_obj.search([('vat','=',regno)], limit=1)
        return partner_id
        
        
        
    def calculate_group(self):
        line_obj = self.env['account.ebarimt.calculation.group.line']
        for order in self:
            data={}
            if self.group_line_ids:
                    raise UserError(u'Мөрүүд үүссэн байна3!!! ')
            
            for line in order.line_ids:
                nonoat=line.amount
                nuat=line.nuat
                noattai=line.noattai
                if data.get(line.partner_id.id,False):
                    data[line.partner_id.id]['amount']+=nonoat
                    data[line.partner_id.id]['nuat']+=nuat
                    data[line.partner_id.id]['noattai']+=noattai
                    
                else:
                    l={'name':line.name,
                       'date':line.parent_id.date,
                       'parent_id':line.parent_id.id,
                       'regno':line.regno,
                       'partner_name':line.partner_name,
                       'partner_id':line.partner_id.id,
                       'amount':line.amount,
                       'nuat':line.nuat,
                       'noattai':line.noattai,
                       
                       }
                    data[line.partner_id.id]=l
                    
            print ('data ',data)
            for d in data:
                print ('d ',data[d])
                vals = {
                    'partner_id': data[d]['partner_id'],
                    'name': data[d]['name'],
                    'regno': data[d]['regno'],
                    'parent_id':self.id,
                    'amount':data[d]['amount'],
                    'noattai':data[d]['noattai'],
                    'nuat':data[d]['nuat'],
                    'date':data[d]['date'],
                    'partner_name':data[d]['partner_name'],
                    }
                
                line_id = line_obj.create(vals)                
                

    def calculate_account(self):
        line_obj = self.env['account.ebarimt.calculation.account.line']
        account_obj = self.env['account.account']
        for order in self:
            data={}
            if order.account_line_ids:
                    raise UserError(u'Мөрүүд үүссэн байна4!!! ')
            
            for line in order.group_line_ids:
                nuat=line.nuat
                first_day = self.date.replace(day=1)
#                 print ('first_day ',first_day)
                account=account_obj.with_context(date_to=self.date,partner_id=line.partner_id.id,date_from=first_day,state='posted').browse(line.parent_id.account_id.id)
                residual=account.debit-account.credit
                zuruu=residual-nuat
                vals={'name':line.name,
                   'date':line.parent_id.date,
                   'parent_id':line.parent_id.id,
                   'regno':line.regno,
                   'partner_name':line.partner_name,
                   'partner_id':line.partner_id.id,
                   'amount':nuat,
                   'residual':residual,
                   'zuruu':zuruu,
                   
                   }
                line_id = line_obj.create(vals)  
                self._cr.commit()            
                    
#             print ('data ',data)
#             for d in data:
#                 print ('d ',data[d])
#                 vals = {
#                     'partner_id': data[d]['partner_id'],
#                     'name': data[d]['name'],
#                     'regno': data[d]['regno'],
#                     'parent_id':self.id,
#                     'amount':data[d]['amount'],
#                     'noattai':data[d]['noattai'],
#                     'nuat':data[d]['nuat'],
#                     'date':data[d]['date'],
#                     'partner_name':data[d]['partner_name'],
#                     }
                
                                
    def create_period(self):
        print ('aaaaaaa11111 ')
        move_obj = self.env['account.move']
        if self.is_postpone:
            if self.move_id:
                raise UserError(u'Ажил гүйлгээ үүссэн байна!!! ')
            for order in self:
                lines=[]
                # if self.account_line_ids:
                #     raise UserError(u'Мөрүүд үүссэн байна!!! ')
                
                for line in order.account_line_ids:
                    ######=================
                    order_amount = line.zuruu
                    print ('order_amount ',order_amount)
                    if order_amount>0:
                        line_ids = [(0,0,{
                            'name': order.name,
                            'ref': order.name,
                            'account_id': order.from_account_id.id,
                            'debit': order_amount,
                            'credit': 0.0,
                            'journal_id': order.journal_id.id,
                            'partner_id': line.partner_id.id,
            #                         'currency_id': current_currency,
            #                         'amount_currency': order.company_id.currency_id.id != current_currency and order.value or 0.0,
                            'date': order.date,
            #                 'order_id': order.id
                        }),(0,0,{
                            'name': order.name,
                            'ref': order.name,
                            'account_id': self.account_id.id,
                            'debit': 0.0,
                            'credit': order_amount,
                            'journal_id': order.journal_id.id,
                            'partner_id': line.partner_id.id,
            #                         'currency_id': current_currency ,
            #                         'amount_currency': order.company_id.currency_id.id != current_currency and -order.value or 0.0,
                            'date': order.date,
            #                     'order_id': order.id
                        })]
                        lines+=line_ids
                move_vals = {
    #                     'order_id': order.id,#Элэгдэл бол
                    'name': order.name+':'+str(order.id),
                    'date': order.date,
                    'ref': order.name,
                    'journal_id': order.journal_id.id,
                    'line_ids': lines
                }
                move_id = move_obj.create(move_vals)            
    #             move_id.post()
                order.write({'move_id':move_id.id})            
        else:
            for order in self:
                lines=[]
#                 if self.line_ids:
#                     raise UserError(u'Мөрүүд үүссэн байна2!!! ')
                
                for line in order.line_ids:
                    ######=================
                    order_amount = line.nuat
                    line_ids = [(0,0,{
                        'name': order.name,
                        'ref': order.name,
                        'account_id': order.account_id.id,
                        'debit': order_amount,
                        'credit': 0.0,
                        'journal_id': order.journal_id.id,
                        'partner_id': line.partner_id.id,
        #                         'currency_id': current_currency,
        #                         'amount_currency': order.company_id.currency_id.id != current_currency and order.value or 0.0,
                        'date': order.date,
        #                 'order_id': order.id
                    }),(0,0,{
                        'name': order.name,
                        'ref': order.name,
                        'account_id': self.from_account_id.id,
                        'debit': 0.0,
                        'credit': order_amount,
                        'journal_id': order.journal_id.id,
                        'partner_id': line.partner_id.id,
        #                         'currency_id': current_currency ,
        #                         'amount_currency': order.company_id.currency_id.id != current_currency and -order.value or 0.0,
                        'date': order.date,
        #                     'order_id': order.id
                    })]
                    lines+=line_ids
                move_vals = {
    #                     'order_id': order.id,#Элэгдэл бол
                    'name': order.name+':'+str(order.id),
                    'date': order.date,
                    'ref': order.name,
                    'journal_id': order.journal_id.id,
                    'line_ids': lines
                }
                move_id = move_obj.create(move_vals)            
    #             move_id.post()
                order.write({'move_id':move_id.id})
            
    def action_import(self):
#         import_data = self.import_data_id[0].datas

#         if not import_data:
#             raise UserError('Оруулах эксэлээ Импортлох эксел-д хийнэ үү ')

        fileobj = NamedTemporaryFile('w+b')
        fileobj.write(base64.decodebytes(self.import_data))
        fileobj.seek(0)
#         if not os.path.isfile(fileobj.name):
#             raise osv.except_osv(u'Aldaa')
        book = xlrd.open_workbook(fileobj.name)
        try :
            sheet = book.sheet_by_index(0)
        except:
            raise UserError(u'Алдаа')
        
        line_obj = self.env['account.ebarimt.calculation.line']
        nrows = sheet.nrows
        rowi = 1
        missing_parts=[]
        for item in range(rowi,nrows):
            row = sheet.row(item)
            padaan = row[0].value
            ddtd = row[1].value
            ognoo = row[2].value
            partner_name = row[3].value
#             regno = row[4].value
            nuat = row[5].value
            nonoat = row[6].value
            noattai = row[7].value
            
            
            serial = ognoo
            # seconds = (serial - 25569) * 86400.0
            # date=datetime.utcfromtimestamp(seconds)
            
            try:
                str_regno =   row[4].value
            except Exception:
                str_regno=''
            
            if type(str_regno) in [float]:
                regno = str(str_regno).strip().split('.')[0]
            elif type(str_regno) in [int]:
                regno = str(str_regno).strip()
            else:
                regno = str_regno.strip()
            
#             try:
#                 date = datetime.strptime(ognoo, '%Y-%m-%d')
#             except ValueError:
#                 raise ValidationError(_('Date error %s row! \n \
#                 format must \'YYYY-mm-dd\'' % rowi))

            partner_id = self.get_partner_search(partner_name,regno)
            if not partner_id:
                missing=u'Нэр: '+partner_name+u' Регистр: ' +str(regno) +', '
                missing_parts.append(missing)
#             print ('partner_id ',partner_id)
#         print ('missing_parts ',missing_parts)
        if len(missing_parts)>0:
            raise UserError(u'{0}  харилцагчид ERP  дээр олдсонгүй!!'.format(missing_parts))
                    
        for item in range(rowi,nrows):
            row = sheet.row(item)
            padaan = row[0].value
            ddtd = row[1].value
            ognoo = row[2].value
            partner_name = row[3].value
#             regno = row[4].value
            nuat = row[5].value
            nonoat = row[6].value
            noattai = row[7].value
            

            try:
                str_regno =   row[4].value
            except Exception:
                str_regno=''
            
            if type(str_regno) in [float]:
                regno = str(str_regno).strip().split('.')[0]
            elif type(str_regno) in [int]:
                regno = str(str_regno).strip()
            else:
                regno = str_regno.strip()
                            
            serial = ognoo
            # seconds = (serial - 25569) * 86400.0
            # date=datetime.utcfromtimestamp(seconds)
#             try:
#                 date = datetime.strptime(ognoo, '%Y-%m-%d')
#             except ValueError:
#                 raise ValidationError(_('Date error %s row! \n \
#                 format must \'YYYY-mm-dd\'' % rowi))

            partner_id = self.get_partner_search(partner_name,regno)
#             print ('partner_id ',partner_id)
            if not partner_id:
                raise UserError(u'{0} нэртэй {1} регистртэй харилцагч ERP  дээр олдсонгүй!!'.format(partner_name,regno))
            vals = {
                'partner_id': partner_id.id,
                'name': ddtd,
                'regno': regno,
                'parent_id':self.id,
                'amount':nonoat,
                'noattai':noattai,
                'nuat':nuat,
                'padaan':padaan,
                'date':ognoo,
                'partner_name':partner_name,
                }
            
# name = fields.Char('Name', required=True)
#     date = fields.Date('Start of Period', required=True, states={'done': [('readonly', True)]})
#     parent_id = fields.Many2one('account.ebarimt.calculation', 'Ebarimt')
#     partner_id = fields.Many2one('res.partner', 'Partner')
#     regno = fields.Char('Register', required=True)
#     partner_name = fields.Char('Partner Name')
#     padaan = fields.Char('Padaan')
#     amount = fields.Float('Amount')            
            line_id = line_obj.create(vals)
#             print ('line_id' ,line_id)

        return True,


