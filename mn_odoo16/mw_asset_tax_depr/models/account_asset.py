# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
from dateutil.relativedelta import relativedelta
from math import copysign
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, float_round
from datetime import date,datetime,timedelta
import logging
_logger = logging.getLogger(__name__)


class AccountAsset(models.Model):
    _inherit = 'account.asset'
    
    tax_value_total = fields.Float(compute='_amount_total_tax', method=True, digits=0, string='Total Value tax', store=True)
    tax_value_residual = fields.Float(compute='_amount_residual_tax', method=True, digits=0, string='Residual Value tax', store=True)
    tax_value_depreciation = fields.Float(compute='_amount_depreciation_tax', method=True, digits=0, string='Depreciation Value tax', store=True)

    depreciation_tax_line_ids = fields.One2many('account.asset.tax.depreciation.line', 'asset_id', string='Depreciation Lines tax', readonly=True, states={'draft': [('readonly', False)], 'open': [('readonly', False)]})

    #Эхний үлдэгдэл оруулах
    initial_depreciation_tax = fields.Float('Initial Depreciated Value',
                        help='At the time launching erp system you can set already depreciated amount of the previous financial period.')
#     account_move_line_ids = fields.One2many('account.move.line', 'asset_id', 'Entries', readonly=True)
#     location_id = fields.Many2one('account.asset.location', string='Asset Location')
#     purchase_date = fields.Date("Purchase date", )
    method_tax = fields.Selection([('linear', 'Linear'), ('degressive', 'Degressive')], string='Computation Method', required=True, readonly=True, states={'draft': [('readonly', False)]}, default='linear',
        help="Choose the method to use to compute the amount of depreciation lines.\n  * Linear: Calculated on basis of: Gross Value / Number of Depreciations\n"
            "  * Degressive: Calculated on basis of: Residual Value * Degressive Factor")
    method_number_tax = fields.Integer(string='Number of Depreciations', default=120, help="The number of depreciations needed to depreciate your asset")#readonly=True, states={'draft': [('readonly', False)]}, 
    method_period_tax = fields.Integer(string='Number of Months in a Period', required=True, readonly=True, default=1, states={'draft': [('readonly', False)]},
        help="The amount of time between two depreciations, in months")
    method_number_tax_conf = fields.Integer(string='Tax Number of Depreciations', default=120, help="The number of depreciations needed to depreciate your asset")#readonly=True, states={'draft': [('readonly', False)]}, 
    method_period_tax_conf = fields.Integer(string='Tax Number of Months in a Period', required=True, readonly=True, default=1, states={'draft': [('readonly', False)]},
        help="The amount of time between two depreciations, in months")
    method_end_tax = fields.Date(string='Ending Date', readonly=True, )#states={'draft': [('readonly', False)]}
    method_progress_factor_tax = fields.Float(string='Degressive Factor', readonly=True, default=0.3, states={'draft': [('readonly', False)]})
    method_time_tax = fields.Selection([('number', 'Number of Entries'), ('end', 'Ending Date')], string='Time Method', required=True, readonly=True, default='number', states={'draft': [('readonly', False)]},
        help="Choose the method to use to compute the dates and number of entries.\n"
             "  * Number of Entries: Fix the number of entries and the time between 2 depreciations.\n"
             "  * Ending Date: Choose the time between 2 depreciations and the date the depreciations won't go beyond.")
    prorata_tax = fields.Boolean(string='Prorata Temporis', readonly=True, states={'draft': [('readonly', False)]},
        help='Indicates that the first depreciation entry for this asset have to be done from the purchase date instead of the first January / Start date of fiscal year')

    value_other_tax = fields.Boolean(string='Other value tax?',)
    value_total_other = fields.Float(string='Other value',)

    tax_date = fields.Date("Tax date", default=lambda self: fields.Datetime.today())

    
    @api.depends('original_value', 'salvage_value', 'depreciation_tax_line_ids.move_check', 'depreciation_tax_line_ids.amount')#'account_move_ids.state',
    def _amount_depreciation_tax(self):
        '''
        '''
        for asset in self:
            total_amount = 0.0
            for line in asset.depreciation_tax_line_ids:
                if line.move_check:
                    total_amount += line.amount
            asset.tax_value_depreciation = total_amount
            
    
    @api.depends('original_value','value_total_other','value_other_tax', 'salvage_value', 'depreciation_tax_line_ids.move_check', 'depreciation_tax_line_ids.amount', 'original_move_line_ids')
    def _amount_total_tax(self):
        res={}
#         self.env.cr.execute("""SELECT
#                 a.id as id, SUM(abs(l.debit)) AS amount
#             FROM
#                 account_move_line l 
#                 left join account_move m on m.id=l.move_id
#                 left join account_invoice i on m.id=i.move_id
#                 left join account_asset_asset a on a.invoice_id=i.id
#             WHERE a.id = {0} and m.state='posted'
#             AND l.move_id not in (select move_id from account_asset_depreciation_line where move_id notnull) GROUP BY a.id""".format(str(self.id)))
#         res=dict(self.env.cr.fetchall())
#         self.value_total = res.get(self.id, 0.0)
        print ('123')
        for asset in self:
            if not asset.value_other_tax:
                asset.tax_value_total = asset.original_value# + asset.value_writeup+asset.value_revaluation#+self.value_revaluation_depr
            else:
                asset.tax_value_total=asset.value_total_other
#         self.tax_value_total = self.value


    
    @api.depends('original_value','tax_value_total','value_total_other','value_other_tax', 'salvage_value', 'depreciation_tax_line_ids.move_check', \
                 'depreciation_tax_line_ids.amount', 'tax_value_depreciation',\
                 )#account_move_ids.state 'history_ids','state'
    def _amount_residual_tax(self):
        '''
        self.value -> self.value + self.value_writeup
        Акталсан бол хасч харуулах
        '''
        for asset in self:
            residual = round(asset.tax_value_total  - asset.tax_value_depreciation,2)
            print ('self.tax_value_total====: ',asset.tax_value_total)
            asset.tax_value_residual = residual

    
    def compute_tax_depreciation_board_all(self):
        for asset in self:
            if asset.initial_depreciation_tax:
                asset.compute_initial_tax_depreciation()
                asset.with_context(ini=True).compute_tax_depreciation_board()
            else:
                asset.compute_tax_depreciation_board()
        return True


    
    def compute_tax_depreciation_board_all_assets(self):
#         assets = self.env['account.asset'].search([])
        print ('assets ',self)
        self.compute_tax_depreciation_board_all()

    def _compute_tax_board_undone_dotation_nb(self, depreciation_date, total_days):
        undone_dotation_number = self.method_number_tax
        if self.method_time_tax == 'end':
            end_date = datetime.strptime(self.method_end_tax, DF).date()
            undone_dotation_number = 0
            while depreciation_date <= end_date:
                depreciation_date = date(depreciation_date.year, depreciation_date.month, depreciation_date.day) + relativedelta(months=+self.method_period_tax)
                undone_dotation_number += 1
        # if self.prorata:
        #     undone_dotation_number += 1
        return undone_dotation_number
        
    def last_day_of_month(self, date):
#         Тухайн огноонооны сарын сүүлчийн өдрийн огноог буцаах
        next_month = date.replace(day=28) + timedelta(days=4)  # this will never fail
        return next_month - timedelta(days=next_month.day)
        
    def compute_tax_depreciation_board(self):
#         Элэгдлийн самбарыг тооцоолохдоо хөрөнгийн огноогоор тооцоолон өдрөөр элэгдэл бодож самбар байгуулах
        '''                    #amount_to_depr = residual_amount - amount
        '''
        self.ensure_one()
        move = False
        posted_depreciation_tax_line_ids = self.depreciation_tax_line_ids.filtered(lambda x: x.move_check).sorted(key=lambda l: l.depreciation_date)
        unposted_depreciation_tax_line_ids = self.depreciation_tax_line_ids.filtered(lambda x: not x.move_check)
        print ('unposted_depreciation_tax_line_ids ',unposted_depreciation_tax_line_ids)
        # Remove old unposted depreciation lines. We cannot use unlink() with One2many field
        commands = [(2, line_id.id, False) for line_id in unposted_depreciation_tax_line_ids]
        d_date=self.first_depreciation_date
        
        if self.tax_value_residual != 0.0:
#             amount_to_depr = residual_amount = check_residual_amount = self.value_residual
            residual_amount = check_residual_amount = self.tax_value_residual
            amount_to_depr = self.tax_value_total
            
            if self.prorata_tax:
                # if we already have some previous validated entries, starting date is last entry + method perio
                if posted_depreciation_tax_line_ids and posted_depreciation_tax_line_ids[-1].depreciation_date:
                    last_depreciation_date = datetime.strptime(posted_depreciation_tax_line_ids[-1].depreciation_date, DF).date()
                    depreciation_date = last_depreciation_date + relativedelta(months=+self.method_period_tax)
                else:
                    depreciation_date = datetime.strptime(self._get_last_depreciation_date()[self.id], DF).date()
            else:
                # depreciation_date = 1st of January of purchase year if annual valuation, 1st of
                # purchase month in other cases
                if self.tax_date:
                    d_date=self.tax_date
                if self.method_period_tax >= 12:
                    asset_date = datetime.strptime(str(d_date.year) + '-01-01', DF).date()
                else:
                    asset_date = datetime.strptime(str(d_date.year)+'-'+str(d_date.month) + '-01', DF).date()
                # if we already have some previous validated entries, starting date isn't 1st January but last entry + method period
                if posted_depreciation_tax_line_ids and posted_depreciation_tax_line_ids[-1].depreciation_date:
                    last_depreciation_date = datetime.strptime(posted_depreciation_tax_line_ids[-1].depreciation_date, DF).date()
                    depreciation_date = last_depreciation_date + relativedelta(months=+self.method_period_tax)
                else:
                    depreciation_date = asset_date
            print ('asset_date ',asset_date)
            print ('depreciation_date1 ',depreciation_date)
                    
            # Эхлэлийн элэгдлийн дугаарлалтаас эхлэхгүй, аль хэдийнэ compute_initial_depreciation функцээр үүсгэгдсэн нөгөөтэйгүүр батлагдсан бичилтүүдийг тооны дараагийн тооноос эхлэх
            start = len(posted_depreciation_tax_line_ids)+1
            initial_depr = 0
            if unposted_depreciation_tax_line_ids.filtered(lambda x: x.initial_depreciation_tax_check):
                start -= len(unposted_depreciation_tax_line_ids.filtered(lambda x: x.initial_depreciation_tax_check and not x.move_check))
                initial_depr = self.initial_depreciation_tax
                print ('unposted_depreciation_tax_line_ids ',unposted_depreciation_tax_line_ids)
                depreciation_date = datetime.strptime(unposted_depreciation_tax_line_ids.filtered(lambda x: x.initial_depreciation_tax_check and not x.move_check)[0].depreciation_date, '%Y-%m-%d').date()
                print ('depreciation_date23 ',depreciation_date)
            else:   
                # Эхлэлийн элэгдэл нь тухайн өдрөөс элэгдүүлэхгүй тохиолдолд сарын сүүлийн өдрөөс байх
                #Өмнө нь элэгдсэн самбарууд байгаа бол шаардлагагүй
                if not self.prorata_tax and not posted_depreciation_tax_line_ids:
                    depreciation_date = self.last_day_of_month(depreciation_date)
                    print ('depreciation_date2 ',depreciation_date)
            day = depreciation_date.day
            month = depreciation_date.month
            year = depreciation_date.year
            total_days = (year % 4) and 365 or 366
            undone_dotation_number = self._compute_tax_board_undone_dotation_nb(depreciation_date, total_days)
            # Нийт мөрийн тоог хадгалж аваад үлдэгдэлийг шууд утга онооход ашиглана
            lines = undone_dotation_number
            stop=False
            sequence=start
 #           print 'depreciation_date ',depreciation_date
#            print 'sequence-----------: ',sequence
            _logger.info('compute_tax_depreciation_board--------------- id (%s).', self.id)  
            while residual_amount>0:
#                 amount=
                print ('residual_amount ',residual_amount)
#                 print 'amount_to_depr111000 ',amount_to_depr
                
#                 print 'sequence ',sequence
                print ('d_date ',d_date)
                if sequence != 0:
                    # Хөрөнгө хааж байгаа үед хаалтын огнооноос хамаарч элэгдлийн бичилтийн дүнг шинэчлэх
                    if 'date' in self._context and 'original_value' in self._context and not move:
                        dates = datetime.strptime(self._context.get('date'), '%Y-%m-%d')
                        d_lines = self.env['account.asset.tax.depreciation.line'].search([('asset_id','=',self.id),('depreciation_date','<',dates.date()),
                                                                            ('move_check','=',False)])
                        if d_lines:
                            raise UserError(_('Validate depreciation lines before %s closing date!' % dates.date()))
                        amount = self._context.get('value')
                        if type(depreciation_date) is not type(dates):
                            dates = dates.date()
                        if depreciation_date >= dates:
                            depreciation_date = dates
#                             amount_to_depr = residual_amount - amount
#                             undone_dotation_number -= 1
                            move = True
                        print ('amount_to_depr2 ',amount_to_depr)
                    # Элэгдлийн бичилтийн огноо болон хөрөнгийн огнооны өдрөөс хамааруулж өдрөөр элэгдүүлийн дүнг тооцоолох
                    elif sequence == 1 and not self.prorata_tax and month == d_date.month and d_date.day != 1:
                        days = (depreciation_date - d_date).days
                        division = undone_dotation_number+1-start
                        if division!=0:
                            monthly_depreciate = residual_amount / division
                            daily_depreciate = monthly_depreciate / depreciation_date.day
                            print ('daily_depreciate ',daily_depreciate)
                            print ('days ',days)
                            
                            amount = daily_depreciate * days
                        else:
                            _logger.info('compute_tax_depreciation_board--------------- asset skip (%s).', self)  
                            amount=0
                            break
#                             continue
#                             raise UserError((u'Хөрөнгө дээр 0 д хуваах үйлдэл хийх гэж байна %s !' % self.name))
                            
#                         amount_to_depr = residual_amount - amount
#                         undone_dotation_number -= 1
#                         print 'amount_to_depr3 ',amount_to_depr
                    else: 
#                         print 'amount_to_depr ',amount_to_depr

#                         amount = self._compute_board_amount(sequence, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_tax_line_ids.ids, total_days, depreciation_date, lines)
                        amount=amount_to_depr/self.method_number_tax
#                     print ('amount-- ',amount)
                    amount = self.currency_id.round(amount)
#                     print ('amount3 ',amount)
                    
#                     if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
#                         continue
                else:
                    amount = initial_depr 
#                     amount_to_depr = residual_amount - amount
#                     print 'amount_to_depr ',amount_to_depr
                print ('amount ',amount)
                residual_amount_prev = residual_amount
                if residual_amount >= amount:
                    residual_amount -= amount
                else:
                    residual_amount = 0
                print ('depreciation_date ',depreciation_date)
                if not stop:
                    if residual_amount == 0:
                        stop = True
                        amount = residual_amount_prev
                    vals = {
                        'amount': amount,
                        'asset_id': self.id,
                        'sequence': sequence,
                        'name': (self.code or '') + '/' + str(sequence),
                        'remaining_value': abs(residual_amount),
                        'depreciated_value': (self.tax_value_total - self.salvage_value) - (residual_amount + amount),
                        'depreciation_date': depreciation_date.strftime(DF),
                    }
                else:
                    break
                if sequence == 0:
                    vals = {
                        'amount': amount,
                        'asset_id': self.id,
                        'sequence': sequence,
                        'name': (self.code or '') + '/' + str(sequence),
                        'remaining_value': abs(residual_amount),
                        'depreciated_value': (self.tax_value_total - self.salvage_value) - (residual_amount + amount),
                        'depreciation_date': depreciation_date.strftime(DF),
                        'initial_depreciation_tax_check': True,
                    }
                commands.append((0, False, vals))
                # Considering Depr. Period as months
                depreciation_date = date(year, month, day) + relativedelta(months=+self.method_period_tax)
                print ('depreciation_date2 ',depreciation_date)
                depreciation_date = self.last_day_of_month(depreciation_date)
                day = depreciation_date.day
                month = depreciation_date.month
                year = depreciation_date.year
                sequence+=1
                _logger.info('compute_tax_depreciation_board--------------- sequence (%s).', sequence)  
                
#                print 'depreciation_date4 ',depreciation_date
        self.with_context(from_tax=True).write({'depreciation_tax_line_ids': commands})
        if move:
            line = self.depreciation_tax_line_ids.search([('depreciation_date','>=',self._context.get('date'))], order='depreciation_date ASC', limit=1)
            line.create_move()
        return True
        
    
    def compute_initial_tax_depreciation(self, context=None):
        if context is None:
            context = self._context or {}
#       Хэрэв элэгдлийн эхний дүн байвал тухайн дүнгээр эдэгдэл үүснэ
        currency_obj = self.env.get('res.currency')
        commands = []
        initial_depreciation_tax_line_ids = self.depreciation_tax_line_ids.filtered(lambda x: x.initial_depreciation_tax_check)
        if initial_depreciation_tax_line_ids:
            commands = [(2, line_id.id, False) for line_id in initial_depreciation_tax_line_ids]
        for asset in self:
            entry_date = context.get('entry_date', asset.tax_date and asset.tax_date or asset.date)
#             year = datetime.strptime(entry_date, '%Y-%m-%d').year
#           Хөрөнгийн ангилал дах хөрөнгийн дансны currency-г авах
            current_currency = asset.currency_id.id 
#             depreciation_amount = currency_obj.compute_currency(current_currency, asset.company_id.currency_id.id, asset.initial_depreciation)
#             asset_amount = currency_obj.compute_currency(current_currency, asset.company_id.currency_id.id, asset.value)
            depreciation_amount = asset.initial_depreciation_tax
            asset_amount = asset.value
            vals = {
                'amount': depreciation_amount,
                'asset_id': asset.id,
                'sequence': 0,
                'name': u'%s өмнөх элэгдэл ' % asset.name,
                'remaining_value': asset_amount - depreciation_amount,
                'depreciated_value': 0,
                'depreciation_date': entry_date,
                'initial_depreciation_tax_check': True,
            }
            commands.append((0, False, vals))
            self.with_context(from_tax=True).write({'depreciation_tax_line_ids': commands})
#             self.compute_depreciation_board()
        return True
    
    
#     @api.model # Бол  File "/Users/darmaa/workspace/mn_odoo13/mw_asset/models/account_asset.py", line 246, in _check_original_many_move_line_ids ЭНД ҮҮССЭН ГЭСЭН АНХААРУУЛГА ГАРАХ
    @api.model_create_multi
    def create(self, vals):
        with self.env.norecompute():
            new_recs = super(AccountAsset, self.with_context(mail_create_nolog=True)).create(vals)
#             print ('new_recs ',new_recs)
#         new_recs.filtered(lambda r: r.state != 'model')._set_value()
#         return new_recs        
#         asset = super(AccountAsset, self).with_context(mail_create_nolog=True).create(vals)#
#         Элэгдэлийн эхний дүн байвал элэгдэлийн самбарт үүсгэнэ
        new_recs.compute_tax_depreciation_board_all()
#         if asset.initial_depreciation_tax:
#             asset.compute_initial_depreciation_tax()
        return new_recs
    
    
    def write(self, vals):
#         print ('vals1',vals)
#         Элэгдэлийн эхний дүн байвал элэгдэлийн самбарт үүсгэнэ
        if vals.get('initial_depreciation_tax'):
#             print 'vals',vals
            self.compute_initial_tax_depreciation()
        if vals.get('tax_value_total') or vals.get('tax_value_residual'):        
            self.compute_tax_depreciation_board()
        return super(AccountAsset, self).write(vals)
    @api.onchange('model_id')
    def _onchange_model_id(self):
        model = self.model_id
        if model:
            self.method = model.method
            self.method_number = model.method_number
            self.method_period = model.method_period
            self.method_progress_factor = model.method_progress_factor
            self.prorata_computation_type = model.prorata_computation_type
            self.analytic_distribution = model.analytic_distribution or self.analytic_distribution
            self.account_depreciation_id = model.account_depreciation_id
            self.account_depreciation_expense_id = model.account_depreciation_expense_id
            self.journal_id = model.journal_id
            self.method_number_tax = model.method_number_tax_conf
            self.method_period_tax = model.method_period_tax_conf

class AccountAssetTaxDepreciationLine(models.Model):
    _name = 'account.asset.tax.depreciation.line'
    _description = 'Asset depreciation line'

    name = fields.Char(string='Depreciation Name', required=True, index=True)
    sequence = fields.Integer(required=True)
    asset_id = fields.Many2one('account.asset', string='Asset', required=True, ondelete='cascade')
    parent_state = fields.Selection(related='asset_id.state', string='State of Asset')
    amount = fields.Float(string='Current Depreciation', digits=0, required=True)
    remaining_value = fields.Float(string='Next Period Depreciation', digits=0, required=True)
    depreciated_value = fields.Float(string='Cumulative Depreciation', required=True)
    depreciation_date = fields.Date('Depreciation Date', index=True)
#     move_id = fields.Many2one('account.move', string='Depreciation Entry')
    move_check = fields.Boolean(string='Linked')
#     move_posted_check = fields.Boolean(compute='_get_move_posted_check', string='Posted', store=True)
    initial_depreciation_tax_check = fields.Boolean(string='Initial depreciation', default=False)

#     
#     @api.depends('move_id')
#     def _get_move_check(self):
#         for line in self:
#             line.move_check = bool(line.move_id)

    
    @api.depends('move_id.state')
    def _get_move_posted_check(self):
        for line in self:
            line.move_posted_check = True if line.move_id and line.move_id.state == 'posted' else False

    
    def create_move(self, post_move=True):
        created_moves = self.env['account.move']
        prec = self.env['decimal.precision'].precision_get('Account')
        for line in self:
            if not line.move_check:
                line.move_check=True


