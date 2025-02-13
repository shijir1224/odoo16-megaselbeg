# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import fields, _, api
from odoo.models import Model
from odoo.exceptions import ValidationError, UserError
from odoo.tools.misc import get_lang
from odoo.tools.float_utils import float_compare, float_round
from .purchase_order import READONLY_STATES

class PurchaseOrderComparison(Model):
	_name = 'purchase.order.comparison'
	_description = 'Purchase order comparison'
	_order = 'create_date desc'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

	@api.model
	def _default_picking_type(self):
		return self._get_picking_type(self.env.context.get('company_id', self.env.company.id))

	picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=READONLY_STATES,
									  required=True, default=_default_picking_type,
									  domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
									  help="This will determine operation type of incoming shipment")
	name = fields.Char('Order Reference', required=True, index=True, copy=False, default='/')
	partner_ids = fields.Many2many('res.partner', 'res_partner_purchase_order_comparison_rel',
								   'purchase_order_comparison_id', 'partner_id', string='Partners', required=True)
	company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
	date_order = fields.Datetime('Comparison Deadline', required=True, index=True, copy=False, default=fields.Datetime.now(),
								 help="Depicts the date within which the Quotation should be confirmed and converted into a purchase order.")
	line_ids = fields.One2many('purchase.order.comparison.line', 'comparison_id', string='Lines', required=True, copy=True)
	winning_partner = fields.Many2one('res.partner', string='Winning partner', domain="[('id', 'in', partner_ids)]", copy=False)
	winning_comment = fields.Char('Winning comment', copy=False)
	winning_po_id = fields.Many2one('purchase.order', string='Winning Order', readonly=True)
	branch_id = fields.Many2one('res.branch', 'Branch', default=lambda self: self.env.user.branch_id)
	state = fields.Selection([('draft', 'Draft'),
							  ('rfq_created', 'RFQ created'),
							  ('vote_started', 'Vote started'),
							  ('vote_ended', 'Vote ended'),
							  ('ended', 'Comparison Ended')], string='State', default='draft', tracking=True)
	related_po_ids = fields.One2many('purchase.order', 'comparison_id', string='Related purchase orders')
	user_id = fields.Many2one('res.users', required=True, string='Comparison Representative', default=lambda self: self.env.user)
	related_po_count = fields.Integer(compute='_compute_related_order_count')
	vote_ids = fields.One2many('purchase.order.comparison.vote', 'comparison_id', string='Votes')
	vote_result_ids = fields.One2many('purchase.order.comparison.vote.result', 'comparison_id', string='Vote results')
	product_id = fields.Many2one('product.product', related='line_ids.product_id', string='Product')
	all_voted = fields.Boolean(compute='_compute_vote')
	vote_percentage = fields.Float('Vote progress', compute='_compute_vote')

	@api.model
	def _get_picking_type(self, company_id):
		if self.env.user.warehouse_id.company_id.id == company_id:
			picking_type = self.env.user.warehouse_id.in_type_id
		else:
			picking_type = self.env.user.warehouse_ids.filtered(lambda w: w.company_id.id == company_id).mapped('in_type_id')
		return picking_type[:1]

	@api.onchange('company_id')
	def _onchange_company_id(self):
		self.picking_type_id = self._get_picking_type(self.company_id.id)

	def _compute_vote(self):
		for obj in self:
			vote_ids = obj.vote_ids
			obj.all_voted = False not in obj.vote_ids.mapped('is_voted')
			if obj.vote_ids:
				vote_count = len(vote_ids)
				voted_count = len(vote_ids.filtered(lambda l: l.is_voted is True))
				obj.vote_percentage = voted_count / vote_count * 100
			else:
				obj.vote_percentage = 0

	def _compute_related_order_count(self):
		for obj in self:
			if obj.related_po_ids:
				obj.related_po_count = len(obj.related_po_ids)
			else:
				obj.related_po_count = False

	def action_view_related_purchase_orders(self):
		self.ensure_one()
		action = self.sudo().env.ref('purchase.purchase_form_action').read()[0]
		action['domain'] = [
			('id', 'in', self.related_po_ids.ids),
		]
		action['context'] = {'create': False}
		return action

	def get_po_vals(self, partner_id):
		return {'partner_id': partner_id.id,
				'date_order': self.date_order,
				'company_id': self.company_id.id,
				'origin': self.name,
				'branch_id': self.branch_id.id,
				'state': 'comparison',
				'picking_type_id': self.picking_type_id.id,
				'user_id': self.user_id.id,
				'comparison_id': self.id}

	@api.model
	def create(self, vals):
		company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
		self_comp = self.with_company(company_id)
		seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals.get('date_order', datetime.now())))
		vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase.order.comparison',
																 sequence_date=seq_date) or '/'
		return super(PurchaseOrderComparison, self).create(vals)

	@api.constrains('line_ids')
	def _check_line_ids(self):
		for obj in self:
			if not obj.line_ids:
				raise ValidationError(_('Please fill the lines'))

	@api.constrains('partner_ids')
	def _check_partner_ids(self):
		for obj in self:
			if len(obj.partner_ids) < 2:
				raise ValidationError(_('2 or more partners must be chosen'))

	def create_purchase_orders(self):
		self.ensure_one()
		if not self.related_po_ids:
			if self.state != 'draft':
				raise UserError(_('Record must be in Draft state'))
			if self.user_id != self.env.user:
				raise UserError(_('Only the Comparison Representative can create purchase orders'))
			for obj in self.partner_ids:
				order_id = self.env['purchase.order'].with_context(from_comparison=True).create(self.get_po_vals(obj))
				for line in self.line_ids:
					po_line_id = self.env['purchase.order.line'].with_context(from_comparison=True).create(
						line.get_po_line_vals(order_id))
					line.order_line_ids |= po_line_id
		else:
			self.related_po_ids.write({'state': 'comparison'})
		self.to_rfq_created()

	def to_draft(self):
		self.ensure_one()
		self.related_po_ids.button_cancel()
		self.vote_result_ids.with_context(from_comparison=True).unlink()
		self.vote_ids.with_context(from_comparison=True).unlink()
		# self.related_po_ids.with_context(from_comparison=True).unlink()
		self.write({'state': 'draft'})

	def unlink(self):
		for obj in self:
			if obj.state != 'draft':
				raise UserError(_('Record must be in Draft state'))
		self.related_po_ids.button_cancel()
		self.related_po_ids.with_context(from_comparison=True).unlink()
		return super(PurchaseOrderComparison, self).unlink()

	def start_vote_button(self):
		self.ensure_one()
		if self.user_id != self.env.user:
			raise UserError(_('Only the Comparison Representative can start the vote'))
		if self.state != 'rfq_created':
			raise UserError(_("Record must be in 'RFQ created' state"))
		wizard = self.env['purchase.order.comparison.vote.wizard'].create({'comparison_id': self.id, 'wizard_type': 'start'})
		action = \
		self.sudo().env.ref('mw_purchase_comparison.action_purchase_order_comparison_vote_wizard').read()[0]
		action['res_id'] = wizard.id
		action['context'] = {'create': False}
		return action

	def start_vote(self):
		for obj in self.partner_ids:
			self.env['purchase.order.comparison.vote.result'].create({'comparison_id': self.id, 'partner_id': obj.id})
		self.write({'state': 'vote_started'})

	def revert_start_vote(self):
		self.vote_result_ids.unlink()
		self.to_rfq_created()

	def to_rfq_created(self):
		return self.write({'state': 'rfq_created'})

	def vote(self):
		self.ensure_one()
		if self.env.user.id not in self.vote_ids.mapped('user_id').ids:
			raise UserError(_('You do not have permission to vote'))
		wizard = self.env['purchase.order.comparison.vote.wizard'].create({'comparison_id': self.id, 'wizard_type': 'primary'})
		action = \
		self.sudo().env.ref('mw_purchase_comparison.action_purchase_order_comparison_vote_wizard').read()[0]
		action['res_id'] = wizard.id
		action['context'] = {'create': False, 'partner_domain': [('id', 'in', self.partner_ids.ids)]}
		return action

	def _add_voter(self):
		wizard = self.env['purchase.order.comparison.vote.wizard'].create({'comparison_id': self.id, 'wizard_type': 'start'})
		action = \
		self.sudo().env.ref('mw_purchase_comparison.action_purchase_order_comparison_vote_wizard').read()[0]
		action['res_id'] = wizard.id
		domain_users = self.vote_ids.mapped('user_id').ids
		action['context'] = {'create': False, 'user_domain': [('id', 'not in', domain_users)]}
		return action

	def add_voter(self):
		self.ensure_one()
		if self.user_id != self.env.user:
			raise UserError(_('Only the Comparison Representative can add new voter'))
		if self.state != 'vote_started':
			raise UserError(_("Record must be in 'Vote started' state"))
		return self._add_voter()

	def end_vote(self):
		self.ensure_one()
		if not self.all_voted and not self.env.context.get('base_wizard_confirmed', False):
			wizard = self.env['base.confirm.wizard'].create({'res_model': self._name,
															 'res_id': self.id,
															 'message': _(
																 'Not all voters have voted. Are you sure you want to end the vote?'),
															 'function_name': 'end_vote'})

			action = self.sudo().env.ref('mw_base.action_base_confirm_wizard').read()[0]
			action['res_id'] = wizard.id
			return action
		if self.user_id != self.env.user:
			raise UserError(_('Only the Comparison Representative can end the vote.'))
		self.write({'state': 'vote_ended'})

	def revert_end_vote(self):
		self.write({'state': 'vote_started'})

	def end_comparison(self):
		self.ensure_one()
		winning_order = self.related_po_ids.filtered(lambda l: l.partner_id == self.winning_partner)
		losing_orders = self.related_po_ids - winning_order
		losing_orders.button_cancel()
		winning_order.button_draft()
		winning_order.button_confirm()
		if self.user_id != self.env.user:
			raise UserError(_('Only the Comparison Representative can end the comparison.'))
		self.write({'state': 'ended', 'winning_po_id': winning_order.id})


class PurchaseOrderComparisonLine(Model):
	_name = 'purchase.order.comparison.line'
	_description = 'Purchase order comparison line'

	comparison_id = fields.Many2one('purchase.order.comparison', required=True, string='Comparison', ondelete='cascade')
	product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)], change_default=True)
	name = fields.Text(string='Description', required=True)
	product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
	product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
								  domain="[('category_id', '=', product_uom_category_id)]", required=True)
	product_packaging_id = fields.Many2one('product.packaging', string='Packaging',
										   domain="[('purchase', '=', True), ('product_id', '=', product_id)]",
										   check_company=True)
	product_packaging_qty = fields.Float('Packaging Quantity')
	product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True)
	taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
	order_line_ids = fields.One2many('purchase.order.line', 'comparison_line_id', string='Order lines')
	company_id = fields.Many2one('res.company', related='comparison_id.company_id', string='Company', store=True, readonly=True)
	date_order = fields.Datetime(related='comparison_id.date_order')
	partner_ids = fields.Many2many(related='comparison_id.partner_ids')
	state = fields.Selection(related='comparison_id.state')

	def get_po_line_vals(self, order_id):
		self.ensure_one()
		return {'order_id': order_id.id,
				'product_id': self.product_id.id,
				'name': self.name,
				'product_uom': self.product_uom.id,
				'product_packaging_id': self.product_packaging_id.id or False,
				'product_packaging_qty': self.product_packaging_qty or False,
				'product_qty': self.product_qty,
				'taxes_id': [(6, 0, self.taxes_id.ids)]}

	@api.onchange('product_id')
	def onchange_product_id(self):
		if not self.product_id:
			return
		self._product_id_change()
		self._suggest_quantity()

	def _product_id_change(self):
		if not self.product_id:
			return
		self._compute_tax_id()
		self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
		product_lang = self.product_id.with_context(
			lang=get_lang(self.env).code,
			company_id=self.company_id.id,
		)
		self.name = self._get_product_purchase_description(product_lang)

	def _get_product_purchase_description(self, product_lang):
		self.ensure_one()
		name = product_lang.display_name
		if product_lang.description_purchase:
			name += '\n' + product_lang.description_purchase
		return name

	def _suggest_quantity(self):
		if not self.product_id:
			return
		self.product_qty = 1.0

	@api.onchange('product_packaging_id', 'product_uom', 'product_qty')
	def _onchange_update_product_packaging_qty(self):
		if not self.product_packaging_id:
			self.product_packaging_qty = 0
		else:
			packaging_uom = self.product_packaging_id.product_uom_id
			packaging_uom_qty = self.product_uom._compute_quantity(self.product_qty, packaging_uom)
			self.product_packaging_qty = float_round(packaging_uom_qty / self.product_packaging_id.qty,
													 precision_rounding=packaging_uom.rounding)

	@api.onchange('product_packaging_qty')
	def _onchange_product_packaging_qty(self):
		if self.product_packaging_id:
			packaging_uom = self.product_packaging_id.product_uom_id
			qty_per_packaging = self.product_packaging_id.qty
			product_qty = packaging_uom._compute_quantity(self.product_packaging_qty * qty_per_packaging, self.product_uom)
			if float_compare(product_qty, self.product_qty, precision_rounding=self.product_uom.rounding) != 0:
				self.product_qty = product_qty

	def _compute_tax_id(self):
		for line in self:
			line = line.with_company(line.company_id)
			line.taxes_id = line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id == line.env.company)
