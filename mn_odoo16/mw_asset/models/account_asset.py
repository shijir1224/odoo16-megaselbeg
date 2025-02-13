# -*- coding: utf-8 -*-
import calendar
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from calendar import monthrange
from odoo import fields, models, api, _
from odoo.tools import float_compare, float_is_zero, formatLang, end_of
from odoo.exceptions import ValidationError, UserError
from math import copysign
from odoo.osv import expression
# from odoo.exceptions import UserError
DAYS_PER_MONTH = 30
DAYS_PER_YEAR = DAYS_PER_MONTH * 12


class AccountAsset(models.Model):
    _inherit = "account.asset"
    _description = "Үндсэн хөрөнгө"
    rec_name = 'display_name'


    original_move_line_ids = fields.Many2many('account.move.line', 'asset_move_line_rel', 'asset_id', 'line_id', string='Journal Items', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    close_status = fields.Selection([('not_state', ' '), ('dispose', 'Актласан'), ('sell', 'Борлуулсан')], string='Хаасан төлөв', readonly=True, default='not_state')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    code = fields.Char(
        string="Хөрөнгийн код",
        size=32,
        tracking=True,
    )
    branch_id = fields.Many2one("res.branch", string="Салбар")
    owner_id = fields.Many2one(
        "res.partner",
        "Эзэмшигч",
        domain=[("employee", "=", True)],)
    first_depreciation_date = fields.Date(string='First Depreciation Date')
    owner_department_id = fields.Many2one("hr.department", "Хэлтэс")
    by_day = fields.Boolean("Full capital is", default=False)
    barcode = fields.Char(string="Зураасан код")
    location_id = fields.Many2one("account.asset.location", string="Байрлал")
    image = fields.Binary(string="Зураг")
    asset_type_id = fields.Many2one('account.asset.type', string="Хөрөнгийн төрөл", store=True)
    capital_value = fields.Monetary(string="Капиталын өртөг")
    revaluation_value = fields.Monetary(string="Дахин үнэлгээний өртөг")
    # original_value = fields.Monetary(string="Нийт өртөг", compute='compute_initial_value', store=True)
    initial_value = fields.Monetary(string="Анхны өртөг", store=True)
    partner_id =fields.Many2one('res.partner', string='Нийлүүлэгч')
    invoice_id =fields.Many2one('account.move', string='Нэхэмжлэх')
    move_count = fields.Integer(string='Шилжүүлэг', compute='_move_count', store=True)
    is_initial_derp = fields.Boolean(string='Эхний үлдэгдэлтэй?', )
    initial_derp = fields.Float(string='ХЭ Эхний үлдэгдэл', )
    initial_account =fields.Many2one('account.account', 'initial account')
    serial = fields.Char('serial')
    value_residual = fields.Monetary(string='Үлдэгдэл өртөг', compute='_compute_value_residual')
    old_code = fields.Char(string="Хуучин код")
    car_number = fields.Char(string='Машины дугаар', tracking=True)
    car_vat = fields.Char(string='Арлын дугаар', tracking=True)
    car_color = fields.Char(string='Өнгө', tracking=True)
    collateral = fields.Boolean(string ='Барьцаанд байгаа эсэх')
    collateral_partner = fields.Many2one('res.partner', string="Банк")
    debug_analytic_account = fields.Many2one('account.analytic.account', string="Debug analytic")
    asset_depreciated_value_amount = fields.Float(string='Элэгдсэн өртөг', store=True, compute='onchnage_asset_depreciated_value_amount')

    @api.depends('original_value','book_value','capital_value')
    def onchnage_asset_depreciated_value_amount(self):
        for item in self:
            if item.original_value:
                item.asset_depreciated_value_amount = item.original_value+item.capital_value-item.book_value
    def _compute_value_residual(self):
        for record in self:
            posted_depreciation_moves = record.depreciation_move_ids.filtered(lambda mv: mv.state == 'posted')
            record.value_residual = (
                record.original_value
                - record.salvage_value
                - record.already_depreciated_amount_import
                + record.capital_value
                - sum(posted_depreciation_moves.mapped('depreciation_value'))
            )

    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = args or []
    #     domain = []
    #     if self.name and self.code:
    #         domain = ['|', ('name','ilike',self), ('code','=like',(self)+'%')]
    #         if operator in expression.NEGATIVE_TERM_OPERATORS:
    #             domain = ['&', '!'] + domain[1:]
    #     return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
    def _recompute_board(self):
        self.ensure_one()
        # All depreciation moves that are posted
        posted_depreciation_move_ids = self.depreciation_move_ids.filtered(
            lambda mv: mv.state == 'posted' and not mv.asset_value_change
        ).sorted(key=lambda mv: (mv.date, mv.id))

        imported_amount = self.already_depreciated_amount_import
        residual_amount = self.value_residual
        # print('residual_amount',residual_amount)
        if not posted_depreciation_move_ids:
            residual_amount += imported_amount
        residual_declining = residual_amount
        # print ('posted_depreciation_move_ids === ',posted_depreciation_move_ids)
        # Days already depreciated
        days_already_depreciated = sum(posted_depreciation_move_ids.mapped('asset_number_days'))
        days_left_to_depreciated = self.asset_lifetime_days - days_already_depreciated
        days_already_added = sum([(mv.date - mv.asset_depreciation_beginning_date).days + 1 for mv in posted_depreciation_move_ids])
        # print('sssss',days_already_added)
        start_depreciation_date = self.paused_prorata_date + relativedelta(days=days_already_added)
        # print('safggawsgsagsagsagsa121421',start_depreciation_date)
        final_depreciation_date = self.paused_prorata_date + relativedelta(months=int(self.method_period) * self.method_number, days=-1)
        final_depreciation_date = self._get_end_period_date(final_depreciation_date)

        depreciation_move_values = []
        init=1
        if not float_is_zero(self.value_residual, precision_rounding=self.currency_id.rounding):
            while days_already_depreciated < self.asset_lifetime_days:
                period_end_depreciation_date = self._get_end_period_date(start_depreciation_date)
                print('set111: ', period_end_depreciation_date)
                period_end_fiscalyear_date = self.company_id.compute_fiscalyear_dates(period_end_depreciation_date).get('date_to')

                days, amount = self._compute_board_amount(residual_amount, start_depreciation_date, period_end_depreciation_date, days_already_depreciated, days_left_to_depreciated, residual_declining,init=init)
                residual_amount -= amount
                print('1212412a,pimt',amount )
                init+=1
                # start_depreciation_date = self.paused_prorata_date + relativedelta(days=days_already_added)
                if not posted_depreciation_move_ids:
                    # print(s)
                    # self.already_depreciated_amount_import management.
                    # Subtracts the imported amount from the first depreciation moves until we reach it
                    # (might skip several depreciation entries)
                    if abs(imported_amount) <= abs(amount):
                        amount -= imported_amount
                        imported_amount = 0
                    else:
                        imported_amount -= amount
                        amount = 0

                if self.method == 'degressive_then_linear' and final_depreciation_date < period_end_depreciation_date:
                    period_end_depreciation_date = final_depreciation_date
                    print('set222: ', period_end_depreciation_date)

                if not float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    # For deferred revenues, we should invert the amounts.
                    if self.asset_type == 'sale':
                        amount *= -1
                    # print('safggawsgsagsagsagsa',period_end_depreciation_date)
                    print('amount:', amount, float_is_zero(amount, precision_rounding=self.currency_id.rounding), self.currency_id.rounding)
                    print('======: ',period_end_depreciation_date)
                    depreciation_move_values.append(self.env['account.move']._prepare_move_for_asset_depreciation({
                        'amount': amount,
                        'asset_id': self,
                        'depreciation_beginning_date': start_depreciation_date,
                        'date': period_end_depreciation_date,
                        'asset_number_days': days,
                        'branch_id': self.branch_id.id if self.branch_id else False,
                    }))
                else:
                    print('amount:', amount, float_is_zero(amount, precision_rounding=self.currency_id.rounding), self.currency_id.rounding)
                    print('else: ', period_end_depreciation_date)
                days_already_depreciated += days

                if period_end_depreciation_date == period_end_fiscalyear_date:
                    days_left_to_depreciated = self.asset_lifetime_days - days_already_depreciated
                    residual_declining = residual_amount
                # print('12412412521515',period_end_depreciation_date)
                start_depreciation_date = period_end_depreciation_date + relativedelta(days=1)

        return depreciation_move_values
    

    @api.constrains('code', 'barcode')
    def _check_asset_code_barcode(self):
        for item in self:
            if self.env['account.asset'].sudo().search(
                    [('code', '=', item.code), ('id', '!=', item.id), ('company_id', '=', self.env.company.id)]) and item.code :
                raise UserError(_('%s Asset code is duplicated  ' % item.name))
            existing_ref = self.env['account.asset'].sudo().search([('barcode', '=', item.barcode), ('id', '!=', item.id), ('company_id', '=', self.env.company.id)])
            if existing_ref and item.barcode:
                raise UserError(_('%s Asset barcode is duplicated: barcode is %s\n%s is %s' % (item.name, item.barcode, existing_ref, existing_ref.mapped('barcode'))))
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
#         print 'args-- ',args
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for account in self:
            if account.code:
                name = account.code + ' ' + account.name
            else:
                name = account.name
            result.append((account.id, name))
        return result
    @api.onchange('analytic_distribution')
    def onchange_analytic(self):
        if self.analytic_distribution:
            for move in self.depreciation_move_ids:
                if move.state == 'draft':
                    for move_line in move.line_ids:
                        move_line.write({'analytic_distribution': self.analytic_distribution})

    def write(self, vals):
        result = super().write(vals)
        lock_date = self.company_id._get_user_fiscal_lock_date()
        if 'account_depreciation_id' in vals:
            # ::2 (0, 2, 4, ...) because we want all first lines of the depreciation entries, which corresponds to the
            # lines with account_depreciation_id as account
            self.depreciation_move_ids.filtered(lambda m: m.date > lock_date).line_ids[::2].account_id = vals['account_depreciation_id']
        if 'account_depreciation_expense_id' in vals:
            # 1::2 (1, 3, 5, ...) because we want all second lines of the depreciation entries, which corresponds to the
            # lines with account_depreciation_expense_id as account
            self.depreciation_move_ids.filtered(lambda m: m.state == 'draft').line_ids[1::2].account_id = vals['account_depreciation_expense_id']
        if 'journal_id' in vals:
            self.depreciation_move_ids.filtered(lambda m: m.date > lock_date).journal_id = vals['journal_id']
        if 'analytic_distribution' in vals:
            # Only draft entries to avoid recreating all the analytic items
            self.depreciation_move_ids.filtered(lambda m: m.state == 'draft').line_ids.analytic_distribution = vals['analytic_distribution']
        return result
    @api.depends('account_depreciation_id', 'original_move_line_ids')
    def _compute_account_asset_id(self):
        for record in self:
            if record.original_move_line_ids:
                if len(record.original_move_line_ids.account_id) > 1:
                    raise UserError(_("All the lines should be from the same account"))
                record.account_asset_id = record.original_move_line_ids.account_id
            if not record.account_asset_id:
                # Only set a default value, do not erase user inputs
                record._onchange_account_depreciation_id()
    @api.depends('acquisition_date', 'company_id', 'prorata_computation_type')
    def _compute_prorata_date(self):
        for asset in self:
            if not asset.prorata_date:
                if asset.prorata_computation_type == 'none' and asset.acquisition_date:
                    fiscalyear_date = asset.company_id.compute_fiscalyear_dates(asset.acquisition_date).get('date_from')
                    asset.prorata_date = fiscalyear_date
                else:
                    asset.prorata_date = asset.acquisition_date
            
        return
    @api.depends('original_move_line_ids', 'original_move_line_ids.account_id', 'asset_type', 'non_deductible_tax_value')
    def _compute_value(self):
        for record in self:
            if not record.original_move_line_ids:
                record.original_value = record.original_value or False
                continue
            # if any(line.move_id.state == 'draft' for line in record.original_move_line_ids):
            #     raise UserError(_("All the lines should be posted"))
            record.original_value = record.related_purchase_value
            if record.non_deductible_tax_value:
                record.original_value += record.non_deductible_tax_value
    # -------------------------------------------------------------------------
    # BOARD COMPUTATION
    # -------------------------------------------------------------------------
    def _compute_board_amount(self, asset_remaining_value, period_start_date, period_end_date, days_already_depreciated, days_left_to_depreciated, residual_declining,init=0):
        '''Дараах мөрүүд нэмсэн
            if self.capital_value>0:
                capital_value=0
                capital_ids=self.env['account.asset.capital.line'].search([('asset_id','=',self.id),
                                                                           ('capital_id.flow_line_id.state_type','=','done'),
                                                                           ('capital_id.date','<=',period_end_date.strftime("%Y-%m-%d"))])
                for capital in capital_ids:
                    if capital not in added:
                        capital_value+=capital.capital_amount
                        added.append(capital)
                total_depreciable_value+=capital_value
                residual_amount+=capital_value
                
            computed_mw_amount = (total_depreciable_value / self.method_number)
            if self.capital_value>0:
                computed_linear_amount=min(computed_mw_amount,computed_linear_amount)
                
                '''
        context = self._context or {}
        if self.asset_lifetime_days == 0:
            return 0, 0
        number_days = self._get_delta_days(period_start_date, period_end_date)
        total_days = number_days + days_already_depreciated
    
        if self.method in ('degressive', 'degressive_then_linear'):
            # Declining by year but divided per month
            # We compute the amount of the period based on ratio how many days there are in the period
            # e.g: monthly period = 30 days --> (30/360) * 12000 * 0.4
            # => For each month in the year we will decline the same amount.
            amount = (number_days / DAYS_PER_YEAR) * residual_declining * self.method_progress_factor
        else:
            total_depreciable_value=self.total_depreciable_value
            capital_ids=[]
            added=[]
            # if self.is_initial_derp == True:
            #     asset_remaining_value -= self.initial_derp
            if self.capital_value>0:
                capital_value=0
                capital_ids=self.env['account.asset.capital.line'].search([('asset_id','=',self.id),
                                                                           ('capital_id.flow_line_id.state_type','=','done'),
                                                                           ('capital_id.date','<=',period_end_date.strftime("%Y-%m-%d"))])
                for capital in capital_ids:
                    if capital not in added:
                        capital_value+=capital.capital_amount
                        added.append(capital)
                # total_depreciable_value+=capital_value
                # asset_remaining_value=self.capital_value+self.original_value
            if self.prorata_computation_type == 'daily_computation':
                total_depreciable_value = self.original_value-self.initial_derp
                # print('safasfasagasga',self.asset_lifetime_days+1)
                life_amount = self.original_value/(self.asset_lifetime_days+1)
                life_amount2 = self.initial_derp/life_amount
                life_new = self.asset_lifetime_days - life_amount2
                computed_linear_amount = (self.original_value/(self.asset_lifetime_days+1) * (total_days-1)) +asset_remaining_value-total_depreciable_value
                # print('total_depreciable_value///////',total_depreciable_value)
                # print('total_days////////',total_days)
                # print('self.asset_lifetime_days//////',self.asset_lifetime_days)
                # print('asset_remaining_value////////',asset_remaining_value)
                # print('total_depreciable_value///////////',total_depreciable_value)
                # print('computed_linear_amount/////////',computed_linear_amount)
                computed_mw_amount = (total_depreciable_value / self.method_number)
            else:
                computed_linear_amount = (self.original_value  / self.method_number)
                computed_mw_amount = (total_depreciable_value / self.method_number)
            print('computed_linear_amount11111',computed_linear_amount)

            if self.capital_value>0 and self.state != 'draft':
                print('number_days',number_days)
                print('total_depreciable_value',total_depreciable_value)
                print('days_already_depreciated',days_already_depreciated)
                print('asset_remaining_value',asset_remaining_value)
                print('self.total_depreciable_value',self.total_depreciable_value)
                print('self.original_value',self.original_value)
                computed_linear_amount=min(computed_mw_amount,computed_linear_amount)
                cc = self.depreciation_move_ids.filtered(lambda r: r.state == 'draft')
                posted_depreciation_move_ids = self.depreciation_move_ids.filtered(lambda x: x.state == 'posted').sorted(key=lambda l: l.date)#ХЭ эхний батлагдсан бол              
                dep_amount_life = 0
                for amount_dep in posted_depreciation_move_ids:
                    dep_amount_life+=amount_dep.depreciation_value
                print('ssss',dep_amount_life)
                if dep_amount_life == self.original_value:
                    computed_linear_amount = self.capital_value/self.method_number
                    print('capital_value',self.capital_value)
                    print('self.method_number',self.method_number)
                elif dep_amount_life < self.original_value and self.by_day==False:
                    life_method = 0
                    monthly_amount = self.original_value/self.method_number
                    dep_amount = dep_amount_life/monthly_amount
                    life_method = self.method_number-dep_amount
                    computed_linear_amount = monthly_amount+ self.capital_value/life_method
                elif dep_amount_life < self.original_value and self.by_day==True:
                    life_method = 0
                    monthly_amount = self.original_value/self.method_number
                    dep_amount = dep_amount_life/monthly_amount
                    life_method = self.method_number
                    computed_linear_amount = monthly_amount+ self.capital_value/life_method
                    
                else:
                    if cc:
                        ccc = len(cc)
                        result = capital_value/(ccc-1)
                    else:
                        result = 0
                    computed_linear_amount += result
                print('computed_linear_amount',computed_linear_amount)
            if self.revaluation_value>0:
                revaluation_value=0
                revaluation_ids=self.env['account.asset.revaluation.line'].search([('asset_id','=',self.id),
                                                                           ('revaluation_id.flow_line_id.state_type','=','done'),
                                                                           ('revaluation_id.date','<=',period_end_date.strftime("%Y-%m-%d"))])
                for revaluation in revaluation_ids:
                    if revaluation not in added:
                        revaluation_value+=revaluation.revaluation_amount
                        added.append(revaluation)
                # total_depreciable_value+=revaluation_value
                asset_remaining_value+=revaluation_value
            # computed_linear_amount = (total_depreciable_value * total_days / self.asset_lifetime_days) + asset_remaining_value - total_depreciable_value
            # computed_linear_amount = (self.original_value  / self.method_number)

            # computed_mw_amount = (total_depreciable_value / self.method_number)
            # if self.revaluation_value>0 and self.state != 'draft':
            #     computed_linear_amount=min(computed_mw_amount,computed_linear_amount)
            #     cc = self.depreciation_move_ids.filtered(lambda r: r.state == 'draft')
            #     ccc = len(cc)
            #     result = revaluation_value/ccc

            #     computed_linear_amount += result
                
            print('safasfasfas',asset_remaining_value)
            if float_compare(asset_remaining_value, 0, precision_rounding=self.currency_id.rounding) >= 0:
                linear_amount = min(computed_linear_amount, asset_remaining_value)
                print('computed_linear_amount11111',computed_linear_amount)
                print('asset_remaining_value11111',asset_remaining_value)
                print('linear_amount11111',linear_amount)

                amount = max(linear_amount, 0)
                print('amount11111',amount)
            else:
                linear_amount = max(computed_linear_amount, asset_remaining_value)
                amount = min(linear_amount, 0)
                print('amount22222',amount)
        print('asset_remaining_value22222',asset_remaining_value)
        if self.method == 'degressive_then_linear' and days_left_to_depreciated != 0:
            linear_amount = number_days * total_depreciable_value / self.asset_lifetime_days
            amount = max(linear_amount, amount, key=abs)
            print('linear_amount112131231',linear_amount)
        # if self.method == 'degressif_chelou' and days_left_to_depreciated != 0:
        #     linear_amount = number_days * residual_declining / days_left_to_depreciated
        #     if float_compare(residual_amount, 0, precision_rounding=self.currency_id.rounding) >= 0:
        #         amount = max(linear_amount, amount)
        #     else:
        #         amount = min(linear_amount, amount)
    
    
        if abs(asset_remaining_value) < abs(amount) or total_days >= self.asset_lifetime_days:
            # If the residual amount is less than the computed amount, we keep the residual amount
            # If total_days is greater or equals to asset lifetime days, it should mean that
            # the asset will finish in this period and the value for this period is equals to the residual amount.
            amount = asset_remaining_value
            print('amount333333',amount)
        posted_depreciation_move_ids = self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and not x.asset_value_change).sorted(key=lambda l: l.date)#ХЭ эхний батлагдсан бол              
        if self.is_initial_derp and self.initial_derp>0 and len(posted_depreciation_move_ids)==0 and init==1:
            amount=self.initial_derp
        print('amountamountamountamountamount',amount)
        return number_days, self.currency_id.round(amount)
    def asset_close_button(self):
        for move in self:
            draft_depreciation_move_ids = move.depreciation_move_ids.filtered(lambda x: x.state == 'draft')      
            if draft_depreciation_move_ids:
                raise UserError(_('Хөрөнгийн элэгдэл батлагдаж дуусаагүй байна'))
            else:
                move.state = 'close'

    @api.depends('model_id')
    def onchange_user_id(self):
        search_domain=self.asset_domain()
        domain = {'asset_type_id': search_domain}
        return {'domain': domain}
    def asset_domain(self):
        search_domain=[]
        for item in self:
            search_domain = [
                    ('model_id','=',item.model_id.id),
                ]
        return search_domain
    
    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            display_name = ''
            if record.name:
                display_name = record.name
                record.display_name = display_name
                if record.code:
                    display_name = record.name + ' ' + record.code
                    record.display_name = display_name
            else:
                record.display_name = ' '

    @api.model
    def compute_generated_entries(self, date, asset_types,company_id):
        # Entries generated : one by grouped category and one by asset from ungrouped category
        created_move_ids = []
        asset_domain=[]
        if asset_types:
            ungrouped_assets = self.env['account.asset'].search(asset_domain + [('company_id', '=', company_id.id),('state', '=', 'open'),('asset_type_id', 'in', asset_types.ids)])
        else:
            ungrouped_assets = self.env['account.asset'].search(asset_domain + [('company_id', '=', company_id.id),('state', '=', 'open'),('asset_type_id', '=', False)])
        # print(sd)
        ungrouped_assets._compute_entries(date)
    def _compute_entries(self, date):
        move_id = self.env['account.move'].search([
            ('asset_id', 'in', self.ids), ('date', '<=', date), ('state','=','draft')]),    
        

        # Find the account.move object with ID 5731 in the list
        for move in move_id:
            if move:
                move.action_post()
            else:
                print("Account move with ID 5731 not found.")
    @api.model
    def compute_generated_entries_tax(self, date):
        # Entries generated : one by grouped category and one by asset from ungrouped category
        created_move_ids = []
        asset_domain=[]
        ungrouped_assets = self.env['account.asset'].search(asset_domain + [('state', '=', 'open')])
        ungrouped_assets._compute_entries_tax(date)
    def _compute_entries_tax(self, date):
        move_id = self.env['account.asset.tax.depreciation.line'].search([
            ('asset_id', 'in', self.ids), ('depreciation_date', '<=', date), ('move_check','=',False)]),    
        

        # Find the account.move object with ID 5731 in the list
        for move in move_id:
            if move:
                move.move_check=True
            else:
                print("Account move with ID 5731 not found.")
    def _get_move_vals(
        self, src_account, asset_amount, current_currency, entry_date, year, initial
    ):
        # Хөрөнгө батлахад хөрөнгө орлогодож байгаа журналын бичилт үүсгэх утга буцаах функц
        self.ensure_one()
        line_ids = []
        journal_id = self.journal_id.id
        # Хөрөнгийн данс
        dt_account = self.account_asset_id.id
        kt_account = src_account
        currency_amount = self.original_value
    #             if self.company_id.asset_journal_settings == 'intersperse' and self.invoice_line_id:
    #                 if not self.company_id.purchase_asset_journal_id:
    #                     raise UserError(_('Configure purchase journal of asset in %s company!' % self.company_id.name))
    #                 journal_id = self.company_id.purchase_asset_journal_id.id
    # Дт талын журналын мөр
        line_ids.append(
            self._get_line_vals(
                self.name,
                dt_account,
                False,
                asset_amount,
                currency_amount,
                current_currency,
                entry_date,
            )
        )
        # Кт талын журналын мөр
        line_ids.append(
            self._get_line_vals(
                self.name,
                kt_account,
                False,
                -asset_amount,
                -currency_amount,
                current_currency,
                entry_date,
            )
        )
        print('line_Vals', line_ids)
        move_vals = {
            "date":self.prorata_date,
            "ref": str(self.code) + "-" + self.name + " Эхний үлдэгдэл",
            "journal_id": journal_id,
            "asset_depreciated_value": 0,
            "depreciation_value": 0,
            "asset_remaining_value": self.original_value,
            "line_ids": line_ids,
        }
        # print('move_vals', move_vals)
        return move_vals
    def _get_move_vals_initial(
        self, src_account, asset_amount, current_currency, entry_date, year, initial
    ):
        # Хөрөнгө батлахад хөрөнгө орлогодож байгаа журналын бичилт үүсгэх утга буцаах функц
        self.ensure_one()
        line_ids = []
        journal_id = self.journal_id.id
        # if initial:
            # Эхний элэгдлийн данс
        dt_account = src_account
        kt_account = self.account_depreciation_id.id
        currency_amount = self.initial_derp

        #             if self.company_id.asset_journal_settings == 'intersperse':
        #                 if not self.company_id.depreciation_asset_journal_id:
        #                     raise UserError(_('Configure depreciation journal of asset in %s company!' % self.company_id.name))
        #                 journal_id = self.company_id.depreciation_asset_journal_id.id
        line_ids.append(
            self._init_get_line_vals(
                self.name,
                dt_account,
                False,
                asset_amount,
                currency_amount,
                current_currency,
                entry_date,
            )
        )
        # Кт талын журналын мөр
        line_ids.append(
            self._init_get_line_vals(
                self.name,
                kt_account,
                False,
                -asset_amount,
                -currency_amount,
                current_currency,
                entry_date,
            )
        )
        print('line_Vals', line_ids)
        move_vals = {
            "date": self.prorata_date,
            "ref": str(self.code) + "-" + self.name + " Эхний үлдэгдэл",
            "journal_id": journal_id,
            "asset_depreciated_value": self.initial_derp,
            "depreciation_value": self.initial_derp,
            "asset_remaining_value": self.original_value - self.initial_derp,
            "line_ids": line_ids,
            "asset_id": self.id,
            "asset_depreciation_beginning_date":entry_date,
        }
        # print('move_vals', move_vals)
        # self.compute_depreciation_board()

        return move_vals
    def new_set_to_validate(self):
        moves = self.env["account.asset"].browse(self._context["active_ids"])
        for move in moves:
            move.validate()
    def validate(self, context=None):
        # Хөрөнгийг батлах үед хөрөнгийн нийт үнэ болон эхний элэгдэлийн дүнгээр журналын бичилт үүснэ
        if context is None:
            context = self._context or {}
        move_obj = self.env.get("account.move")
        self.compute_depreciation_board()
        for asset in self:
            if asset.state =='open':
                raise UserError(_("Батлагдсан хөрөнгө байна!!! %s") % asset.name)    
            else:        
                self.write({"state": "open"})
                asset_amount = 0
                #             if asset.initial_value + asset.revaluation_value != asset.value:
                #                 raise UserError(_("%s asset Initial Value + Revaluation Value != Value.") % asset.name)
                # if asset.date < asset.purchase_date:
                #     raise UserError(_("%s asset purchase date may be equal to or less than date.") % asset.name)
                # print ('asset.account_move_line_ids ',asset.account_move_line_ids)
                if  asset.original_value and self.is_initial_derp:
                    #                 if not context.get('src_account_id', False):
                    #                     dummy, action_id = tuple(self.env['ir.model.data'].get_object_reference(
                    #                         'l10n_mn_account_asset', 'action_account_asset_validate'))
                    #                     result = self.env['ir.actions.act_window'].sudo().browse(action_id).read([])[0]
                    #                     result['context'] = dict(context.items(), active_id=asset.id, active_ids=[asset.id])
                    #                     return result
                    # Журналын бичилт хийх
                    entry_date = context.get("entry_date", asset.acquisition_date)
                    year = entry_date.year
                    # Хөрөнгийн ангилал дах хөрөнгийн дансны currency-г авах
                    current_currency = asset.currency_id
                    asset_amount = current_currency._convert(
                        asset.original_value,
                        asset.company_id.currency_id,
                        asset.company_id,
                        entry_date,
                        round=False,
                    )
                    #                 move_id = move_obj.create(asset._get_move_vals(context['src_account_id'], asset_amount, current_currency, entry_date, year, False))
                    #                 if asset.category_id.open_asset:
                    #                     move_id.action_post()
                    # Хэрэв элэгдлийн эхний дүн байвал тухайн дүнгээр дахин ажил гүйлгээ үүсгэнэ
                    #                 if asset.initial_depreciation > 0: #ХЭ  c1 гүй бол
                    if context.get("src_account_id", False):
                        # Анхны өртгөөр
                        if not context.get("src_account_id", False):
                            raise UserError(
                                _(
                                    "хөрөнгө: %s \nЭхний үлдэгдлэлээр оруулсан бол жагсаалтаас ЭҮ данс сонгож батлана."
                                )
                                % self.name
                            )
                        move_id = move_obj.create(
                            asset._get_move_vals(
                                context["src_account_id"],
                                asset_amount,
                                current_currency,
                                entry_date,
                                year,
                                False,
                            )
                        )
                        move_id.action_post()
                    unposted_depreciation_move_ids = self.depreciation_move_ids.filtered(lambda x: x.state == 'draft' and x.depreciation_value == self.initial_derp).sorted(key=lambda l: l.date)#ХЭ эхний батлагдсан бол
                    print ('unposted_depreciation_move_ids== ',unposted_depreciation_move_ids)
                    all_moves = self.env['account.move'].search([('id', 'in', self.depreciation_move_ids.ids)])
                    all_moves.write({
                        'auto_post': 'no',
                    })
                    # asset.validate_new()
                    # for moves_ids in all_moves:                                                                                                                                                                                                                                                                                                                                   
                    #     moves_ids.auto_post == 'no'    
                    # print('===========', all_moves)
        return
    def validate_new(self, context=None):
        # Хөрөнгийг батлах үед хөрөнгийн нийт үнэ болон эхний элэгдэлийн дүнгээр журналын бичилт үүснэ
        if context is None:
            context = self._context or {}
        move_obj = self.env.get("account.move")
        for asset in self:
            # asset.compute_depreciation_board()
            # self.write({"state": "open"})
            asset_amount = 0
            #             if asset.initial_value + asset.revaluation_value != asset.value:
            #                 raise UserError(_("%s asset Initial Value + Revaluation Value != Value.") % asset.name)
            # if asset.date < asset.purchase_date:
            #     raise UserError(_("%s asset purchase date may be equal to or less than date.") % asset.name)
            # print ('asset.account_move_line_ids ',asset.account_move_line_ids)
            if  asset.original_value and self.is_initial_derp:
                #                 if not context.get('src_account_id', False):
                #                     dummy, action_id = tuple(self.env['ir.model.data'].get_object_reference(
                #                         'l10n_mn_account_asset', 'action_account_asset_validate'))
                #                     result = self.env['ir.actions.act_window'].sudo().browse(action_id).read([])[0]
                #                     result['context'] = dict(context.items(), active_id=asset.id, active_ids=[asset.id])
                #                     return result
                # Журналын бичилт хийх
                entry_date = context.get("entry_date", asset.prorata_date)
                year = entry_date.year
                # Хөрөнгийн ангилал дах хөрөнгийн дансны currency-г авах
                current_currency = asset.currency_id
                asset_amount = current_currency._convert(
                    asset.initial_derp,
                    asset.company_id.currency_id,
                    asset.company_id,
                    entry_date,
                    round=False,
                )
                move_id = move_obj.create(
                    asset._get_move_vals_initial(
                        context["src_account_id"],
                        asset_amount,
                        current_currency,
                        entry_date,
                        year,
                        False,
                    )
                )
                move_id.action_post()

        return
    def compute_depreciation_board(self):
        self.ensure_one()
        new_depreciation_moves_data = self._recompute_board()

        # Need to unlink draft move before adding new one because if we create new move before, it will cause an error
        # in the compute for the depreciable/cumulative value
        self.depreciation_move_ids.filtered(lambda mv: mv.state == 'draft').write({'asset_id': False,'to_check':True})
        new_depreciation_moves = self.env['account.move'].create(new_depreciation_moves_data)
        # if self.state == 'open':
        #     # In case of the asset is in running mode, we post in the past and set to auto post move in the future
        #     new_depreciation_moves._post()

        return True
        
    # @api.depends('account_depreciation_id', 'account_depreciation_expense_id', 'original_move_line_ids')
    # def _compute_account_asset_id(self):
    #     for record in self:
    #         if record.original_move_line_ids:
    #             # if len(record.original_move_line_ids.account_id) > 1:
    #             #     raise UserError(_("All the lines should be from the same account"))
    #             for item in record.original_move_line_ids:
    #                 record.account_asset_id = item.account_id
    #         if not record.account_asset_id:
    #             # Only set a default value, do not erase user inputs
    #             record._onchange_account_depreciation_id()
    @api.onchange("owner_id")
    def _onchange_owner_partner(self):
        if self.owner_id.user_ids:
            employee_id = self.owner_id.user_ids.employee_id
            self.owner_department_id = employee_id.department_id.id
    @api.onchange('model_id')
    def _onchange_model_id_account(self):
        model = self.model_id
        if model:
            self.account_asset_id = model.account_asset_id
    @api.depends('owner_id','location_id','owner_department_id')
    def _move_count(self):
        for asset in self:
            res = self.env['account.asset.move.line'].search_count([('asset_id', '=', asset.id),('state','=', 'receipt')])
            # res = 0
            asset.move_count = res if res else 0
    @api.depends('owner_id','location_id','owner_department_id')
    def move_history_open(self):
        for asset in self:
            action = self.env.ref('mw_asset.action_asset_move_line').read()[0]
            action['domain'] = [('asset_id','=', asset.id),('state','=', 'receipt')]    
            action['context'] = {}
            return action
    def _get_line_vals(self, name, account, partner_id, asset_amount, currency_amount, current_currency, entry_date):
        # Журналын мөр үүсгэх
        context = self._context or {}
        vals={'name': name,
                       'ref': name,
                       'account_id': account,
                       'debit': asset_amount if asset_amount > 0 else 0,
                       'credit': abs(asset_amount) if asset_amount < 0 else 0,
                       'partner_id': partner_id or self.partner_id.id or False,
                       'currency_id': current_currency and current_currency.id or False,
                       'amount_currency': currency_amount if current_currency and self.company_id.currency_id.id == current_currency.id else 0.0,
                    #    'analytic_account_id': analytic_account,
                       'date': entry_date,
                       'balance':asset_amount
                       }
        if asset_amount>0 and context.get("src_account_id", False):
            vals.update({
            'asset_ids': [(6,0,[self.id])]
            })
        return (0, 0, vals)
        
    def _init_get_line_vals(self, name, account, partner_id, asset_amount, currency_amount, current_currency, entry_date):
        # Журналын мөр үүсгэх
        context = self._context or {}
        vals={'name': name,
                       'ref': name,
                       'account_id': account,
                       'debit': asset_amount if asset_amount > 0 else 0,
                       'credit': abs(asset_amount) if asset_amount < 0 else 0,
                       'partner_id': self.partner_id and self.partner_id.id and partner_id or False,
                       'currency_id': current_currency and current_currency.id or False,
                       'amount_currency': currency_amount if current_currency and self.company_id.currency_id.id == current_currency.id else 0.0,
                    #    'analytic_account_id': analytic_account,
                       'date': entry_date,
                       'balance':asset_amount
                       }
  # if asset_amount>0 and context.get("src_account_id", False):
  #     vals.update({
  #     'asset_ids': [(6,0,[self.id])]
  #     })
        return (0, 0, vals)
                                              

    def set_to_close(self, invoice_line_ids, date=None, message=None, close_status=None):
        self.ensure_one()
        disposal_date = date or fields.Date.today()
        if invoice_line_ids and self.children_ids.filtered(lambda a: a.state in ('draft', 'open') or a.value_residual > 0):
            raise UserError(_("You cannot automate the journal entry for an asset that has a running gross increase. Please use 'Dispose' on the increase(s)."))
        full_asset = self + self.children_ids
        move_ids = full_asset._get_disposal_moves([invoice_line_ids] * len(full_asset), disposal_date,message)
        for asset in full_asset:
            asset.message_post(body=
                _('Asset sold. %s', message if message else "")
                if invoice_line_ids else
                _('Asset disposed. %s', message if message else "")
            )
        full_asset.write({'state': 'close'})
        full_asset.write({'close_status': close_status if close_status else None})
        if move_ids:
            name = _('Disposal Move')
            view_mode = 'form'
            if len(move_ids) > 1:
                name = _('Disposal Moves')
                view_mode = 'tree,form'
            return {
                'name': message if message else ' '+' '+ self.name if self.name else ' '+' '+self.code if self.code else ' ',
                'view_mode': view_mode,
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': move_ids[0],
                'domain': [('id', 'in', move_ids)]
            }

    def _get_disposal_moves(self, invoice_lines_list, disposal_date,message=''):
        """Create the move for the disposal of an asset.

        :param invoice_lines_list: list of recordset of `account.move.line`
            Each element of the list corresponds to one record of `self`
            These lines are used to generate the disposal move
        :param disposal_date: the date of the disposal
        """
        def get_line(asset, amount, account):
            return (0, 0, {
                'name': message if message else ' '+' '+ self.name if self.name else ' '+' '+self.code if self.code else ' ',
                'account_id': account.id,
                'balance': -amount,
                'analytic_distribution': analytic_distribution,
                'currency_id': asset.currency_id.id,
                'amount_currency': -asset.company_id.currency_id._convert(
                    from_amount=amount,
                    to_currency=asset.currency_id,
                    company=asset.company_id,
                    date=disposal_date,
                )
            })

        move_ids = []
        assert len(self) == len(invoice_lines_list)
        for asset, invoice_line_ids in zip(self, invoice_lines_list):
            asset._create_move_before_date(disposal_date)

            analytic_distribution = asset.analytic_distribution

            dict_invoice = {}
            invoice_amount = 0

            initial_amount = asset.original_value
            initial_account = asset.original_move_line_ids.account_id if len(asset.original_move_line_ids.account_id) == 1 else asset.account_asset_id

            all_lines_before_disposal = asset.depreciation_move_ids.filtered(lambda x: x.date <= disposal_date)
            depreciated_amount = asset.currency_id.round(copysign(
                sum(all_lines_before_disposal.mapped('depreciation_value')) + asset.already_depreciated_amount_import,
                -initial_amount,
            ))
            depreciation_account = asset.account_depreciation_id

            # for invoice_line in invoice_line_ids:
            #     dict_invoice[invoice_line.account_id] = copysign(invoice_line.balance, -initial_amount) + dict_invoice.get(invoice_line.account_id, 0)
            #     invoice_amount += copysign(invoice_line.balance, -initial_amount)
            # print('sssasfsafsa',depreciated_amount)
            # print('sssasfsafsa222',initial_amount)
            new_depreciation_value = -1*depreciated_amount
            invoice_amount = initial_amount-new_depreciation_value
            # list_accounts = [(amount, account) for account, amount in dict_invoice.items()]
            # list_accounts = [(amount, asset.company_id.loss_account_id.id) for asset.company_id.loss_account_id]
            difference = -initial_amount - depreciated_amount
            if not asset.company_id.account_id:
                raise UserError(_('%s Компани дээр хөрөнгийн гарзын данс тохируулаагүй байна.' % asset.company_id.name))
            difference_account = asset.company_id.account_id
            line_datas = [(initial_amount, initial_account), (depreciated_amount, depreciation_account)] + [(difference, difference_account)]
            # print('lineexssssss',line_datas)
            vals = {
                'asset_id': asset.id,
                'ref': message if message else ' '+' '+ self.name if self.name else ' '+' '+self.code if self.code else ' ',
                'asset_depreciation_beginning_date': disposal_date,
                'date': disposal_date,
                'journal_id': asset.journal_id.id,
                'move_type': 'entry',
                'line_ids': [get_line(asset, amount, account) for amount, account in line_datas if account],
            }
            # print('sssasfsafsa2222212312312',vals)
            for moves in self.depreciation_move_ids:
                if moves.state=='draft':
                    moves.write({'to_check': True,'asset_id': False})
                # print('21241242142142',moves.state)
            asset.write({'depreciation_move_ids': [(0, 0, vals)]})
            draft_move_id=self.env['account.move'].search([('id','=',asset.depreciation_move_ids.ids),('state','=','draft')])
            draft_move_id.action_post()
            move_ids += self.env['account.move'].search([('asset_id', '=', asset.id), ('state', '=', 'draft')]).ids

        return move_ids
    
    def _cancel_future_moves(self, date):
        """Cancel all the depreciation entries after the date given as parameter.

        When possible, it will reset those to draft before unlinking them, reverse them otherwise.

        :param date: date after which the moves are deleted/reversed
        """
        to_reverse = self.env['account.move']
        to_cancel = self.env['account.move']
        for asset in self:
            posted_moves = asset.depreciation_move_ids.filtered(lambda m: (
                not m.reversal_move_id
                and not m.reversed_entry_id
                and m.state == 'posted'
                and m.date > date
            ))
            lock_date = asset.company_id._get_user_fiscal_lock_date()
            for move in posted_moves:
                if move.inalterable_hash or move.date <= lock_date:
                    to_reverse += move
                else:
                    to_cancel += move
        to_reverse._reverse_moves(cancel=True)
        to_cancel.button_draft()
        self.depreciation_move_ids.filtered(lambda m: m.state == 'draft').write({'to_check': True,'asset_id': False})
                            # moves.write({'to_check': True,'asset_id': False})

    def search_and_raise_line(self, date):
        # Хаалтын огноонд тохирох сарын элэгдлийн мөр батлагдаагүй байх хэрэгтэй учир нь хөрөнгө хаах үед батлагдана
        line = []
        if date and self and self.depreciation_move_ids:
            before_lines = self.depreciation_move_ids.filtered(
                lambda l: l.state=='draft' and l.date < date
            )
            if before_lines:
                raise UserError(
                    _(
                        "%s asset validate depreciation lines before %s date!"
                        % (self.name, date)
                    )
                )
            after_lines = self.depreciation_move_ids.filtered(
                lambda l: l.state=='posted' and l.date > date
            )
            if after_lines:
                raise UserError(
                    _(
                        "%s validated depreciation lines after %s date!"
                        % (self.name, date)
                    )
                )
        return line
    def asset_close_before_board(self, date, type):
        # Элэгдлийн самбар байгуулах
        self.ensure_one()
        date = date
        context = dict(self._context or {})
        unposted_depreciation_line_ids = self.depreciation_move_ids.filtered(
            lambda x: x.state=='draft'
        )
        #         print ('unposted_depreciation_line_ids=== ',unposted_depreciation_line_ids)
        #         # Батлагдсан элэгдлийн мөрүүд
        posted_depreciation_line_ids = self.depreciation_move_ids.filtered(
            lambda x: x.state=='posted'
        ).sorted(key=lambda l: l.date)
        #         # Батлагдаагүй элэгдлийн мөрүүд
        #         unposted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: not x.move_check and not x.is_freeze)
        #         # Батлагдсан, царцаасан элэгдлийн мөрүүд
        #         # Remove old unposted depreciation lines. We cannot use unlink() with One2many field
        commands = [
            (2, line_id.id, False) for line_id in unposted_depreciation_line_ids
        ]
        if not posted_depreciation_line_ids:
            return False
        if self.value_residual > 0:
            move_obj = self.env.get("account.move")
            value = (
                self.original_value
                + self.capital_value
            )
            month_days = calendar.monthrange(date.year, date.month)[1]
            day1 = posted_depreciation_line_ids[-1].date
            days = (date - day1).days
            mm_amount = self.original_value / self.asset_lifetime_days
            monthly_amount = mm_amount * days
            residual_amount = self.value_residual
            if self.value_residual <= monthly_amount:
                monthly_amount = self.value_residual
            residual_amount -= monthly_amount
            # move_id = move_obj.create(
                        # self._get_dispose_move_vals(monthly_amount,date,type))
            # self.update({'depreciation_move_ids': [(0, 0, move_id)]})

    def _get_dispose_move_vals(
        self, asset_amount, entry_date, type
    ):
        line_ids = []
        type_name = ''
        if type=='sale':
            type_name += 'боруулалт'
        elif type=='act':
            type_name += 'акт'
        else:
            type_name = ''
        kt_account = self.account_depreciation_id.id
        dt_account =  self.account_depreciation_expense_id.id
        print('assset_amount',asset_amount)
        currency_amount = asset_amount
        journal_id = self.journal_id.id
        current_currency = self.currency_id
        asset_depreciated_value = self.original_value - asset_amount
    # Дт талын журналын мөр
        line_ids.append(
            self._get_line_vals(
                self.name,
                dt_account,
                False,
                asset_amount,
                currency_amount,
                current_currency,
                entry_date,
            )
        )
        # Кт талын журналын мөр
        line_ids.append(
            self._get_line_vals(
                self.name,
                kt_account,
                False,
                -asset_amount,
                -currency_amount,
                current_currency,
                entry_date,
            )
        )
        move_vals = {
            "date": entry_date, #self.prorata_date,
            "ref": str(self.code) + "-" + self.name + ' ' +type_name,
            "journal_id": journal_id,
            "asset_depreciated_value": 0,
            "depreciation_value": asset_amount,
            "asset_remaining_value": self.original_value,
            "line_ids": line_ids,
        }
        print('move_vals', move_vals)
        return move_vals
class AccountAssetLocation(models.Model):
    _name = "account.asset.location"
    _description = "Asset location"

    name = fields.Char(string="Name", index=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    description = fields.Text(string="Description")
    account_analytic_id = fields.Many2one(
        "account.analytic.account", string="Analytic account"
    )
    location_type = fields.Selection(
        [("view", "View"), ("simple", "Simple")],
        string="Location Type",
        default="simple",
    )
    parent_id = fields.Many2one(
        "account.asset.location",
        "Top Location",
        domain=[("location_type", "=", "view")],
        ondelete="set null",
    )

    def unlink(self):
        for obj in self:
            asset_obj = self.env["account.asset"].search(
                [("location_id", "=", obj.id)], limit=1
            )
            if asset_obj:
                raise ValidationError(
                    _("The location of the asset is selected on the %s asset.")
                    % asset_obj.name
                )
            return super(AccountAssetLocation, self).unlink()

    @api.constrains("name")
    def _check_name(self):
        for locations in self:
            if locations.name:
                categories = self.env["account.asset.location"].search(
                    [
                        ("name", "=", locations.name),
                        ("id", "!=", locations.id),
                        ("company_id", "=", locations.company_id.id),
                    ]
                )
            if locations.parent_id.location_type == "simple":
                exception = _(
                    "Location type of Top Location is not able to be simple: "
                ) + str(locations.parent_id.name)
                raise ValidationError(exception)
            for categ in categories:
                if categ:
                    exception = _("location name duplicated: ") + categ.name
                    raise ValidationError(exception)

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault("name", _("%s (copy)") % (self.name or ""))
        return super(AccountAssetLocation, self).copy(default)
