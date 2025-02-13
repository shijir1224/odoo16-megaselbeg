# -*- encoding: utf-8 -*-

# from openerp.tools.safe_eval import safe_eval
from odoo import api, fields, models, _

#def _round(value):
#    return round(value / 2) * 2

class consume_order_moves(models.TransientModel):
	_name = 'consume.order.moves'
	_inherit = 'analytic.mixin'
	_description = "Asset move"
	
	def action_asset_moves(self):
		''' Хөрөнгө эзэмшигчийг солих'''
		context=self._context
		asset_obj = self.env['consumable.material.in.use']
		history_obj = self.env['consume.order.history']

		if context.get('active_ids',False) and len(context['active_ids'])>1:
			move_ids=[]
			assets = asset_obj.browse( context['active_ids'])
			for asset in assets:
				obj = self
				history_vals = {'use_id':asset.id,'type':'move'}
				line_vals=[]
				if obj.description:
					history_vals.update({'name': obj.description})
				
				vals = {}
		
				if obj.owner_dep_id:
					vals.update({'department_id':obj.owner_dep_id.id})
					history_vals.update({
										 'dep_id': asset.department_id.id,
										 })
				if obj.owner_id:
					vals.update({'owner_id':obj.owner_id.id})
					history_vals.update({
										'new_owner_id': obj.owner_id.id
										})
					if asset.owner_id:
						history_vals.update({
										 'owner_ids': [asset.owner_id.id],
										 })
				if  obj.branch_id:
					vals.update({'branch_id':obj.branch_id.id})
					# Хөрөнгө шилжүүлэхэд гүйлгээ хийхгүй
					history_vals.update({
										 'branch_id': asset.branch_id.id,
										 })
					
				if obj.account_id:
					vals.update({'account_id':obj.account_id.id})
					history_vals.update({
										 'account_id': asset.account_id.id,
										 })
					
				if obj.analytic_distribution:
					vals.update({'analytic_distribution':obj.analytic_distribution})
					history_vals.update({
										 'analytic_distribution': asset.analytic_distribution,
										 })
				# print('-ssssss', self.qty)
				if vals:
					asset.write({'qty':asset.qty-self.qty})
					# vals['qty']=self.qty
					vals['doc_number']=asset.doc_number
					vals['price']=asset.price
					vals['note']=asset.note
					vals['related_product_move_id'] = asset.related_product_move_id and asset.related_product_move_id.id or False
					vals['expense_line_id'] = asset.expense_line_id and asset.expense_line_id.id or False
					vals['type_id'] = asset.type_id and asset.type_id.id or False
					vals['product_id'] = asset.product_id and asset.product_id.id or False
					asset.write(vals)
					asset_lines = asset.depreciation_line_ids.filtered(lambda r: not r.move_id)
					if asset_lines:
						asset_lines.write({'owner_id': obj.owner_id.id})
					# print('-vals', vals)
					# print(k)
				if history_vals:
					history_vals.update({'date': obj.date})
					history_obj.create( history_vals)
				# print(l)
		
		#1 хөрөнгө
		else:
			if self.is_qty and self.qty>0:
				asset = asset_obj.browse( context['active_id'])
				obj = self
				history_vals = {'use_id':asset.id,'type':'move','qty':self.qty}
				line_vals=[]
				if obj.description:
					history_vals.update({'name': obj.description})
				
				vals = {}
		
				if obj.owner_dep_id:
					vals.update({'department_id':obj.owner_dep_id.id})
					history_vals.update({
										 'dep_id': asset.department_id.id,
										 })
				if obj.owner_id:
					history_vals.update({
										'new_owner_id': obj.owner_id.id
										})
					vals.update({'owner_id':obj.owner_id.id})
					if asset.owner_id:
						history_vals.update({
										 'owner_ids': [asset.owner_id.id],
										 })
				if obj.branch_id:
					vals.update({'branch_id':obj.branch_id.id})
					# Хөрөнгө шилжүүлэхэд гүйлгээ хийхгүй
					history_vals.update({
										'branch_id': asset.branch_id.id,
										})
				
				if obj.account_id:
					vals.update({'account_id':obj.account_id.id})
					history_vals.update({
										 'account_id': asset.account_id.id,
										 })
					
				if obj.analytic_distribution:
					vals.update({'analytic_distribution':obj.analytic_distribution})
					history_vals.update({
										 'analytic_distribution': asset.analytic_distribution,
										 })
				if vals:
					asset.write({'qty':asset.qty-self.qty})
					vals['qty']=self.qty
					vals['doc_number']=asset.doc_number
					vals['price']=asset.price
					vals['note']=asset.note
					vals['related_product_move_id'] = asset.related_product_move_id and asset.related_product_move_id.id or False
					vals['expense_line_id'] = asset.expense_line_id and asset.expense_line_id.id or False
					vals['type_id'] = asset.type_id and asset.type_id.id or False
					vals['product_id'] = asset.product_id and asset.product_id.id or False
					asset.write(vals)
					asset_lines = asset.depreciation_line_ids.filtered(lambda r: not r.move_id)
					if asset_lines:
						asset_lines.write({'owner_id': obj.owner_id.id})
				if history_vals:
					history_vals.update({'date': obj.date})
					history_obj.create( history_vals)
			else:
				asset = asset_obj.browse( context['active_id'])
				obj = self
				history_vals = {'use_id':asset.id,'type':'move'}
				line_vals=[]
				if obj.description:
					history_vals.update({'name': obj.description})

				vals = {}
		
				if obj.owner_dep_id:
					vals.update({'department_id':obj.owner_dep_id.id})
					history_vals.update({
										 'dep_id': asset.department_id.id,
										 })
				if obj.owner_id:
					history_vals.update({
										'new_owner_id': obj.owner_id.id
										})
					vals.update({'owner_id':obj.owner_id.id})
					if asset.owner_id:
						history_vals.update({
										 'owner_ids': [asset.owner_id.id],
										 })
	
				if  obj.branch_id:
					vals.update({'branch_id':obj.branch_id.id})
					# Хөрөнгө шилжүүлэхэд гүйлгээ хийхгүй
					history_vals.update({
										 'branch_id': asset.branch_id.id,
										 })
					
				if  obj.account_id:
					vals.update({'account_id':obj.account_id.id})
					history_vals.update({
										 'account_id': asset.account_id.id,
										 })
					
				if  obj.analytic_distribution:
					vals.update({'analytic_distribution':obj.analytic_distribution})
					history_vals.update({
										 'analytic_distribution': asset.analytic_distribution,
										 })
					
				if vals:
					asset.write(vals)
					asset_lines = asset.depreciation_line_ids.filtered(lambda r: not r.move_id)
					if asset_lines:
						asset_lines.write({'owner_id': obj.owner_id.id})
				if history_vals:
					history_vals.update({'date': obj.date})
					history_obj.create( history_vals)
		return {'type': 'ir.actions.act_window_close'}
	
	description = fields.Text('Description')
	owner_ids = fields.Many2many('res.partner','consum_use_wiz_owner_rel','use_id','owner_id','Owner')
	owner_id = fields.Many2one('res.partner', 'Owner', domain="[('employee','=',True)]")
	owner_dep_id = fields.Many2one('hr.department', 'New department', )
	date =  fields.Datetime('Date', required=True)
	branch_id = fields.Many2one('res.branch', 'New Branch', )
	account_id = fields.Many2one('account.account', 'Зардлын данс')
	analytic_account_id = fields.Many2one('account.analytic.account', 'Шинжилгээний данс')
	
	is_qty = fields.Boolean('Is QTY')
	qty = fields.Float('QTY')
	

	def _get_old_values(self,  field, context=None):
		asset = self.env['account.asset'].browse(context['active_id'])
		if field == 'journal_id':
			return asset.journal_id.id
		return asset.category_id.id
