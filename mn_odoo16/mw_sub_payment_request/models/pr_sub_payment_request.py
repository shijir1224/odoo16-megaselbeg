# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.addons.mw_base.verbose_format import verbose_format

TYPE_Selection = [
		('cash', u'Бэлнээр'),
		('bank', u'Банкны шилжүүлгээр'),
		('pretty', u'Жижиг мөнгөн сангаас'),
		('credit_card', u'Кредит картаар'),
		('transfer', u'Хоорондын тооцоо'),
		('talon', u'Бензин талон'),
	]

class PaymentRequest(models.Model):
	_inherit = 'payment.request'

	flow_id = fields.Many2one('dynamic.flow', string='Урсгал тохиргоо', tracking=True, 
					default=False, copy=True, required=True, domain="[('model_id.model','=','payment.request')]")
	approved_date = fields.Datetime(string='Батлагдсан огноо', copy=False)
	branch_id = fields.Many2one('res.branch', 'Салбар', tracking=True)
	type = fields.Selection(TYPE_Selection, string='Төлбөрийн төрөл', default=False, tracking=True)
	journal_id = fields.Many2one('account.journal', string='Журнал')
	account_company_line_ids = fields.One2many('account.company.request.item', 'payment_id', string='Тайлбарын мөр')
	amount_total = fields.Monetary(string='Нийт дүн', store=True, readonly=True, compute='compute_amount_total')
	is_butsaalt = fields.Boolean(related='flow_id.is_butsaalt')
	butsaalt_partner = fields.Char(string='Харилцагч')
	butsaalt_bank = fields.Char(string='Харилцагчийн банк')
	butsaalt_dans = fields.Char(string='Харилцагчийн данс')
	is_info = fields.Boolean(related='flow_id.is_info')
	info_payment = fields.Text(string='Дэлгэрэнгүй мэдээлэл', readonly=True)

	@api.depends('account_company_line_ids.price_total')
	def compute_amount_total(self):
		for order in self:
			sum_amount = 0.0
			for line in order.account_company_line_ids:
				sum_amount += line.price_total
			order.update({
				'amount_total': sum_amount,
			})

	@api.onchange('desc_line_ids','account_company_line_ids')
	def onch_amount_total(self):
		if self.desc_line_ids:
			self.amount = self.amount_total_pay
		else:
			self.amount = self.amount_total

	@api.depends('create_partner_id')
	def compute_user_branch(self):
		for item in self:
			if not item.branch_id:
				item.branch_id = item.department_id.branch_id.id or False

	def action_next_stage(self):
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if next_flow_line_id:
			if self.visible_flow_line_ids and next_flow_line_id.id not in self.visible_flow_line_ids.ids:
				check_next_flow_line_id = next_flow_line_id
				while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:

					temp_stage = check_next_flow_line_id._get_next_flow_line()
					if temp_stage.id == check_next_flow_line_id.id or not temp_stage:
						break
					check_next_flow_line_id = temp_stage
				next_flow_line_id = check_next_flow_line_id
			if next_flow_line_id._get_check_ok_flow(self.branch_id, False, self.create_uid):
				self.flow_line_id = next_flow_line_id
				if self.flow_line_id.state_type == 'done':
					self.action_done()
				if self.flow_line_id.state_type == 'accountant':
					self.approved_date = datetime.now()

				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'payment_request_id', self)
				send_users = next_flow_line_id._get_flow_users(self.branch_id, False, self.env.user)
				if send_users:
					self.send_chat_employee(send_users.mapped('partner_id'))
			else:
				con_user = next_flow_line_id._get_flow_users(self.branch_id, False, self.create_uid)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)

	def get_company_logo(self, ids):
		report_id = self.browse(ids)
		image_buf = report_id.company_id.logo_web.decode('utf-8')
		image_str = ''
		if len(image_buf) > 10:
			image_str = '<img alt="Embedded Image" width="90" src="data:image/png;base64,%s" />' % image_buf
		return image_str

	def get_date(self, ids):
		report_id = self.browse(ids)
		year = report_id.date.date().year
		month = report_id.date.date().month
		day = report_id.date.date().day
		return '{} оны {} сарын {} өдөр'.format(year, month, day)

	def get_bank_name(self, ids):
		report_id = self.browse(ids)
		bank_name = ''
		if report_id.journal_id:
			bank_name = report_id.journal_id.bank_id.name
		return bank_name

	def get_dans_name(self, ids):
		report_id = self.browse(ids)
		bans_name = ''
		if report_id.journal_id:
			bans_name = report_id.journal_id.bank_account_id.acc_number
		return bans_name

	def get_user_info(self, ids):
		report_id = self.browse(ids)
		user_info = ''
		if report_id.user_id:
			emp_obj = self.env['hr.employee'].search([('user_id','=',report_id.user_id.id)])
			if emp_obj:
				user_info = emp_obj.job_id.name + ', ' + emp_obj.last_name[:1] + '.' + emp_obj.name
		return user_info

	def get_partner_info(self, ids):
		report_id = self.browse(ids)
		partner_info = ''
		if report_id.partner_id:
			partner_info = report_id.partner_id.name + ', ' + (report_id.partner_id.vat if report_id.partner_id.vat else '')
		return partner_info

	# def get_amount_str(self, ids):
	# 	report_id=self.browse(ids)
	# 	amount_str = ''
	# 	if report_id.amount > 0:
	# 		amount_str = verbose_format(abs(report_id.amount))
	# 	return amount_str

	def get_journal_bank_dans(self, ids):
		report_id=self.browse(ids)
		journal_bank_dans = ''
		if report_id.journal_id and report_id.journal_id.bank_account_id:
			journal_bank_dans = report_id.journal_id.bank_account_id.bank_id.name + ' - ' + report_id.journal_id.bank_account_id.acc_number
		return journal_bank_dans

	def get_journal_currency(self, ids):
		report_id=self.browse(ids)
		journal_currency = ''
		if report_id.journal_id and report_id.journal_id.currency_id:
			journal_currency = report_id.journal_id.currency_id.name
		return journal_currency

	def get_payment_partner(self, ids):
		report_id=self.browse(ids)
		payment_partner = ''
		if report_id.partner_id and not report_id.flow_id.is_butsaalt:
			payment_partner = report_id.partner_id.name
		elif report_id.butsaalt_partner and report_id.flow_id.is_butsaalt:
			payment_partner = report_id.butsaalt_partner
		return payment_partner

	def get_payment_dans(self, ids):
		report_id=self.browse(ids)
		payment_dans = ''
		if report_id.dans_id and not report_id.flow_id.is_butsaalt:
			payment_dans = report_id.dans_id.bank_id.name + ' - ' + report_id.dans_id.acc_number
		elif report_id.butsaalt_dans and report_id.flow_id.is_butsaalt:
			payment_dans = report_id.butsaalt_bank + ' - ' + report_id.butsaalt_dans
		return payment_dans

	def get_payment_currency(self, ids):
		report_id=self.browse(ids)
		payment_currency = ''
		if report_id.dans_id:
			payment_currency = report_id.dans_id.currency_id.name
		return payment_currency

	def get_company_payment_line(self,ids):
		report_id = self.browse(ids)
		lines = report_id.account_company_line_ids
		html = """
		<table style="width:100%; font-size:12pt; border:1px solid; border-collapse:collapse; font-family:Times New Roman">	
			"""
		i = 1
		if lines:
			html += """
				<tr>
					<td rowspan="2">№</td>
					<td style="border:1px solid; border-collapse:collapse; text-align:center; width:35%" colspan="2"><b>Хаанаас</b></td>
					<td style="border:1px solid; border-collapse:collapse; text-align:center; width:30%" rowspan="2"><b>Дүн</b></td>
					<td style="border:1px solid; border-collapse:collapse; text-align:center; width:35%" colspan="2"><b>Хаана</b></td>
				</tr>
				<tr>
					<td style="border:1px solid; border-collapse:collapse; text-align:center;"><b>Компани</b></td>
					<td style="border:1px solid; border-collapse:collapse; text-align:center;"><b>Банк, дансны дугаар</b></td>
					<td style="border:1px solid; border-collapse:collapse; text-align:center;"><b>Компани</b></td>
					<td style="border:1px solid; border-collapse:collapse; text-align:center;"><b>Банк, дансны дугаар</b></td>
				</tr>
			"""

			for line in lines:
				haanaas_bank_dans = ''
				if report_id.journal_id and report_id.journal_id.bank_account_id:
					haanaas_bank_dans = report_id.journal_id.bank_account_id.bank_id.name + '-' + report_id.journal_id.bank_account_id.acc_number

				haana_bank_dans = ''
				if line.bank_id and line.dans_id:
					haana_bank_dans = line.bank_id.name + '-' + line.dans_id.acc_number

				html += """
					<tr>
						<td style="font-size:12pt; text-align:center; border:1px solid; border-collapse:collapse;">%s</td>
						<td style="font-size:12pt; text-align:center; border:1px solid; border-collapse:collapse;">%s</td>
						<td style="font-size:12pt; text-align:center; border:1px solid; border-collapse:collapse;">%s</td>
						<td style="font-size:12pt; text-align:center; border:1px solid; border-collapse:collapse;">%s %s</td>
						<td style="font-size:12pt; text-align:center; border:1px solid; border-collapse:collapse;">%s</td>
						<td style="font-size:12pt; text-align:center; border:1px solid; border-collapse:collapse;">%s</td>
					</tr>
				"""%(str(i), report_id.company_id.name, haanaas_bank_dans, "{0:,.2f}".format(line.price_total), report_id.currency_id.name, line.partner_id.name, haana_bank_dans)
				i += 1

			html +="""
				<tr>
					<td style="font-size:12pt; text-align:center; border:1px solid; border-collapse:collapse;"></td>
					<td style="font-size:12pt; text-align:center; border:1px solid; border-collapse:collapse;"><b>Нийт</b></td>
					<td style="font-size:12pt; text-align:center; border:1px solid; border-collapse:collapse;"></td>
					<td style="font-size:12pt; text-align:center; border:1px solid; border-collapse:collapse;"><b>%s %s</b></td>
					<td style="font-size:12pt; text-align:center; border:1px solid; border-collapse:collapse;"></td>
					<td style="font-size:12pt; text-align:center; border:1px solid; border-collapse:collapse;"></td>
				</tr>
			"""%("{0:,.2f}".format(report_id.amount), report_id.currency_id.name)

		html += """
			</table>
		"""
		return html

	def request_print(self):
		model_id = self.env['ir.model'].sudo().search([('model','=','payment.request')], limit=1)
		if not self.flow_id.is_between_account and not self.flow_id.is_cash and not self.flow_id.is_between_company:
			template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','tulburiin_huselt')], limit=1)
		elif self.flow_id.is_between_account:
			template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','dans_hoorond')], limit=1)
		elif self.flow_id.is_between_company:
			template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','company_hoorond')], limit=1)
		else:
			template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','belen_mungu')], limit=1)

		if template:
			res = template.sudo().print_template(self.id)
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

	@api.model
	def create(self, vals):
		res = super(PaymentRequest, self).create(vals)
		company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
		if res.journal_id:
			res.journal_id = self.env['account.journal'].browse(res['journal_id'])
			seq_id = res.journal_id.bank_account_id.payment_sequence_id if res.journal_id and res.journal_id.bank_account_id else False
			res.name = seq_id.next_by_id(seq_id.id) if seq_id else self.env['ir.sequence'].with_company(company_id).next_by_code('account.payment.request')
		return res

class AccountCompanyRequestItem(models.Model):
	_name = 'account.company.request.item'
	_description = 'Account company request item'

	def compute_bank_dans(self):
		res_partner_bank_obj = self.env['res.partner.bank'].search([('partner_id','=',self.partner_id.id),('bank_id','=',self.bank_id.id)])
		return [('id','in',res_partner_bank_obj.ids)]

	sequence = fields.Integer(string='Дараалал', default=1)
	payment_id = fields.Many2one('payment.request', string='Төлбөрийн хүсэлт', ondelete='cascade')
	partner_id = fields.Many2one('res.partner', string='Харилцагч', default=1, required=True)
	bank_id = fields.Many2one('res.bank', string='Харилцагчийн банк', required=True,)
	dans_id = fields.Many2one('res.partner.bank', string='Харилцагчийн данс', required=True, domain=compute_bank_dans)
	price_total = fields.Float(string='Нийт дүн')

	@api.onchange('bank_id','partner_id')
	def onchange_bank_dans(self):
		if self.partner_id:
			domain = {
				'dans_id': self.compute_bank_dans()
			}
			return {'domain':domain}

class ResPartnerBank(models.Model):
	_inherit = 'res.partner.bank'

	code = fields.Char(string='Код')
	payment_sequence_id = fields.Many2one('ir.sequence', string='Авто дугаарлалтын дүрэм', tracking=True, compute='compute_payment_seq')

	@api.depends('acc_number')
	def compute_payment_seq(self):
		for item in self:
			if not item.payment_sequence_id:
				sequence_id = self.env['ir.sequence'].sudo().search([('name','=',item.acc_number + '-дансны PR дугаарлалт')])
				if not sequence_id and item.code:
					vals = {
						'name': item.acc_number + '-дансны PR дугаарлалт',
						'implementation': 'standard',
						'code': item.code,
						'prefix': item.code + '-%(y)s%(month)s-',
						'padding': 3,
						'number_increment': 1,
						'use_date_range': False,
						'active': True,
					}
					sequence_id = self.env['ir.sequence'].sudo().create(vals)
				item.payment_sequence_id = sequence_id.id
			else:
				item.payment_sequence_id.prefix = item.code + '-%(y)s%(month)s-'

	def name_get(self):
		return [(acc.id, '{} - {}'.format(acc.bank_id.name, acc.acc_number) if acc.bank_id else acc.acc_number)
			for acc in self]
