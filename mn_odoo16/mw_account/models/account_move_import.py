# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections
from calendar import monthrange
from io import BytesIO
import base64
# import encodestring
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd

class account_move_import(models.Model):
    _name = 'account.move.import'
    _inherit = ['mail.thread']
    _description = 'account move import'
    _order = 'date desc,name'

    name = fields.Char('Нэр')
    date = fields.Date('Огноо', required=True)
    state = fields.Selection([('draft','Ноорог'), ('done','Дууссан')], default='draft', string='Төлөв')
    import_data = fields.Binary('Импортлох эксел', copy=False)
    export_data = fields.Binary('Export excel file')
    line_ids = fields.Many2many('account.move','account_move_import_move_res','import_id','move_id','Moves')
    journal_id = fields.Many2one('account.journal','Journal')

    
    def action_done(self):
        self.write({'state':'done'})


    def action_post(self):
        for item in self:
            for line in item.line_ids:
                if line.state == 'draft':
                    line.action_post()
            
#         self.write({'state':'done'})

    
    def action_draft(self):
        self.write({'state':'draft'})

    
    def action_export(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(u'moves')
        
        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(9)
        h1.set_align('center')
        h1.set_font_name('Arial')

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#9ad808')
        header.set_text_wrap()
        header.set_font_name('Arial')
        
        header_wrap = workbook.add_format({'bold': 1})
        header_wrap.set_text_wrap()
        header_wrap.set_font_size(11)
        header_wrap.set_align('center')
        header_wrap.set_align('vcenter')
        header_wrap.set_border(style=1)
        # header_wrap.set_fg_color('#6495ED')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_right = workbook.add_format()
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)
        contest_right.set_num_format('#,##0.00')

        contest_center = workbook.add_format()
        contest_center.set_text_wrap()
        contest_center.set_font_size(9)
        contest_center.set_align('center')
        contest_center.set_align('vcenter')
        contest_center.set_border(style=1)
        contest_center.set_font_name('Arial')

        cell_format2 = workbook.add_format({
        'border': 1,
        'align': 'right',
        'font_size':9,
        'font_name': 'Arial',
        # 'text_wrap':1,
        'num_format':'#,####0'
        })

        
        row = 0
        last_col = 9
        worksheet.write(row, 0, u"Move", header)
        worksheet.write(row, 1, u"Date", header)
        worksheet.write(row, 2, u"Account", header)
        worksheet.write(row, 3, u"Partner registr", header)
        worksheet.write(row, 4, u"Transaction text", header)
        worksheet.write(row, 5, u"debit", header)
        worksheet.write(row, 6, u"Credit", header)
        worksheet.write(row, 7, u"Currency", header)
        worksheet.write(row, 8, u"Currency amount", header)
        worksheet.write(row, 9, u"Analytic account", header)
        worksheet.write(row, 10, u"Equipment", header)
        worksheet.write(row, 11, u"VAT?", header)
        worksheet.write(row, 12, u"Reconcile number", header)
        worksheet.write(row, 13, u"Branch name", header)
        worksheet.write(row, 14, u"Product code", header)
        

        workbook.close()

        out = base64.encodebytes(output.getvalue())
        excel_id = self.write({'export_data': out})

        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=account.move.import&id=" + str(self.id) + "&filename_field=filename&download=true&field=export_data&filename=" + self.name+'.xlsx',
             'target': 'new',
        }


    def action_import(self):
        if not self.import_data:
            raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')

        try:
            fileobj = NamedTemporaryFile('w+b')
            fileobj.write(base64.b64decode(self.import_data))
            fileobj.seek(0)
            book = xlrd.open_workbook(fileobj.name)
        except ValueError:
            raise UserError(
                _('Error loading data file. \ Please try again!'))
        

        
        try :
            sheet = book.sheet_by_index(0)
        except:
            raise osv.except_osv(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
        nrows = sheet.nrows
        
        rowi = 1
        move_obj = self.env['account.move']
        analytic_obj = self.env['account.analytic.account']
        analytic_distr = self.env['account.analytic.account']
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        curr_obj = self.env['res.currency']
        aml_obj = self.env['account.move.line']
        moves={}
        line_vals=[]
        debit_sum=credit_sum=0
        recon_aml_ids=[]
        partners=''
        for item in range(rowi,nrows):
            row = sheet.row(item)
            move_id = row[0].value
            dd = row[1].value
            account_code = row[2].value
            partner_name = row[3].value
            if not dd:
                raise ValidationError(_('Огноо хоосон мөр байна, эсвэл excel ийн доод талын мөрүүдээ устгана уу!!! '))  
            if len(row)<13:
                raise ValidationError(_('Багана дудуу байна Баганыу толгой хэсгийг загварын дагуу гүйцэд оруулж өгнө үү, Датагүй бол хоосон орхиж болно!!! '))  
            try:
                if type(dd)==float:
                    serial = dd
                    seconds = (serial - 25569) * 86400.0
                    date=datetime.utcfromtimestamp(seconds)
                else:
                    date = datetime.strptime(dd, '%Y-%m-%d')
            except ValueError:
                raise ValidationError(_('Date error %s row! \n \
                format must \'YYYY-mm-dd\'' % rowi))  

            
            try:
                if type(partner_name)==float or type(partner_name)==int:
                    partner_name = int(partner_name)
                else:
                    partner_name = partner_name
            except ValueError:
                partner_name=partner_name
            if partner_name:
                partner_id=partner_obj.search([('vat','=',partner_name)])
                if not partner_id:
                    partner_name=str(partner_name)
                    partner_id=partner_obj.search([('vat','=',partner_name.upper())])
                    if not partner_id:
                        partner_id=partner_obj.search([('vat','=',partner_name.lower())])
                        if not partner_id:
                            partner_id=partner_obj.search([('vat','=',partner_name.capitalize())])
                            if not partner_id:
                                pname=partner_name.lower()[0]+partner_name.lower()[1].upper()+partner_name.lower()[2:]
                                partner_id=partner_obj.search([('vat','=',pname)])
                                if not partner_id:
                                    partner_name=str(partner_name)
                                    partner_id=partner_obj.search([('name','=',partner_name)])
                                    if not partner_id:
                                        partner_name=str(partner_name)
                                        partner_id=partner_obj.search([('name','=',partner_name.upper())])
                                        if not partner_id:
                                            partner_id=partner_obj.search([('name','=',partner_name.lower())])
                                            if not partner_id:
                                                partner_id=partner_obj.search([('name','=',partner_name.capitalize())])
                                                if not partner_id:
                                                    ppname=partner_name.lower()[0]+partner_name.lower()[1].upper()+partner_name.lower()[2:]
                                                    partner_id=partner_obj.search([('name','=',ppname)])
            if partner_name and not partner_id:
                partners+=partner_name+' , '

            if moves.get(move_id):
                continue
            else:
                move_vals = {
                    'date': date,
                    'ref': self.name,
                    'journal_id': self.journal_id.id,
                }
                new_move_id = move_obj.create(move_vals)                 
                moves[move_id]=new_move_id
        print ('moves ',moves)
        if len(partners)>5:
            raise ValidationError(_('Харилцагч олдсонгүй %s ! ' % partners))  
            
        for item in range(rowi,nrows):
            row = sheet.row(item)
            move_id = row[0].value
            excel_date = row[1].value
            account_code = row[2].value
            partner_name = row[3].value
            name = row[4].value
            debit = row[5].value
            credit = row[6].value
            currency = row[7].value
            currency_amount = row[8].value
            analytic_code = row[9].value
            technic_code = row[10].value
            is_vat = row[11].value
            is_vat = str(is_vat).split('.')[0]
            reconcile_num = row[12].value   
            branch_name = row[13].value    
            print ('reconcile_num ',reconcile_num)
            account_code = str(account_code).split('.')[0]
            analytic_code = str(analytic_code).split('.')[0]
            technic_code = str(technic_code).split('.')[0]
            print ('analytic_code ',analytic_code)
            analityc_lines={}
            if analytic_code:
                analytic_datas=analytic_code.split(',')
                print ('analytic_datas ',analytic_datas)
                
                for ad in analytic_datas:
                    print ('ad ',ad)
                    aa=ad.split(':')
                    print ('aa[0] ',aa)
                    analytic_id = analytic_obj.search([('name','=',aa[0])], limit=1)
                    line = ''
                    if analytic_id:
                        # analityc_lines.append({str(analytic_id.id):float(aa[1])})
                        analityc_lines[str(analytic_id.id)]=100

            print ('analityc_lines ',analityc_lines)
            # aaaa=''
            # for i in analityc_lines:
            #     aaaa+=str(i)+','
            # print ('aaaa ',aaaa)
            # analytic_id = analytic_obj.search([('name','=',analytic_code)], limit=1)
            account_id = account_obj.search([('code','=',account_code)], limit=1)
            branch_id = self.env['res.branch'].search([('name','=',branch_name)], limit=1)
            
            curr_id = curr_obj.search([('name','=',currency)], limit=1)
            if not self.date:
                raise UserError(_(u'Огноо оруулана уу.'))
            date=self.date
            if currency == 'MNT':
                if debit:
                    currency_amount = debit
                elif credit:
                    currency_amount = credit * (-1)
            partner_id=False
            try:
                if type(partner_name)==float or type(partner_name)==int:
                    partner_name = int(partner_name)
                else:
                    partner_name = partner_name
            except ValueError:
                raise ValidationError(_('Харилцагч олдсонгүй %s row! ' % rowi))  
            if partner_name:
                partner_id=partner_obj.search([('vat','=',partner_name)])
                if not partner_id:
                    partner_name=str(partner_name)
                    partner_id=partner_obj.search([('vat','=',partner_name.upper())])
                    if not partner_id:
                        partner_id=partner_obj.search([('vat','=',partner_name.lower())])
                        if not partner_id:
                            partner_id=partner_obj.search([('vat','=',partner_name.capitalize())])
                            if not partner_id:
                                pname=partner_name.lower()[0]+partner_name.lower()[1].upper()+partner_name.lower()[2:]
                                partner_id=partner_obj.search([('vat','=',pname)])
                                if not partner_id:
                                    partner_name=str(partner_name)
                                    partner_id=partner_obj.search([('name','=',partner_name)])
                                    if not partner_id:
                                        partner_name=str(partner_name)
                                        partner_id=partner_obj.search([('name','=',partner_name.upper())])
                                        if not partner_id:
                                            partner_id=partner_obj.search([('name','=',partner_name.lower())])
                                            if not partner_id:
                                                partner_id=partner_obj.search([('name','=',partner_name.capitalize())])
                                                if not partner_id:
                                                    ppname=partner_name.lower()[0]+partner_name.lower()[1].upper()+partner_name.lower()[2:]
                                                    partner_id=partner_obj.search([('name','=',ppname)])
            if partner_name and not partner_id:
                raise ValidationError(_('Харилцагч олдсонгүй %s ! ' % partner_name))  

            if account_id:
                account_id=account_id.id
            else:
                raise UserError(_(u'Данс олдсонгүй {0}.'.format(account_code)))
            if partner_id and len(partner_id)==1:
                partner_id=partner_id.id
            elif partner_name and  len(partner_id)>1 :
                raise UserError(_(u'Дараах харилцагч олон үүссэн байна {0}.'.format(partner_id[0].name)))
            

            try:
                product_name = row[14].value
            except Exception:
                product_name=''
            
            product_id=False
            if product_name:
                product = self.env['product.product'].search([('default_code', '=', product_name)], limit=1)
                if not product:
                    raise UserError(_("No product matching '%s'.") % product_name)
                product_id = product.id
            print ('product_id ',product_id)
                                        
            if moves.get(move_id):
                new_move_id=moves[move_id]
            print ('partner_id ',partner_id)
            if is_vat and int(is_vat)==1:
                vat=0
                is_debit=True
                if debit:
                    vat=round(debit/1.1,2)
                    debit=debit-vat
                elif credit:
                    vat=round(credit/1.1,2)
                    credit=credit-vat
                    is_debit=False
                    
                aml_dict = {
                    'name': name,
                    'ref': self.name,
                    'account_id': account_id,
                    'debit':debit and debit or 0,
                    'credit':  credit and credit or 0,
                    'journal_id': self.journal_id.id,
                    'currency_id': curr_id and curr_id.id or False,
                    'amount_currency': currency_amount,
                    'date': date,
                    'partner_id': partner_id,
                    'move_id':new_move_id.id,
                    'branch_id':branch_id and branch_id.id or False,
                    'product_id':product_id ,
                    'analytic_distribution':analityc_lines
                }
                new_aml_id = aml_obj.with_context(check_move_validity=False).create(aml_dict)                

                if reconcile_num:
                    aml_id = aml_obj.search([
                                        ('name','=',reconcile_num),
                                        ('partner_id','=',partner_id),
                                        ('account_id','=',account_id),
                                        ])
                    (new_aml_id | aml_id).reconcile()      
                tax_account_id=self.env['account.tax'].search([('account_id','!=','')], limit=1).account_id
                aml_dict = {
                    'name': name+u' НӨАТ',
                    'ref': self.name+u' НӨАТ',
                    'account_id': tax_account_id.id,
                    'debit':is_debit and vat or 0,
                    'credit':  not is_debit and vat or 0,
                    'journal_id': self.journal_id.id,
                    'date': date,
                    'partner_id': partner_id,
                    'move_id':new_move_id.id,
                    'branch_id':branch_id and branch_id.id or False,
                    'product_id':product_id 
                }      
                new_aml_id = aml_obj.with_context(check_move_validity=False).create(aml_dict)                
                                         
            else:
                aml_dict = {
                    'name': name,
                    'ref': self.name,
                    'account_id': account_id,
                    'debit':debit and debit or 0,
                    'credit':  credit and credit or 0,
                    'journal_id': self.journal_id.id,
                    'currency_id': curr_id and curr_id.id or False,
                    'amount_currency': currency_amount,
                    'date': date,
                    'partner_id': partner_id,
                    'move_id':new_move_id.id,
                    'branch_id':branch_id and branch_id.id or False,
                    'product_id':product_id ,
                    'analytic_distribution':analityc_lines
                }
                new_aml_id = aml_obj.with_context(check_move_validity=False).create(aml_dict)                

                if reconcile_num:
                    aml_id = aml_obj.search([
                                        ('name','=',reconcile_num),
                                        ('partner_id','=',partner_id),
                                        ('account_id','=',account_id),
                                        ])
                    (new_aml_id | aml_id).reconcile()                  
            credit_sum+=credit and credit or 0
            debit_sum+=debit and debit or 0
        for move in moves :
            self.env.cr.execute("insert into account_move_import_move_res(import_id,move_id) values({0},{1})".format(self.id,moves[move].id))  
        return new_move_id            
         
    def get_vals(self,name,account_id,debit,credit,date,partner_id):
        return {
                    'name': name,
                    'ref': self.name,
                    'account_id': account_id,
                    'debit':debit and debit or 0,
                    'credit':  credit and credit or 0,
                    'journal_id': self.journal_id.id,
                    'date': date,
                    'partner_id': partner_id,
                }
        
    def action_import_mdlold(self):
        if not self.import_data:
            raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')

        try:
            fileobj = NamedTemporaryFile('w+b')
            fileobj.write(base64.decodebytes(self.import_data))
            fileobj.seek(0)
            book = xlrd.open_workbook(fileobj.name)
        except ValueError:
            raise UserError(
                _('Error loading data file. \ Please try again!'))
        

        
        try :
            sheet = book.sheet_by_index(0)
        except:
            raise osv.except_osv(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
        nrows = sheet.nrows
        
        rowi = 1
        move_obj = self.env['account.move']
        analytic_obj = self.env['account.analytic.account']
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        aml_obj = self.env['account.move.line']
        moves={}
        line_vals=[]
        debit_sum=credit_sum=0
        recon_aml_ids=[]
        for item in range(rowi,nrows):
            row = sheet.row(item)
            move_id = row[0].value
            excel_date = row[1].value
            account_code = row[2].value
            partner_name = row[3].value
            name = row[4].value
            debit = row[5].value
            credit = row[6].value
            currency = row[7].value
            currency_amount = row[8].value
            analytic_code = row[9].value
            technic_code = row[10].value
            is_vat = row[11].value
            is_vat = str(is_vat).split('.')[0]
            reconcile_num = row[12].value    
            print ('reconcile_num ',reconcile_num)
            account_code = str(account_code).split('.')[0]
            analytic_code = str(analytic_code).split('.')[0]
            technic_code = str(technic_code).split('.')[0]
            analytic_id = analytic_obj.search([('code','=',analytic_code)], limit=1)
            account_id = account_obj.search([('code','=',account_code)], limit=1)
            if not self.date:
                raise UserError(_(u'Огноо оруулана уу.'))
            date=self.date
            print ('partner_name ',partner_name)
            partner_id=partner_obj.search([('vat','=',partner_name)])

            print ('partner_id ',partner_id)
            if account_id:
                account_id=account_id.id
            if len(partner_id)==1:
                partner_id=partner_id.id
            elif len(partner_id)>1:
                raise UserError(_(u'Дараах харилцагч олон үүссэн байна {0}.'.format(partner_id[0].name)))
            
            if reconcile_num:
                tmp={'domain':[
                                    ('name','=',reconcile_num),
                                    ('partner_id','=',partner_id),
                                    ('account_id','=',account_id),
                                    ]
                    }
                recon_aml_ids.append(tmp)
            if moves.get(move_id):
                moves[move_id]={''}
            if is_vat and int(is_vat)==1:
                vat=0
                is_debit=True
                if debit:
                    vat=round(debit/1.1,2)
                    debit=debit-vat
                elif credit:
                    vat=round(credit/1.1,2)
                    credit=credit-vat
                    is_debit=False
                vals=self.get_vals(name,account_id,debit,credit,date,partner_id)
                line_vals.append([0,0,vals])
                tax_account_id=self.env['account.tax'].search([('account_id','!=','')], limit=1).account_id
                get_vals =self.get_vals() 
                vals=self.get_vals(name+u' НӨАТ',tax_account_id.id,is_debit and vat or 0,not is_debit and vat or 0,date,partner_id)
                line_vals.append([0,0,vals])                                
            else:
                vals=self.get_vals(name,account_id,debit,credit,date,partner_id)
                line_vals.append([0,0,vals])
            credit_sum+=credit and credit or 0
            debit_sum+=debit and debit or 0
            
        new_name = '/'
        journal = self.journal_id
        if journal.sequence_id:
                sequence = journal.sequence_id
                new_name = sequence.with_context(ir_sequence_date=self.date).next_by_id()
        else:
            raise UserError(_('Please define a sequence on the journal.'))

        move_vals = {
            'date': self.date,
            'ref': self.name,
            'journal_id': self.journal_id.id,
            'line_ids': line_vals
        }
        move_id = move_obj.create(move_vals)
        
                            
        self.env.cr.execute("insert into account_move_import_move_res(import_id,move_id) values({0},{1})".format(self.id,move_id.id))  
        return move_id            
         
    
