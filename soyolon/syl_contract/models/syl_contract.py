from odoo import fields, models, _, api
from odoo.exceptions import UserError
from datetime import date

class ContractPaymentType(models.Model):
	_name='contract.payment.type'

	name=fields.Char('Төлбөрийн хэлбэр')
class ContractProcessType(models.Model):
	_name='contract.process.type'

	name=fields.Char('Нэр')

class ContractDocumentReal(models.Model):
	_inherit = "contract.document.real"

	no_date = fields.Char('Гэрээний хугацааны тайлбар', tracking=True)
	part_type_id = fields.Many2one(
		'contract.part.type', 'Гэрээнд оролцох хэлбэр', tracking=True, store=True)
	payment_sum = fields.Float(u'Гэрээний үнийн дүн', tracking=True)
	in_deal_sum = fields.Selection(
		[('yes', 'Тийм'), ('no', 'Үгүй')], 'Их хэмжээний хэлцэл эсэх', tracking=True)
	contract_days = fields.Integer(string='Үргэлжилэх хугацаа/Өдөр/', compute='find_period_days')
	contract_department_id=fields.Many2one('hr.department', 'Гэрээний хэрэгжилтийг хариуцах хэлтэс, нэгж')
	attachment_other = fields.Many2many('ir.attachment', 'contract_document_attach', 'contract_id', 'attachment_id' ,string='Батлагдсан гэрээ')
	other_desc=fields.Char('Бусад шаардлагатай мэдээлэл')
	connect_desc=fields.Char('Холбогдох баримт мэдээлэл')
	checklist_id =fields.One2many('contract.checklist', 'parent_id', 'Vote')
	flow_user_id =fields.One2many('contract.flow.user', 'parent_id', 'Print', readonly=True)
	company_type1 = fields.Selection([('person','Хувь хүн'),('company','Компани'), ('goverment','Төрийн байгууллага'),('not_goverment', 'Төрийн бус байгууллага')], 'Харилцагчийн төрөл',   tracking=True)
	payment_type_id=fields.Many2one('contract.payment.type', 'Төлбөрийн хэлбэр')
	process_type_id=fields.Many2one('contract.process.type', 'Гэрээний явцын төлөв')
	date_char=fields.Char('Үргэлжлэх хугацаа')
	attachment_act = fields.Many2many('ir.attachment', 'contract_document_attach_act', 'contract_id', 'attachment_act_id' ,string=' Гэрээ дүгнэх акт')
	confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids')
	confirm_count = fields.Float(string='Батлах хэрэглэгчийн тоо')

			

	def set_number(self):
		if not self.name:
			if self.type_id.number:
				self.name = str(self.type_id.number + '-' +
								self.env['ir.sequence'].next_by_code('contract.document.real'))
			else:
				raise UserError(
					_(u'Төрлийн дугаарлалтын тайлбар ороогүй байна!'))

	@api.onchange('date_to','date_from')
	def find_period_days(self):
		for i in self:
			if i.date_to and i.date_from:
				period = i.date_to - i.date_from
				i.contract_days = period.days
			else:
				i.contract_days = 0

	def action_next_stage(self):
		res = super(ContractDocumentReal, self).action_next_stage()
		self.update_flow_user_line()
		return res

	def update_flow_user_line(self):
		if self.history_ids:
			mapped_flow = self.history_ids.mapped('flow_line_id')
			if not self.flow_user_id:
				for item in mapped_flow:
					history_obj = self.history_ids.filtered(lambda r: r.flow_line_id.id == item.id)
					self.flow_user_id.create({
						'parent_id': self.id,
						'flow_line_id': item.id,
						'user_id': history_obj[0].user_id.id,
						'date': history_obj[0].date
					})
			else:
				self.flow_user_id.unlink()
				for item in mapped_flow:
					history_obj = self.history_ids.filtered(lambda r: r.flow_line_id.id == item.id)
					self.flow_user_id.create({
						'parent_id': self.id,
						'flow_line_id': item.id,
						'user_id': history_obj[0].user_id.id,
						'date': history_obj[0].date
					})
	@api.depends('flow_line_id', 'flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
			next_flow_line_id = item.flow_line_next_id
			if next_flow_line_id:
				ooo = next_flow_line_id._get_flow_users(self.branch_id, False)
				temp_users = ooo.ids if ooo else []
				item.confirm_user_ids = [(6, 0, temp_users)]
				item.confirm_count = len(item.sudo().confirm_user_ids)
			else:
				item.confirm_user_ids = False
				item.confirm_count = 0
				
class ContractType(models.Model):
	_inherit = 'contract.type'

	number = fields.Char('Дугаарлалт')

class ContractPartType(models.Model):
	_name = 'contract.part.type'
	_description = 'Гэрээнд оролцох хэлбэр'

	name = fields.Char('Нэр')


class ContractChecklist(models.Model):
	_name = 'contract.checklist'
	_description=' contract checklist'


	user_id=fields.Many2one('res.users', 'Санал өгөх ажилтан')
	description=fields.Char('Санал')
	parent_id=fields.Many2one('contract.document.real',  'Contract')


class ContractFlowUser(models.Model):
	_name='contract.flow.user'
	_order='date asc'

	parent_id = fields.Many2one('contract.document.real','Хүсэлт', ondelete='cascade')
	user_id = fields.Many2one('res.users','Өөрчилсөн Хэрэглэгч')
	date = fields.Datetime('Огноо')
	flow_line_id = fields.Many2one('dynamic.flow.line', 'Төлөв')
  

class ContractRealPaymentLine(models.Model):
	_inherit = 'contract.real.payment.line'

	payment_request_id = fields.Many2one('payment.request','Төлбөрийн хүсэлт')
	state = fields.Char(related='payment_request_id.state',string='Төлбөрийн хүсэлт төлөв')
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлбөрийн хүсэлт төлөв', tracking=True,related='payment_request_id.flow_line_id')
	# pay_cate = fields.Selection([('type1', 'Эхний төлбөр'), ('type2', 'Дундын төлбөр'), ('type3', 'Сүүлийн үлдэгдэл'), ('type4', 'Барьцаа')], 'Tөлбөрийн төрөл')
	# pay_company_id = fields.Many2one('res.company', 'Kомпани')
	# pay_department_id = fields.Many2one('hr.department', 'Хэлтэс')
	# cont_invoice = fields.Many2many('ir.attachment', 'cont_invoice_attach_rel', 'cont_inv', 'attach_id',string='Нэхэмжлэх')
	# cont_act = fields.Many2many('ir.attachment','cont_act_attach_rel', 'item_id', 'cont_act',string='Акт')
	# cont_dxakt = fields.Many2many('ir.attachment', 'cont_dxakt_attach_rel', 'item_id', 'cont_a',string='ДХАКТ')


	def auto_contract_payment_request(self):
		for obj in self:
			# if not obj.payment_request_id and obj.contract_amount_graph_id.state_type in ['done', 'ended']:
			if not obj.payment_request_id and obj.contract_amount_graph_id.state_type !='draft':
				cont =obj.contract_amount_graph_id
				payment_pool=self.env['payment.request']
				payment_flow = self.env['dynamic.flow'].search([('model_id.model', '=', 'payment.request'),('company_id','=', cont.res_company_id.id)], order='sequence',limit=1)
				# narration = self.env['payment.request.narration'].search([('name', '=', 'Гэрээ')],limit=1)
				data_id = payment_pool.create({
					# 'contract_id': cont.id,
					# 'description' : cont.contract_name,
					'user_id' : cont.employee_id.user_id.id,
					'department_id' : cont.employee_id.department_id.id,
					'amount' : obj.paid_amount,
					'flow_id': payment_flow.id,
					'narration_id': 1,
					'payment_ref': cont.name,
					'partner_id': cont.partner_id.id,
					'paid_date':obj.paid_date,
					'payment_type':'dotood',
				
				})

   