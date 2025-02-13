# -*- coding: utf-8 -*-

import odoo
import time
from odoo import api, fields, models
from odoo import _, tools
from datetime import datetime, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import collections
import xlrd
import os
from tempfile import NamedTemporaryFile
import base64
from io import BytesIO

import logging

from odoo.osv.osv import osv

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'
	main_price_unit = fields.Float(u'Үндсэн үнэ', readonly=True, digits=(16, 1),)
	return_qty = fields.Float(u'Буцаалт', digits=(16, 1),)
	return_reason = fields.Selection([
		('return_expired', u'Хугацаа дөхсөн'),
		('return_complaints', u'Хэрэглэгчийн гомдол'),
		('return_payment', u'Төлбөр бүрэн биш'), ],
		string=u'Буцаалтын шалтгаан', readonly=True, )
	# Хайрцаг
	package_qty = fields.Integer(string=u'Хайрцаг', states={'sale': [('readonly', True)], 'done': [('readonly', True)]})
	@api.onchange('package_qty')
	def onchange_package_qty(self):
		if self.package_qty and self.product_id:
			package_qty = 1
			if self.product_id.uom_po_id and self.product_id.uom_po_id.factor > 0:
				package_qty = self.product_id.uom_po_id.factor
				self.product_uom_qty = self.package_qty * package_qty

class SalesMasterPlan(models.Model):
	_name = 'sales.master.plan'
	_description = 'Sales master plan'
	_inherit = 'mail.thread'
	_order = 'year desc, month desc, branch_id'

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	date = fields.Datetime(u'Created date', readonly=True, default=fields.Datetime.now(), copy=False)
	plan_description = fields.Char(u'Description', copy=True, states={'confirmed':[('readonly',True)],'done':[('readonly',True)],'company':[('readonly',True)]})
	name = fields.Char(u'Төлөвлөгөөний нэр', copy=False, required=True, states={'confirmed':[('readonly',True)],'done':[('readonly',True)]}, default='/')
	plan_type = fields.Selection([
		('branch', u'By Branch'),
		('partner', u'By Partner'),
		('company', u'Компаны нийт'),
	], string=u'Plan type', copy=True, default='branch', required=True,
		states={'confirmed':[('readonly',True)],'done':[('readonly',True)],'company':[('readonly',True)]})
	partner_id = fields.Many2one('res.partner', u'Partner', index=True,
								 states={'confirmed':[('readonly',True)],'done':[('readonly',True)],'company':[('readonly',True)]})
	branch_id = fields.Many2one('res.branch', u'Branch', copy=True, index=True,
								states={'confirmed':[('readonly',True)],'done':[('readonly',True)],'company':[('readonly',True)]})
	crm_team_id = fields.Many2one('crm.team', string=u'Team', copy=True, index=True,
								  states={'confirmed':[('readonly',True)],'done':[('readonly',True)],'company':[('readonly',True)]})
	salesman_id = fields.Many2one('res.users', string=u'Salesman', index=True,
								  states={'confirmed':[('readonly',True)],'done':[('readonly',True)],'company':[('readonly',True)]})

	year = fields.Integer(string=u'Year', copy=True, required=True,
		states={'confirmed':[('readonly',True)],'done':[('readonly',True)],'company':[('readonly',True)]})

	month = fields.Selection([
		('1', u'January'),
		('2', u'February'),
		('3', u'March'),
		('4', u'April'),
		('5', u'May'),
		('6', u'June'),
		('7', u'July'),
		('8', u'August'),
		('9', u'September'),
		('10', u'October'),
		('11', u'November'),
		('12', u'December'),
	], string=u'Month', copy=True, states={'confirmed':[('readonly',True)],'done':[('readonly',True)],'company':[('readonly',True)]})

	user_id = fields.Many2one('res.users', string='User', default=_get_user, readonly=True)
	validator_id = fields.Many2one('res.users', string=u'Баталсан', readonly=True)

	line_ids = fields.One2many('sales.master.plan.line', 'parent_id', 'Lines', copy=True,
							   states={'done': [('readonly', True)],'company': [('readonly', True)]})

	state = fields.Selection([
		('draft', 'Draft'),
		('confirmed', 'Confirmed'),
		('done', 'Done'),
		('company', 'Компани')
	], default='draft', required=True, string='State', tracking=True)

	excel_data = fields.Binary(string='Excel file',)
	import_description = fields.Text(u'Import description', readonly=True, copy=False,
									 default=u"(Default code, Price unit, Quantity, Barcode) - Must be these column (no header)")

	increase_product_id = fields.Many2one('product.product', string=u'Засвар хийх бараа', 
		domain=[('sale_ok','=',True)], 
		help=u"Зөвхөн сонгосон барааг өсгөх, буруулах боломжтой")
	increase_percent = fields.Float(string=u'Өсгөх хувь', default=0,
		help=u"Төлөвлөгөөг хувиар өсгөж, бууруулах хэмжээ")
	
	def action_get_excecution(self):
		for obj in self:
			for line in obj.line_ids:
				query = 'SELECT * from sale_order_line a left join sale_order b on a.order_id = b.id where aml_id={0}'.format(l['id'])
				self._cr.execute(query)
				res = self._cr.fetchall()
				orders = self.env['sale.order'].search([('')])

	@api.depends('line_ids')
	def _methods_compute(self):
		for obj in self:
			obj.total_amount = sum(obj.mapped('line_ids.amount'))
			obj.total_amount_fixed = sum(obj.mapped('line_ids.amount_fixed'))

	total_amount = fields.Float(compute=_methods_compute, store=True, string=u'Total amount', tracking=True, default=0)
	total_amount_fixed = fields.Float(compute=_methods_compute, store=True, string=u'Нийт тодотгосон дүн', tracking=True, default=0)

	warehouse_id = fields.Many2one('stock.warehouse', u'Агуулах', 
		states={'confirmed':[('readonly',True)],'done':[('readonly',True)],'company':[('readonly',True)]})
	# ====================== OVERRIDE ======================
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('In order to delete a record, it must be draft first!'))
		return super(SalesMasterPlan, self).unlink()

	def write(self, vals):
		res = super(SalesMasterPlan, self).write(vals)
		p_ids = [l.product_id for l in self.line_ids]
		dup_ids = [item for item, count in collections.Counter(p_ids).items() if count > 1]
		if dup_ids:
			names = [d.name for d in dup_ids]
			raise UserError(_(u'"%s" duplicated products!' % (', '.join(names))))

		return res

	# ================ CUSTOM =============================
	# Төлөвлөгөөний тоо хэмжээг өөрчлөх, % аар өмгөж бууруулах
	def increase_plan_qty(self):
		if self.increase_percent and self.increase_percent != 0:
			if self.increase_product_id:
				for line in self.line_ids.filtered(lambda l: l.product_id.id == self.increase_product_id.id):
					if line.qty > 0:
						qty = line.qty
						new_qty = qty + int((qty * self.increase_percent) / 100)
						line.qty = new_qty
						line.qty_fixed = new_qty
			else:
				for line in self.line_ids:
					if line.qty > 0:
						qty = line.qty
						new_qty = qty + int((qty * self.increase_percent) / 100)
						line.qty = new_qty
						line.qty_fixed = new_qty
			self._methods_compute()
			self.message_post(body=u"%d хувиар тоо хэмжээг өөрчиллөө. " % self.increase_percent)
		return True

	def action_to_draft(self):
		self.state = 'draft'

	def action_to_done(self):
		self.state = 'done'

	def action_to_confirm(self):
		if self.line_ids:
			if not self.name:
				seq = self.env['ir.sequence'].next_by_code('sales.master.plan')
				self.name = seq
			for l in self.line_ids:
				if l.qty <= 0 or l.amount <= 0:
					raise UserError(_(u'Please insert quantity and amount! %s' % l.product_id.name))
				if self.partner_id and self.plan_type == 'partner':
					price = self.partner_id.property_product_pricelist.get_product_price(l.product_id, l.qty, self.partner_id)
					l.price_unit = price
			# Төлөвлөгөөний давхардлыг шалгах
			# if self.branch_id and not self.partner_id:
			#	 lids = self.env['sales.master.plan'].search([
			#		 ('branch_id', '=', self.branch_id.id),
			#		 ('state', 'in',['confirmed','done']),
			#		 ('year', '=', self.year),
			#		 ('month', '=', self.month),
			#	 ])
			#	 if len(lids) > 0:
			#		 dddd = ", ".join([p.name for p in lids])
			#		 id_dddd = str(lids.mapped('id'))
			#		 raise UserError(_(u'Duplicated plan!\n Name: %s, id: %s' % (dddd, id_dddd)))
			
			# elif self.partner_id:
			# 	lids = self.env['sales.master.plan'].search([
			# 		('partner_id','=',self.partner_id.id),
			# 		('state', 'in',['confirmed','done']),
			# 		('year','=',self.year),
			# 		('month','=',self.month),
			# 	])
			# 	if len(lids) > 0:
			# 		dddd = ", ".join([p.name for p in lids])
			# 		id_dddd = str(lids.mapped('id'))
			# 		raise UserError(_(u'Duplicated plan!\n Name: %s, id: %s' % (dddd,id_dddd)))

			self.validator_id = self.env.user.id
			self.message_post(body="Confirmed SMP by %s" % self.validator_id.name)
			if self.plan_type == 'company':
				self.state = 'company'
			else:
				self.state = 'confirmed'
		else:
			raise UserError(_('Insert plan lines!'))

	def import_from_excel(self):
		if not self.excel_data:
			raise UserError(_(u'Choose import excel file!'))

		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise osv.except_osv(u'Error', u'Importing error.\nCheck excel file!')

		book = xlrd.open_workbook(fileobj.name)
		try:
			sheet = book.sheet_by_index(0)
		except:
			raise osv.except_osv(u'Warning', u'Wrong Sheet number.')

		self.import_description = ""
		nrows = sheet.nrows
		desc = ''
		for i in range(0, nrows):
			row = sheet.row(i)
			default_code = False
			barcode = False
			product = False
			# Барааны кодоор
			if row[0].value:
				if row[0].ctype in [2, 3]:
					default_code = int(row[0].value)
				else:
					default_code = row[0].value
				product = self.env['product.product'].search([('default_code', '=', default_code)], limit=1)
			# Баркодоор
			if row[3].value:
				if row[3].ctype in [2, 3]:
					barcode = int(row[3].value)
				else:
					barcode = row[3].value
				product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)

			price_unit = row[1].value
			qty = row[2].value
			_logger.info(u'-*************-Import plan-***************--%s %s %d %d------\n', default_code, barcode, price_unit, qty)
			if product:
				vals = {
					'parent_id': self.id,
					'product_id': product.id,
					'price_unit': price_unit,
					'qty': qty,
				}
				plan = self.env['sales.master.plan.line'].create(vals)
				plan.onchange_qty()
			else:
				desc += str(default_code or barcode) + ', '

		if desc:
			self.import_description = desc + u'- not found product!'

		return True

	# Өнгөрсөн жилийн борлуулалтаас татах
	def get_last_year_data(self):
		self.line_ids.unlink()
		d1 = datetime(self.year-1, int(self.month), 1)
		last_day = monthrange(self.year, int(self.month))[1]
		d2 = datetime(self.year-1, int(self.month), last_day)
		query = """
			SELECT 
				ll.product_id as product_id,
				sum(ll.qty) as qty
			FROM sale_pivot_report as ll
			WHERE 
				ll.order_date >= '%s' and
				ll.order_date <= '%s' and
				ll.branch_id = %d and
				ll.crm_team_id = %d 
            GROUP BY ll.product_id
		""" % (d1, d2, self.branch_id.id, self.crm_team_id.id)
		print ('====', query)
		self.env.cr.execute(query)
		query_result = self.env.cr.dictfetchall()
		o_line_data = []
		for ll in query_result:
			product = self.env['product.product'].search([('id','=',ll['product_id'])], limit=1)
			vll = {
				'product_id': product.id,
				'price_unit': product.list_price,
				'qty': ll['qty'],
				'qty_fixed': ll['qty'],
			}
			o_line_data += [(0,0,vll)]
		self.line_ids = o_line_data
		return True

class SalesMasterPlanLine(models.Model):
	_name = 'sales.master.plan.line'
	_description = 'Sales master plan line'
	_order = 'product_id'

	@api.depends('price_unit', 'qty', 'qty_fixed')
	def _get_amount(self):
		for obj in self:
			obj.amount = obj.qty * obj.price_unit
			obj.amount_fixed = obj.qty_fixed * obj.price_unit

	# Columns
	parent_id = fields.Many2one('sales.master.plan', 'Parent ID', ondelete='cascade')
	state = fields.Selection(related='parent_id.state', string=u'State', store=True, readonly=True)
	name = fields.Char(related='parent_id.name', string='Name', store=True, readonly=True, )
	product_id = fields.Many2one('product.product', u'Product', required=True, copy=True, domain=[('sale_ok', '=', True)],
								 index=True,
								 states={'confirmed':[('readonly',True)],'done':[('readonly',True)],'company':[('readonly',True)]})
	uom_id = fields.Many2one('uom.uom', related='product_id.uom_id', string=u'Хэмжих нэгж', readonly=True, )
	categ_id = fields.Many2one(related='product_id.categ_id', string=u'Category', store=True, readonly=True, index=True, )
	branch_id = fields.Many2one(related='parent_id.branch_id', string=u'Branch', store=True, readonly=True)
	salesman_id = fields.Many2one(related='parent_id.salesman_id', string=u'Salesman', store=True, readonly=True)

	year = fields.Integer(related='parent_id.year', string=u'Year', store=True, readonly=True, index=True, )
	month = fields.Selection(related='parent_id.month', copy=False, store=True, readonly=True, index=True, )

	qty = fields.Float(string=u'Quantity', copy=True, default=0, required=True, digits=(16, 1),
						 states={'confirmed':[('readonly',True)],'done':[('readonly',True)],'company':[('readonly',True)]})
	qty_fixed = fields.Float(string=u'Тодотгосон тоо', copy=True, default=0, required=True,
							   states={'done': [('readonly', True)]}, digits=(16, 1))
	qty_excecution = fields.Float(string=u'Гүйцэтгэл тоо', copy=True, default=0,
							   states={'done': [('readonly', True)]}, digits=(16, 1))

	@api.depends('qty', 'qty_fixed', 'product_id')
	def _set_package(self):
		for obj in self:
			package_qty = 1
			if obj.product_id.uom_po_id and obj.product_id.uom_po_id.factor > 0:
				package_qty = obj.product_id.uom_po_id.factor
			obj.package = obj.qty / float(package_qty)
			obj.package_fixed = obj.qty_fixed / float(package_qty)
	package = fields.Float(string=u'Package', compute='_set_package', store=True,
						   readonly=True, )
	package_fixed = fields.Float(string=u'Хайрцаг.Тод', compute='_set_package', store=True,
								 readonly=True, )

	price_unit = fields.Float(string=u'Unit price', required=True, copy=True,
							  states={'confirmed':[('readonly',True)],'done':[('readonly',True)],'company':[('readonly',True)]})
	amount = fields.Float(compute='_get_amount',
						  store=True, string=u'Total amount', copy=False)
	amount_fixed = fields.Float(compute='_get_amount',
								store=True, string=u'Тодотгосон дүн', copy=False)
	amount_excecution = fields.Float(string=u'Гүйцэтгэл дүн', copy=False)
	
	# METHODs
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Must be draft!'))
		return super(SalesMasterPlanLine, self).unlink()

	@api.onchange('product_id','qty')
	def onchange_product_id(self):
		if self.parent_id.partner_id and self.product_id:
			price = self.parent_id.partner_id.property_product_pricelist.get_product_price(self.product_id, self.qty, self.parent_id.partner_id)
			self.price_unit = price
		else:
			self.price_unit = self.product_id.list_price

	@api.onchange('qty')
	def onchange_qty(self):
		if self.qty:
			self.qty_fixed = self.qty

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	invoice_ids = fields.Many2many("account.move", string='Invoices', compute="_get_invoiced", readonly=True, copy=False, store=True)