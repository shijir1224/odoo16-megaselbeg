from odoo import fields, models, api
from odoo.exceptions import UserError

class sale_order_pr_create(models.TransientModel):
	_name='sale.order.pr.create'
	_description = 'Purchase Request Create'

	date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
	flow_id = fields.Many2one('dynamic.flow', string='Худалдан авалтын урсгал тохиргоо', required=True, domain="[('model_id.model', '=', 'purchase.request')]")
	partner_id = fields.Many2one('res.partner', string='Ажилтан', required=True, domain="[('employee', '=', True)]", default=lambda self: self.env.user.partner_id)
	line_ids = fields.One2many('sale.order.pr.create.line', 'parent_id', 'Мөр')
	priority_line = fields.Many2one('purchase.request.priority', string='Зэрэглэл', required=False)

	@api.onchange('partner_id')
	def onch_pr_qty(self):
		so_line_obj = self.env['sale.order.line'].search([('id','in',self._context['active_ids'])])
		sale_order_po_line_obj = self.env['sale.order.pr.create.line']
		self.line_ids = False
		line_ids = []

		for line in so_line_obj:
			if line.pr_id:
				raise UserError('%s борлуулалтаас ХА хүсэлт үүссэн байна. %s' % (line.order_id.name, line.pr_id.name))
			qty=0
			if line.order_id.prepayment_amount and (line.order_id.amount_total - line.order_id.uldegdel_tulbur) < line.order_id.prepayment_amount:
				raise UserError('Урьдчилсан орлого ороогүй борлуулалтын захиалга байга! %s' % line.order_id.name)
			quant_ids = self.env['stock.quant'].search([('product_id','=',line.product_id.id),('location_id.usage','=','internal')])
			quant_sum = sum(quant_ids.mapped('quantity'))
			if quant_sum<=0: 
				qty=line.product_uom_qty
			elif line.product_uom_qty>quant_sum:
				qty=line.product_uom_qty-quant_sum
			elif line.product_uom_qty<=quant_sum:
				raise UserError('%s барааны үлдэгдэл хүссэн тоо хэмжээнд хүрж байна' % line.product_id.display_name)
			sale_order_po_line_obj.create({
					'parent_id': self.id,
					'product_id': line.product_id.id,
					'qty': qty,
					'desc': line.order_id.name,
					'sale_price_calculator_line_id': line.sale_price_calculator_line_id.id,
					# 'order_price_calc': line.price_unit,
					'order_price_calc': line.sale_price_calculator_line_id.unit_price,
					
					'sol_id': line.id,
				})
		if not self.line_ids and line_ids:
			self.line_ids = self.env['sale.order.pr.create.line'].create(line_ids)

	def create_pr(self):
		purchase_obj = self.env['purchase.request']
		pr_line_obj = self.env['purchase.request.line']
		flow_line_id = self.env['dynamic.flow.line'].search([('flow_id', '=', self.flow_id.id)], order='sequence', limit=1)
		department_id = False
		if self.partner_id.user_ids:
			department_id = self.partner_id.user_ids[0].department_id.id
		pr_id = purchase_obj.create({
			'flow_id': self.flow_id.id,
			'flow_line_id': flow_line_id.id,
			'partner_id': self.partner_id.id,
			'sub_partner_id': self.line_ids[0].sol_id.order_id.partner_id.id if self.line_ids[0].sol_id.order_id.partner_id else False,
			'date': self.date,
			'pr_department_id': department_id,
			'desc': 'Харилцагч: '+', '.join(self.line_ids.mapped('sol_id.order_id.partner_id.name'))
		})
		for line in self.line_ids:
			pr_line_obj.create({
				'request_id': pr_id.id,
				'product_id': line.product_id.id,
				'requested_qty': line.qty,
				'priority_line': self.priority_line.id,
				'date_required': line.parent_id.date,
				'transportation_cost': line.sale_price_calculator_line_id.transportation_cost if line.sale_price_calculator_line_id else '',
				'custom_tax': line.sale_price_calculator_line_id.custom_tax if line.sale_price_calculator_line_id else '',
				'internal_shipping': line.sale_price_calculator_line_id.internal_shipping if line.sale_price_calculator_line_id else '',
				'internal_costing': line.sale_price_calculator_line_id.internal_costing if line.sale_price_calculator_line_id else '',
				'order_price_calc': line.order_total_price_calc,
			})
			line.sol_id.pr_id = pr_id.id

class sale_order_pr_create_line(models.TransientModel):
	_name='sale.order.pr.create.line'
	_description = 'Purchase Request Create'

	desc = fields.Char(string='Name')
	parent_id = fields.Many2one('sale.order.pr.create', ondelete='cascade', string='Parent')
	product_id = fields.Many2one('product.product', readonly=True)
	qty_on_wait = fields.Float(string='Захиалгад байгаа', compute='compute_qty_on_wait', store=True ,readonly=True)
	qty_on_hand = fields.Float(string='Гарт байгаа', compute='compute_qty_on_hand', store=True ,readonly=True)
	qty = fields.Float(string='ХА Хүсэлт тоо хэмжээ', readonly=True)
	sale_price_calculator_line_id = fields.Many2one('sale.price.calculator.line', string='Sale Price Calculator Line ID')
	order_price_calc = fields.Float(string='Үнэ тооцолол дүн', readonly=True)
	order_total_price_calc = fields.Float(string='Үнэ тооцолол нийт дүн', readonly=True, compute='compute_qty_on_hand', store=True)
	sol_id = fields.Many2one('sale.order.line', 'SO line ID')

	@api.depends('qty', 'product_id')
	def compute_qty_on_wait(self):
		for item in self:
			so_line_obj = self.env['purchase.order.line'].search([('product_id','=',item.product_id.id)])
			item.qty_on_wait = sum(so_line_obj.mapped('product_qty')) - sum(so_line_obj.mapped('qty_received'))

	@api.depends('product_id')
	def compute_qty_on_hand(self):
		for item in self:
			quant_ids = self.env['stock.quant'].search([('product_id','=',item.product_id.id),('location_id.usage','=','internal')])
			item.qty_on_hand = sum(quant_ids.mapped('quantity'))
			item.order_total_price_calc = item.qty * item.order_price_calc