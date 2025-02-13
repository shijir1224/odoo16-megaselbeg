# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import base64
import xlrd
from tempfile import NamedTemporaryFile
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.modules.module import get_module_resource

class AccountBudgetImportFile(models.TransientModel):
    _name = 'account.budget.import.file'
    _description = "Import File"
    
    @api.model
    def _default_image(self):
        image_path = get_module_resource('mw_account_budget', 'static/img', 'demo.png')
        return base64.b64encode(open(image_path, 'rb').read())
    

    data_file = fields.Binary(string='Bank Statement File', required=True, help='Get you bank statements in electronic format from your bank and select them here.')
    image_1920 = fields.Image(default=_default_image)

    desc = fields.Text('Template', default="""# A Огноо 2020-02-10 загвартай байна
# B Гүйлгээний утга
# C харилцагчийн ERP нэр
# D Дүн Орлого + Зарлага бол -
# E Дансны код 
# F Мөнгөн гүйлгээний төрлийн нэр
# G Салбарын нэр ERP дээрх
# H Банкны данс
# I Шинжилгээний данс нэр""", readonly=True)
    


    def create_lines(self, interval=1):
        period_line_obj = self.env['mw.account.budget.period.line']
        line_obj = self.env['mw.account.budget.line']
        period_line_line_obj = self.env['mw.account.budget.period.line.line']
        
        month = interval
        if self.type=='season':
            month=3
        for b in self:
            for conf in b.conf_id.line_ids:
                line=line_obj.create({
                    'description': conf.name,
                    'date_from': b.date_from,
                    'date_to': b.date_to,
                    'conf_line_id': conf.id,
                    'parent_id': b.id,
                })                
    
                for cl in conf.item_ids:
                    period_line=period_line_obj.create({
                        'name': conf.name,
                        'date_from': b.date_from,
                        'date_to': b.date_to,
                        'items_id': cl.id,
                        'parent_line_id': line.id,
                    })                                        
                    ds = b.date_from
        #             while ds.strftime('%Y-%m-%d') < fy.date_to:
                    while ds < b.date_to:
                        de = ds + relativedelta(months=month, days=-1)
        #                 if de.strftime('%Y-%m-%d') > fy.date_to:
                        if de > b.date_to:
        #                     de = datetime.strptime(fy.date_to, '%Y-%m-%d')
                            de = b.date_to
        
                        period_line_line_obj.create({
                            'name': ds.strftime('%m/%Y'),
                            'date_from': ds.strftime('%Y-%m-%d'),
                            'date_to': de.strftime('%Y-%m-%d'),
                            'period_line_id': period_line.id,
                        })
                        ds = ds + relativedelta(months=month)
        return True
    

    def import_file(self):
        context = self._context
        statement=None
        
        
        if context.get('active_model') == 'mw.account.budget' and context.get('active_ids'):
            statement = self.env['mw.account.budget'].browse(context['active_ids'])[0]
        if not statement:
            raise UserError(_("No active statement!"))
            
            
        try:
            fileobj = NamedTemporaryFile('w+b')
            fileobj.write(base64.decodebytes(self.data_file))
            fileobj.seek(0)
            book = xlrd.open_workbook(fileobj.name)
        except ValueError:
            raise UserError(
                _('Error loading data file. \ Please try again!'))
        
        start_sequence = 1
        print ('statement ',statement)
#         last_statment_line = self.env['account.budget.line'].search([('statement_id', '=', statement.id)], order='sequence desc', limit=1)
#         if last_statment_line:
#             start_sequence = last_statment_line.sequence+1

        sheet = book.sheet_by_index(0)
        nrows = sheet.nrows
        start_row=1
        rowidex=1
        while rowidex < nrows:
            partner_id = False
            cashflow_id = False
            account_id=False
            branch_id=False
            amount = 0.0
            row = sheet.row(rowidex)
            print ('rowi ',rowidex)
            print ('row[0].value ',row[0].value)
            print ('row[1].value ',row[1].value)
            if row[3].value==u'Төсвийн зориулалт':
                start_row=rowidex+1
                break
            rowidex += 1
        period_line_obj = self.env['mw.account.budget.period.line']
        line_obj = self.env['mw.account.budget.line']
        period_line_line_obj = self.env['mw.account.budget.period.line.line']
        
        item_obj = self.env['mw.account.budget.items']
            
        print ('start_row ',start_row)
        rowi = start_row
        line=False
        period_line=False
        month=1
        while rowi < nrows:
            partner_id = False
            cashflow_id = False
            account_id=False
            branch_id=False
            amount = 0.0
            row = sheet.row(rowi)
#             print ('rowi ',rowi)
#             print ('row[0].value ',row[0].value)
#             print ('row[1].value ',row[1].value)
            dd=row[0].value
            if row[0].value:
                line=line_obj.create({
                    'name': row[3].value,
                    'code': row[2].value,
                    'description': row[5].value,
#                     'date_from': statement.date_from,
#                     'date_to': statement.date_to,
#                     'conf_line_id': conf.id,
                    'parent_id': statement.id,
                })                                
            if line and not row[0].value and row[1].value:
                item_id=False
                if row[3].value:
                    item = item_obj.search([('name', '=', row[3].value)], limit=1)
                    if not item:
                        item=item_obj.create({'code':row[2].value,
                                              'name':row[3].value})
#                         raise UserError(_("No cashflow found matching '%s'.") % row[5].value)
                    item_id = item.id
                    
                    period_line=period_line_obj.create({
                        'name': row[3].value,
                        'code': row[2].value,
#                         'date_from': statement.date_from,
#                         'date_to': statement.date_to,
                        'items_id': item_id,
                        'parent_line_id': line.id,
                    })              
            if line and period_line and not row[0].value and not row[1].value:
                if row[2].value:
                    period_line_line_obj.create({
                        'name': row[3].value,
                        'code': row[2].value,
                        'period_line_id': period_line.id,
                        'budget_01' : row[9].value ,
                        'budget_02' : row[10].value ,
                        'budget_03' : row[11].value ,
                        'budget_04' : row[12].value ,
                        'budget_05' : row[13].value ,
                        'budget_06' : row[14].value ,
                        'budget_07' : row[15].value ,
                        'budget_08' : row[16].value ,
                        'budget_09' : row[17].value ,
                        'budget_10' : row[18].value ,
                        'budget_11' : row[19].value ,
                        'budget_12' : row[20].value ,                        
                    })                                  
#                     ds = statement.date_from
#                     i=11
#                     while ds < statement.date_to:
#                         amount=0
# #                         print ('row[i].value ',row[i].value)
#                         if type(row[i].value)==float:
#                             amount=row[i].value
#                         de = ds + relativedelta(months=month, days=-1)
#         #                 if de.strftime('%Y-%m-%d') > fy.date_to:
#                         if de > statement.date_to:
#         #                     de = datetime.strptime(fy.date_to, '%Y-%m-%d')
#                             de = statement.date_to
#         
#                         period_line_line_obj.create({
#                             'name': ds.strftime('%m/%Y'),
#                             'date_from': ds.strftime('%Y-%m-%d'),
#                             'date_to': de.strftime('%Y-%m-%d'),
#                             'period_line_id': period_line.id,
#                             'budget_amount':amount
#                         })
#                         i+=1
#                         ds = ds + relativedelta(months=month)                

            rowi += 1
            start_sequence += 1
#         statement.onchange_balance_end()
        return True
        
    def import_file_date(self):
        context = self._context
        statement=None
        
        
        if context.get('active_model') == 'mw.account.budget' and context.get('active_ids'):
            statement = self.env['mw.account.budget'].browse(context['active_ids'])[0]
        if not statement:
            raise UserError(_("No active statement!"))
            
            
        try:
            fileobj = NamedTemporaryFile('w+b')
            fileobj.write(base64.decodebytes(self.data_file))
            fileobj.seek(0)
            book = xlrd.open_workbook(fileobj.name)
        except ValueError:
            raise UserError(
                _('Error loading data file. \ Please try again!'))
        
        start_sequence = 1
        print ('statement ',statement)
#         last_statment_line = self.env['account.budget.line'].search([('statement_id', '=', statement.id)], order='sequence desc', limit=1)
#         if last_statment_line:
#             start_sequence = last_statment_line.sequence+1

        sheet = book.sheet_by_index(0)
        nrows = sheet.nrows
        start_row=1
        rowidex=1
        while rowidex < nrows:
            partner_id = False
            cashflow_id = False
            account_id=False
            branch_id=False
            amount = 0.0
            row = sheet.row(rowidex)
            print ('rowi ',rowidex)
            print ('row[0].value ',row[0].value)
            print ('row[1].value ',row[1].value)
            if row[1].value==u'Төсвийн утга':
                start_row=rowidex+1
                break
            rowidex += 1
        period_line_obj = self.env['mw.account.budget.period.line']
        line_obj = self.env['mw.account.budget.line']
        period_line_line_obj = self.env['mw.account.budget.period.line.line']
        
        item_obj = self.env['mw.account.budget.items']
            
        print ('start_row ',start_row)
        rowi = start_row
        line=False
        month=1
        while rowi < nrows:
            partner_id = False
            cashflow_id = False
            account_id=False
            branch_id=False
            amount = 0.0
            row = sheet.row(rowi)
#             print ('rowi ',rowi)
#             print ('row[0].value ',row[0].value)
#             print ('row[1].value ',row[1].value)
            dd=row[0].value
            if row[0].value:
                line=line_obj.create({
                    'name': row[5].value,
                    'description': row[5].value,
                    'date_from': statement.date_from,
                    'date_to': statement.date_to,
#                     'conf_line_id': conf.id,
                    'parent_id': statement.id,
                })                                
#             try:
#                 if type(dd)==float:
#                     serial = dd
#                     seconds = (serial - 25569) * 86400.0
#                     date=datetime.utcfromtimestamp(seconds)
#                 else:
#                     date = datetime.strptime(dd, '%Y-%m-%d')
#             except ValueError:
#                 raise ValidationError(_('Date error %s row! \n \
#                 format must \'YYYY-mm-dd\'' % rowi))
            if line and not row[0].value:
                item_id=False
                if row[5].value:
                    item = item_obj.search([('name', '=', row[5].value)], limit=1)
                    if not item:
                        item=item_obj.create({'code':row[3].value,
                                              'name':row[5].value})
#                         raise UserError(_("No cashflow found matching '%s'.") % row[5].value)
                    item_id = item.id
                    
                    period_line=period_line_obj.create({
                        'name': row[5].value,
                        'date_from': statement.date_from,
                        'date_to': statement.date_to,
                        'items_id': item_id,
                        'parent_line_id': line.id,
                    })              
                    ds = statement.date_from
        #             while ds.strftime('%Y-%m-%d') < fy.date_to:
                    i=11
                    while ds < statement.date_to:
                        amount=0
#                         print ('row[i].value ',row[i].value)
                        if type(row[i].value)==float:
                            amount=row[i].value
                        de = ds + relativedelta(months=month, days=-1)
        #                 if de.strftime('%Y-%m-%d') > fy.date_to:
                        if de > statement.date_to:
        #                     de = datetime.strptime(fy.date_to, '%Y-%m-%d')
                            de = statement.date_to
        
                        period_line_line_obj.create({
                            'name': ds.strftime('%m/%Y'),
                            'date_from': ds.strftime('%Y-%m-%d'),
                            'date_to': de.strftime('%Y-%m-%d'),
                            'period_line_id': period_line.id,
                            'budget_amount':amount
                        })
                        i+=1
                        ds = ds + relativedelta(months=month)                
            rowi += 1
            start_sequence += 1
#         statement.onchange_balance_end()
        return True
