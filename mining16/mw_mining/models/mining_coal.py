# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class mining_coal_sales(models.Model):
	_name = 'mining.coal.sales'
	_description = 'Mining Coal Sales'
	_inherit = ['mail.thread']
	STATE_SELECTION = [
		('draft', 'Draft'),
		('approved', 'Confirmed'),
	]
	@api.depends('line_ids')
	def _sum_sales_amount(self):
		for obj in self:
			val = 0.0
			val_m3 = 0.0
			val_res = 0.0
			for item in obj.line_ids:
				val += item.sales_amount_tn
				val_m3 += item.sales_amount_m3
				val_res += item.res_count
			obj.sum_sales_amount_tn = val
			obj.sum_sales_amount_m3 = val_m3
			obj.sum_res_count = val_res


	date = fields.Date('Огноо',required=True, states={'approved':[('readonly',True)]}, default=fields.Date.context_today)
	line_ids = fields.One2many('mining.coal.sales.line', 'mining_coal_sales_id', 'Mining Coal Sales Lines', states={'approved':[('readonly',True)]})
	description = fields.Text('Тайлбар', states={'approved':[('readonly',True)]})
	branch_id = fields.Many2one('res.branch', 'Салбар', required=True, states={'approved':[('readonly',True)]})
	sum_sales_amount_m3 = fields.Float(string='Нийт Борлуулсан м3', compute='_sum_sales_amount', readonly=True, store=True)
	sum_sales_amount_tn = fields.Float( string='Нийт Борлуулсан Дүн тонн', compute='_sum_sales_amount', readonly=True, store=True)
	sum_res_count = fields.Integer(string='Нийт Ресс', compute='_sum_sales_amount', readonly=True, store=True)
	state = fields.Selection(STATE_SELECTION, 'State', readonly=True, tracking=True, default='draft')


	# by Bayasaa Confirm
	def action_to_approved(self):
		# obj = self.browse(cr,uid,ids,context)[0]
		for item in self.line_ids:
			item.pile_material_id.mining_product_type

		if not self.line_ids:
			raise UserError('Нүүрс борлуулалтын мөр хоосон байна.')
		else:
			self.write({'state': 'approved'})
		return True
	# by Bayasaa Цуцлах
	def action_to_draft(self):
		self.write({'state': 'draft'})
		return True


	_sql_constraints = [
        ('date_uniq', 'UNIQUE(date)', 'Date must be unique!')
    ]

	_order = "date DESC"

class mining_coal_sales_line(models.Model):
	_name = 'mining.coal.sales.line'
	_description = 'Mining Coal Sales Line'

	@api.depends('sales_amount_tn','pile_id.material_id')
	def _set_sales_amount_m3(self):
		for obj in self:
			if obj.pile_id.material_id.bcm_coefficient > 0:
				obj.sales_amount_m3 = obj.sales_amount_tn/obj.pile_id.material_id.bcm_coefficient

	mining_coal_sales_id = fields.Many2one('mining.coal.sales','Mining Coal Sales', required=True, ondelete='cascade')
	date = fields.Date(related='mining_coal_sales_id.date')
	type = fields.Selection([('sale', 'Борлуулалт'),('sub_coal', 'Хандивийн Нүүрс'),('other_coal','Бусад Нүүрс')], default='sale', required=True, string='Type')
	partner_id = fields.Many2one('res.partner', 'Partner')
	pile_id = fields.Many2one('mining.pile', 'Овоолго', required = True)
	pile_material_id = fields.Many2one(related='pile_id.material_id', string='Material', store=True, readonly=True)
	total_balance_m3 = fields.Float(related='pile_id.balance_by_report_m3', string="Овоолгын Үлдэгдэл Мэдээгээр м3")
	total_balance_tn = fields.Float(related='pile_id.balance_by_report_tn', string="Овоолгын Үлдэгдэл тонн")
	sales_amount_m3 = fields.Float(compute='_set_sales_amount_m3', string='Борлуулсан Дүн м3', readonly=True, store=True)
	sales_amount_tn = fields.Float('Sales Amount tn', required=True)
	res_count = fields.Integer('Res Count')

	_order = 'date desc'
	_defaults = {
		'type': 'sale'
	}
	_sql_constraints = [
		('year_month_uniq', 'UNIQUE(mining_coal_sales_id, pile_id, partner_id)', 'Pile, Partner must be unique!'),
		# ('pile_balance','CHECK(total_balance_m3 < 0)','Error ! Pile Balace Not Enough'),
	]
