# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import base64
import xlrd
from tempfile import NamedTemporaryFile
from datetime import datetime
from io import BytesIO
import xlsxwriter
from tempfile import NamedTemporaryFile

class AccountBankStatementImportFile(models.TransientModel):
    _name = 'account.bank.statement.import.file'
    _description = "Import File"

    type = fields.Selection([('default','Энгийн'),
                             ('golomt','Голомт'),
                             ('tdb','ХХБ'),
                             ('xac','ХАС'),
                             ('khaan','ХААН'),
                             ('tur','ТӨР'),
                             ('capitron','Капитрон'),
                             ('arig','Ариг'),
                             ('uhob','ҮХОБ'),
                             ('teever','Тээвэр'),
                             ('credit','Кредит'),
                             ],'TYPE',default='default')
    data_file = fields.Binary(string='Харилцахын хуулганы файл', help='Get you bank statements in electronic format from your bank and select them here.')


    desc = fields.Text('Template', default="""# A Огноо 2020-02-10 загвартай байна
# B Гүйлгээний утга
# C харилцагчийн ERP нэр
# D Дүн Орлого + Зарлага бол -
# E Дансны код 
# F Мөнгөн гүйлгээний төрлийн нэр
# G Салбарын нэр ERP дээрх
# H Банкны данс
# I Шинжилгээний данс нэр
# J Банкны гүйлгээний утга
# K Шимтгэл эсэх TRUE, FALSE
# L Харилцахын журналын үндсэн данс 
""", readonly=True)
    result = fields.Html(string='Үр дүн', readonly=True)
    
    def import_file(self):
        if not self.data_file:
            raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')
        context = self._context
        statement=None
        # if context.get('active_model') == 'account.bank.statement' and context.get('active_ids'):
        #     statement = self.env['account.bank.statement'].browse(context['active_ids'])[0]
        # if not statement:
        #     raise UserError(_("No active statement!"))
            
            
        try:
            fileobj = NamedTemporaryFile('w+b')
            fileobj.write(base64.decodebytes(self.data_file))
            fileobj.seek(0)
            book = xlrd.open_workbook(fileobj.name)
        except ValueError:
            raise UserError(
                _('Error loading data file. \ Please try again!'))
        
        # start_sequence = 1
        # last_statment_line = self.env['account.bank.statement.line'].search([('statement_id', '=', statement.id)], order='sequence desc', limit=1)
        # if last_statment_line:
        #     start_sequence = last_statment_line.sequence+1

        sheet = book.sheet_by_index(0)
        nrows = sheet.nrows
        rowi = 1
        partners=''
                    
        while rowi < nrows:
            partner_id = False
            row = sheet.row(rowi)
            dd=row[0].value
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
                
            name = row[1].value
            name_ref = row[9].value
            is_qpay = row[10].value
            try:
                partner_name = row[2].value
            except Exception:
                partner_name=''
            partner = self.env['res.partner'].search([('name', '=', partner_name)], limit=1)
            if partner_name and len(str(partner_name))>1:
                if partner:
                    partner_id = partner.id
                else :
                    partner = self.env['res.partner'].search([('vat', '=', partner_name)], limit=1)
                    if partner:
                        partner_id = partner.id
                    else:
                        partner_vat=partner_name
                        if type(partner_name) in [float]:
                            partner_vat = str(partner_name).strip().split('.')[0]
                        elif type(partner_name) in [int]:
                            partner_vat = str(partner_name).strip()
                        else:
                            partner_vat = partner_name.strip()
                        partner = self.env['res.partner'].search([('vat', '=', partner_vat)], limit=1)
                        if partner:
                            partner_id = partner.id
                    if not partner and partner_name:
                        partners+=str(partner_name)+' , '                        
#                         raise UserError(_("No partner found matching '%s'.") % partner_name)
            rowi += 1        
        if len(partners)>5:
            raise ValidationError(_('Харилцагч олдсонгүй %s ! ' % partners))  
                    
        nrows = sheet.nrows
        rowi = 1
        done_btl = self.env['account.bank.statement.line']
        analytic_obj = self.env['account.analytic.account']
        while rowi < nrows:
            partner_id = False
            cashflow_id = False
            account_id=False
            branch_id=False
            amount = 0.0
            row = sheet.row(rowi)
            print ('row[0].value ',row[0].value)
            dd=row[0].value
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
                
            name = row[1].value
            name_ref = row[9].value
            is_qpay = row[10].value
            try:
                partner_name = row[2].value
            except Exception:
                partner_name=''
            db_amount = row[3].value
            try:
                str_account_code =   row[4].value
            except Exception:
                str_account_code=''
            try:
                cashflow_type_name = row[5].value
            except Exception:
                cashflow_type_name=''

            try:
                branch_name = row[6].value
            except Exception:
                branch_name=''
                
            try:
                str_account_bank =   row[7].value
            except Exception:
                str_account_bank=''
            try:
                str_journal_account_code =   row[11].value
            except Exception:
                str_journal_account_code=''
#             if db_amount and cr_amount:
#                 raise ValidationError(_('Data error %s row! \n \
#                     Only one of Income and Expense columns \
#                     must have a value' % rowi))

            if type(str_account_code) in [float]:
                account_code = str(str_account_code).strip().split('.')[0]
            elif type(str_account_code) in [int]:
                account_code = str(str_account_code).strip()
            else:
                account_code = str_account_code.strip()
            if type(str_journal_account_code) in [float]:
                journal_account_code = str(str_journal_account_code).strip().split('.')[0]
            elif type(str_journal_account_code) in [int]:
                journal_account_code = str(str_journal_account_code).strip()
            else:
                journal_account_code = str_journal_account_code.strip()
                
            if type(str_account_bank) in [float]:
                account_bank = str(str_account_bank).strip().split('.')[0]
            elif type(str_account_bank) in [int]:
                account_bank = str(str_account_bank).strip()
            else:
                account_bank = str_account_bank.strip()                
            try:
                analytic_name = row[8].value
            except Exception:
                analytic_name=''

#             if db_amount:
            amount = db_amount
#             if cr_amount:
#                 amount = -cr_amount
#             print ('account_code ',account_code)
            analytic_code = row[8].value
            analytic_code = str(analytic_code).split('.')[0]
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
                    if analytic_id:
                        # analityc_lines.append({str(analytic_id.id):float(aa[1])})
                        analityc_lines[str(analytic_id.id)]=100
            print ('analityc_lines ',analityc_lines)
            partner = self.env['res.partner'].search([('name', '=', partner_name)], limit=1)
            if partner_name and len(str(partner_name))>1:
                if partner:
                    partner_id = partner.id
                else :
                    partner = self.env['res.partner'].search([('vat', '=', partner_name)], limit=1)
                    if partner:
                        partner_id = partner.id
                    else:
                        partner_vat=partner_name
                        if type(partner_name) in [float]:
                            partner_vat = str(partner_name).strip().split('.')[0]
                        elif type(partner_name) in [int]:
                            partner_vat = str(partner_name).strip()
                        else:
                            partner_vat = partner_name.strip()
                        partner = self.env['res.partner'].search([('vat', '=', partner_vat)], limit=1)
                        if partner:
                            partner_id = partner.id
                    if not partner and partner_name:
                        raise UserError(_("No partner found matching '%s'.") % partner_name)
                
            branch = self.env['res.branch'].search([('name', '=', branch_name)], limit=1)
            if branch:
                branch_id = branch.id

            account = self.env['account.account'].search([('code', '=', account_code)], limit=1)
            if account:
                account_id = account.id
            jr_account = self.env['account.account'].search([('code', '=', journal_account_code)], limit=1)
            if not jr_account:
                raise UserError(_("Тухайн данстай Харилцахын журнал олдсонгүй. L Харилцахын журналын үндсэн данс баганы өгөгдлийг шалгана уу!!!!"))
            journal = self.env['account.journal'].search([('default_account_id', '=', jr_account.id)])
            if not journal:
                raise UserError(_("Тухайн данстай Харилцахын журнал олдсонгүй.\
                 L Харилцахын журналын үндсэн данс баганы өгөгдлийг шалгана уу. Мөн журнал дээрх данс шалга!!!!{}" .format(jr_account.code)))
            else:
                journal_id = journal.id

            bank_account_id = False
            bank_account = self.env['res.partner.bank'].search([('acc_number', '=', account_bank)], limit=1)
            if bank_account:
                bank_account_id = bank_account.id


            if cashflow_type_name:
                cashflow = self.env['account.cash.move.type'].search([('name', '=', cashflow_type_name)], limit=1)
                if not cashflow:
                    raise UserError(_("No cashflow found matching '%s'.") % cashflow_type_name)
                cashflow_id = cashflow.id
            if not bank_account_id:
                partner_bank = self.env['res.partner.bank'].search([('partner_id', '=', partner_id)], limit=1)
                if partner_bank:
                    bank_account_id = partner_bank.id
            if name:
                if isinstance(name, float) or isinstance(name, int):
                    name=str(int(name))
            # analytic_id=False
            # if analytic_name:
            #     analytic = self.env['account.analytic.account'].search([('name', '=', analytic_name)], limit=1)
            #     if not analytic:
            #         if type(analytic_name) in [float]:
            #             analytic_name = str(analytic_name).strip().split('.')[0]
            #         elif type(analytic_name) in [int]:
            #             analytic_name = str(analytic_name).strip()
            #         else:
            #             analytic_name = analytic_name.strip()                       
            #         analytic = self.env['account.analytic.account'].search([('code', '=', analytic_name)], limit=1)
            #     if not analytic:
            #         raise UserError(_("No analytic account matching '%s'.") % analytic_name)
            #     analytic_id = analytic.id
            btl_line = self.env['account.bank.statement.line'].create({
                    'payment_ref': name or '/',
                    'bank_ref': name_ref or '/',
                    'amount': amount,
                    'partner_id': partner_id,
                    # 'statement_id': statement.id,
                    'date': date,
#                     'currency_id': statement.currency_id.id if statement.currency_id else False,
                    'cash_type_id': cashflow_id,
                    # 'sequence':start_sequence,
                    # 'bank_account_id':bank_account_id,
                    'account_id':account_id,
                    'journal_id':journal_id,
                    'branch_id':branch_id,
                    'analytic_distribution':analityc_lines,
                    # 'is_qpay':is_qpay
                })

            rowi += 1
            # start_sequence += 1
#         statement.onchan123124124124ge_balance_end()
            done_btl +=btl_line
        self.result = """
			<span>Импортолсон үр дүн</span><br/>
			<span>%s мөр импортлогдлоо.</span>
		"""%(len(done_btl))
        return {
			'name': 'Харилцахын гүйлгээ',
			'context': self._context,
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'account.bank.statement.import.file',
			'res_id': self.id,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}
    
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
        worksheet.write(row, 0, u"Огноо", header)
        worksheet.write(row, 1, u"Гүйлгээний утга", header)
        worksheet.write(row, 2, u"харилцагчийн ERP нэр", header)
        worksheet.write(row, 3, u"Дүн Орлого + Зарлага бол -", header)
        worksheet.write(row, 4, u"Дансны код", header)
        worksheet.write(row, 5, u"Мөнгөн гүйлгээний төрлийн нэр", header)
        worksheet.write(row, 6, u"Салбарын нэр ERP дээрх", header)
        worksheet.write(row, 7, u"Банкны данс", header)
        worksheet.write(row, 8, u"Шинжилгээний данс нэр", header)
        worksheet.write(row, 9, u"Банкны гүйлгээний утга", header)
        worksheet.write(row, 10, u"Шимтгэл эсэх TRUE, FALSE", header)
        worksheet.write(row, 11, u"Харилцахын журналын үндсэн данс ", header)
        
        # inch = 3000
        # worksheet.col(0).width = int(0.7*inch)
        # worksheet.col(1).width = int(0.7*inch)
        # worksheet.col(2).width = int(0.7*inch)

        workbook.close()

        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({
                                'data':out,
                                'name':self.id
        })
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=Хуулганы загвар" ,
             'target': 'new',
        }
class account_statement_import_invoice(models.TransientModel):
    """ Generate Entries by Account Bank Statement from Invoices """
    _name = "account.bank.statement.import.invoice"
    _description = "Import Invoice"

    account_invoices = fields.Many2many(
        'account.move', 'account_invoice_relation', 'invoice_id', 'invoice_line', 'Invoices')

    def populate_invoice(self):
        context = dict(self._context or {})
        statement_id = context.get('statement_id', False)
        if not statement_id:
            return {'type': 'ir.actions.act_window_close'}
        account_invoices = self.account_invoices
        if not account_invoices:
            return {'type': 'ir.actions.act_window_close'}

        statement_line_obj = self.env['account.bank.statement.line']
        move_line_obj = self.env['account.move.line']

        statement = self.env['account.bank.statement'].browse(statement_id)
        # for each selected move lines
        for line in self.account_invoices:
            bank_account_id = False
            ctx = context.copy()
            ctx['date'] = statement.date
            amount = 0.0
            count = 0
            reconcile = self.env['account.move.line.reconcile.writeoff'].search(
                [('writeoff_acc_id', '=', line.account_id.id)])
            move_line_id = move_line_obj.search(
                [('account_id', '=', line.account_id.id), ('invoice_id', '=', line.id)])  # , ('reconcile','=',False)
            if move_line_id:
                move_line = move_line_obj.browse(move_line_id.id)
                if line.type == 'out_refund' or line.type == 'in_invoice':
                    amount = -line.residual
                elif line.type == 'in_refund' or line.type == 'out_invoice':
                    amount = line.residual
                
                partner_bank = self.env['res.partner.bank'].search([('partner_id', '=', move_line.partner_id.id)], limit=1)
                if partner_bank:
                    bank_account_id = partner_bank.id
                    
                statement_line_obj.create({
                    'name': move_line.name or '?',
                    'amount': amount,
                    'partner_id': move_line.partner_id.id,
                    'bank_account_id': bank_account_id,
                    # 'statement_id': statement_id,
                    'ref': move_line.ref,
                    'date': statement.date,
                    'amount_currency': move_line.amount_currency,
                    'currency_id': move_line.currency_id.id,
                    'import_line_id': move_line.id,
                    'account_id': line.account_id.id,
                    'cashflow_id': False
                })
#         statement.onchange_balance_end()
        return {'type': 'ir.actions.act_window_close'}
