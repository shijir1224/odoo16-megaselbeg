# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api

class PurchaseAccView(models.Model):
	_name = "purchase.acc.view"
	_description = "purchase acc view"
	_auto = False

	partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
	company_id = fields.Many2one('res.company', string='Company', readonly=True)
	purchase_id = fields.Many2one('purchase.order', string='Purchase', readonly=True)
	account_move_line_id = fields.Many2one('account.move.line', string='Journal item', readonly=True)
	account_id = fields.Many2one('account.account', string='Account', readonly=True)
	po_state = fields.Char(string='PO state', readonly=True)
	po_date = fields.Datetime('PO date', readonly=True)
	acc_state = fields.Char(string='Journal item state', readonly=True)
	acc_date = fields.Date('Journal item date', readonly=True)
	debit = fields.Float('Debit', readonly=True)
	credit = fields.Float('Credit', readonly=True)
	user_id = fields.Many2one('res.users', string='Created user', readonly=True)
	
	def _select(self):
		return """
			SELECT
				aml.id,
				aml.id as account_move_line_id,
				aml.account_id,
				aml.debit,
				aml.credit,
				pol.order_id as purchase_id,
				po.partner_id,
				po.company_id,
				po.state as po_state,
				po.date_order as po_date,
				po.create_uid as user_id,
				am.state as acc_state,
				aml.date as acc_date
		"""

	def _from(self):
		return """
			FROM account_move_line AS aml
			left join account_move am on (am.id=aml.move_id)
			left join stock_move sm on (sm.id=am.stock_move_id)
			left join account_move_purchase_order_rel rel on (rel.account_move_id=aml.move_id)
			left join purchase_order_line pol on (pol.order_id=rel.purchase_order_id or pol.id=sm.purchase_line_id)
			left join purchase_order po on (pol.order_id=po.id)
		"""

	def _group_by(self):
		return """
			group by
			aml.id,
				aml.account_id,
				aml.debit,
				aml.credit,
				pol.order_id,
				po.partner_id,
				po.state,
				po.date_order,
				po.create_uid,
				am.state,
				aml.date,
				po.company_id
		"""

	def _having(self):
		return """
		   
		"""

	def _where(self):
		return """
		where pol.state not in ('cancel') and am.state='posted' and po.id is not null
		"""

	def union_all(self):
		return """"""
		
	def _select2(self):
		return """
			
		"""

	def _from2(self):
		return """
			
		"""

	def _group_by2(self):
		return """
			
		"""

	def _having2(self):
		return """
		   
		"""

	def _where2(self):
		return """"""

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
			CREATE OR REPLACE VIEW %s AS (
				%s
				%s
				%s
				%s
				%s
				%s
				%s
				%s
				%s
				%s
				%s
			)
		""" % (self._table, self._select(), self._from(), self._where(), self._group_by(),self._having(), self.union_all(), self._select2(), self._from2(), self._where2(), self._group_by2(),self._having2())
		)


class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	def view_po_am(self):
		action = self.env.ref('account.action_account_moves_all_tree')
		vals = action.read()[0]
		aml_ids = self.env['account.move.line'].search([('move_id','in',self.invoice_ids.ids)]).ids
		aml_ids += self.env['account.move.line'].search([('move_id.stock_move_id.purchase_line_id.order_id','=',self.id)]).ids
		domain = [('id','in',aml_ids),('move_id.state','=','posted')]
		vals['domain'] = domain
		vals['context'] = {'search_default_group_by_account':1}
		return vals
	
	zamd_amount_debit = fields.Float('Замд Дт', compute='_zamd_compute',store=True)
	zamd_amount_credit = fields.Float('Замд Кр', compute='_zamd_compute',store=True)

	@api.depends('invoice_ids', 'invoice_ids.line_ids', 'order_line.move_ids', 'order_line.move_ids.account_move_ids', 'order_line.move_ids.account_move_ids.line_ids')
	def _zamd_compute(self):
		for item in self:
			debit=0
			credit=0
			for inv in item.invoice_ids:
				for line in inv.line_ids:
					if line.account_id.id==557:
						debit+=line.debit
						credit+=line.credit
			for oline in item.order_line:
				for  sline in oline.move_ids:
					for am in sline.account_move_ids:
						for aml in am.line_ids:
							if aml.account_id.id==557:
								debit+=aml.debit
								credit+=aml.credit
			item.zamd_amount_debit = debit
			item.zamd_amount_credit = credit
