# -*- coding: utf-8 -*-
# Copyright 2014 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError, AccessDenied
_logger = logging.getLogger(__name__)

FIELD_TYPES = [(key, key) for key in sorted(fields.Field.by_type)]

class StockMoveLine(models.Model):
	_inherit = "stock.move.line"
	
	product_uom_id = fields.Many2one(
		'uom.uom', 'Unit of Measure', required=True, domain="[('category_id', '=', product_uom_category_id)]",
		compute="_compute_product_uom_id", store=True, readonly=False, precompute=True, index=True)
	date = fields.Datetime('Date', default=fields.Datetime.now, required=True, index=True)
	location_id = fields.Many2one(
		'stock.location', 'From', domain="[('usage', '!=', 'view')]", check_company=True, required=True,
		compute="_compute_location_id", store=True, readonly=False, precompute=True, index=True)
	location_dest_id = fields.Many2one('stock.location', 'To', domain="[('usage', '!=', 'view')]", check_company=True, required=True, compute="_compute_location_id", store=True, readonly=False, precompute=True, index=True)
	state = fields.Selection(related='move_id.state', store=True, related_sudo=False, index=True)

class Picking(models.Model):
	_inherit = "stock.picking"

	date_done = fields.Datetime('Date of Transfer', copy=False, readonly=True, help="Date at which the transfer has been processed or cancelled.", index=True)
	location_id = fields.Many2one(
		'stock.location', "Source Location",
		compute="_compute_location_id", store=True, precompute=True, readonly=False,
		check_company=True, required=True, index=True,
		states={'done': [('readonly', True)]})
	location_dest_id = fields.Many2one(
		'stock.location', "Destination Location",
		compute="_compute_location_id", store=True, precompute=True, readonly=False,
		check_company=True, required=True, index=True,
		states={'done': [('readonly', True)]})

class stock_quant(models.Model):
	_inherit = "stock.quant"

	company_id = fields.Many2one(related='location_id.company_id', string='Company', store=True, readonly=True, index=True)

class mail_channel(models.Model):
	_inherit = 'mail.channel'

	group_public_id = fields.Many2one('res.groups', string='Authorized Group', compute='_compute_group_public_id', readonly=False, store=True)

class IrAttachment(models.Model):
	_inherit = 'ir.attachment'

	create_uid = fields.Many2one('res.users', 'Created by', index=True, readonly=True)
	name = fields.Char('Name', required=True, index=True)

class ir_ui_view(models.Model):
	_inherit = 'ir.ui.view'

	website_id = fields.Many2one('website', ondelete='cascade', string="Website", index=True)
	key = fields.Char(index='btree_not_null')

class ImBus(models.Model):
	_inherit = 'bus.bus'
	
	channel = fields.Char('Channel', index=True)
	create_date = fields.Datetime(string='Created on', readonly=True, index=True)

class IrModelFields(models.Model):
	_inherit = 'ir.model.fields'
	
	ttype = fields.Selection(selection=FIELD_TYPES, string='Field Type', required=True, index=True)
	relation = fields.Char(string='Object Relation',
						   help="For relationship fields, the technical name of the target model", index=True)

class IrModelData(models.Model):
	_inherit = 'ir.model.data'

	name = fields.Char(string='External Identifier', required=True,
					   help="External Key/Identifier that can be used for "
							"data integration with third-party systems", index=True)
	module = fields.Char(default='', required=True, index=True)

class ModuleDependency(models.Model):
	_inherit = "ir.module.module.dependency"
	
	module_id = fields.Many2one('ir.module.module', 'Module', ondelete='cascade', index=True)

class AccountPartialReconcile(models.Model):
	_inherit = "account.partial.reconcile"
	
	full_reconcile_id = fields.Many2one(
		comodel_name='account.full.reconcile',
		string="Full Reconcile", copy=False,index=True)

class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	company_id = fields.Many2one(
		related='move_id.company_id', store=True, readonly=True, precompute=True,
		index=True,
	)

class AccountMove(models.Model):
	_inherit = "account.move"

	to_check = fields.Boolean(
		string='To Check',
		tracking=True,
		help="If this checkbox is ticked, it means that the user was not sure of all the related "
			 "information at the time of the creation of the move and that the move needs to be "
			 "checked again.", index=True
	)