from odoo import api, fields, models

class StockMove(models.Model):
	_inherit = 'stock.move'
	
	def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
									   credit_account_id, svl_id, description):
		
		self.ensure_one()

		rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value,
																	 debit_account_id, credit_account_id,svl_id, description)
		if self.picking_id.other_expense_id:
			account_id = False
			analytic_distribution = False
			partner_id =False
			if self.picking_id.other_expense_id:
				if self.expense_line_id and self.expense_line_id.account_id :
					account_id = self.expense_line_id.account_id.id
				elif self.picking_id.other_expense_id.transaction_value_id and self.picking_id.other_expense_id.transaction_value_id.account_id:
					if self.expense_line_id and self.expense_line_id.account_id :
						account_id = self.expense_line_id.account_id.id
					else:
						account_id = self.picking_id.other_expense_id.transaction_value_id.account_id.id
				elif self.picking_id.other_expense_id.account_id:
					account_id = self.picking_id.other_expense_id.account_id.id
				if self.expense_line_id and self.expense_line_id.analytic_distribution:
					analytic_distribution = self.expense_line_id.analytic_distribution
				if self.expense_line_id and self.expense_line_id.parent_id and self.expense_line_id.parent_id.account_partner_id and self.expense_line_id.parent_id.is_partner == True:
					partner_id = self.expense_line_id.parent_id.account_partner_id.id
					rslt['debit_line_vals']['partner_id'] = partner_id
					rslt['credit_line_vals']['partner_id'] = partner_id
				elif self.expense_line_id and self.expense_line_id.res_partner_id:
					partner_id = self.expense_line_id.res_partner_id.id
					rslt['debit_line_vals']['partner_id'] = partner_id
					rslt['credit_line_vals']['partner_id'] = partner_id
				elif self.picking_id.other_expense_id.analytic_distribution:
					analytic_distribution = self.picking_id.other_expense_id.analytic_distribution
				elif self.picking_id.other_expense_id.transaction_value_id and self.picking_id.other_expense_id.transaction_value_id.analytic_distribution:
					analytic_distribution = self.picking_id.other_expense_id.transaction_value_id.analytic_distribution
			#                 if self.picking_id.other_expense_id.branch_id:
			#                     dest_branch =  self.picking_id.other_expense_id.branch_id.id #Шаардах дээрээс буруу бранч аваад байна.
			if self.picking_id.other_expense_id.department_id and self.picking_id.other_expense_id.department_id.branch_id:
				rslt['debit_line_vals']['branch_id'] = self.picking_id.other_expense_id.department_id.branch_id.id
				rslt['credit_line_vals']['branch_id'] = self.picking_id.other_expense_id.department_id.branch_id.id
			# print ('analytic_distribution3 ',analytic_distribution)
			if analytic_distribution:
				rslt['debit_line_vals']['analytic_distribution'] = analytic_distribution
				rslt['credit_line_vals']['analytic_distribution'] = analytic_distribution
			# print('-------------------------', account_id)
			# print ('analytic_distribution123123 ',analytic_distribution)
			if account_id:
				if self._is_out():
					rslt['debit_line_vals']['account_id'] = account_id
					# rslt['debit_line_vals']['analytic_distribution'] = analytic_distribution
				else:
					rslt['credit_line_vals']['account_id'] = account_id
					# rslt['credit_line_vals']['analytic_distribution'] = analytic_distribution
		return rslt

class StockPickingLine(models.Model):
	_inherit = 'stock.move.line'

	is_qualified = fields.Selection([('yes','Тийм'), ('no','Үгүй')], string='Шаардлага хангасан эсэх')
	no_quality = fields.Char(string='Тайлбар')
	code = fields.Selection(related='picking_type_id.code', string='Code')
	internal_approve = fields.Boolean(related='picking_id.internal_approve', string='Бараа явуулахыг зөвшөөрөх')
	is_sent = fields.Boolean(string='Мэдэгдэл очсон эсэх', readonly=True)

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	car_plate_number = fields.Char(string='Улсын дугаар')
	scrap_id = fields.Integer(compute='get_scrap_ids')
	purchase_id = fields.Many2one('purchase.order', related='move_ids.purchase_line_id.order_id', string="Purchase Orders", readonly=True, store=True)
	shaardah_partner_id = fields.Many2one('res.partner', string='Хүсэлт гаргасан ажилтан')

	# Гологдол баримтын тоо хэмжээ 
	def get_scrap_ids(self):
		for i in self:
			if i.picking_type_code == 'internal':
				scraps = self.env['stock.scrap.multi'].search_count([('picking_id','=',i.id)])
				i.scrap_id = scraps
			else:
				i.scrap_id = 0

	# Гологдол баримтууд харах
	def view_scrap_ids(self):
		tree_view = self.env.ref("mw_stock.stock_scrap_tree_view", raise_if_not_found=False)
		form_view = self.env.ref("mw_stock.stock_scrap_multi_form_view", raise_if_not_found=False)
		lists = self.env['stock.scrap.multi'].search([('picking_id','=',self.id)])
		action = {
			"type": "ir.actions.act_window",
			"name": "Гологдол",
			"res_model": "stock.scrap.multi",
			"view_mode": "tree,form",
			"domain": [("id", "in", lists.ids)],
		}
		if tree_view and form_view:
			action["views"] = [(tree_view.id, "tree"), (form_view.id, "form")]
		return action

	@api.onchange('state')
	def onchange_picking_state(self):
		for item in self:
			if item.state in ['done']:
				item.other_expense_id.product_expense_line.get_done_qty()
