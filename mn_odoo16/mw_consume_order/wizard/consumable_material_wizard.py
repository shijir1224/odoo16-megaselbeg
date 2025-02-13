# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import datetime
from odoo.exceptions import UserError

class SaleOrderWizard(models.TransientModel):
	_name = 'consumable.material.in.use.wizard'
	_description = 'consumable.material.in.use.wizard'
	
	account_id = fields.Many2one('account.account', 'Account')
	date = fields.Date('Date', default=lambda self: fields.Datetime.now(), tracking=True)
	note_close = fields.Char('Note close', required=True)
	is_qty = fields.Boolean('Is QTY')
	qty = fields.Float('QTY')

	def process(self):
	#    Товч дархад ашиглалтанд буй хангамжийн материал дээр журналын бичилт үүсгэж холбоотой барааны хөдөлгөөнийг хийгдсэн төлөвт оруулна.
		for line in self:
			# if line.account_id:
			if self.is_qty and self.qty>0:
				context=dict(line._context)
				consumable_obj = line.env.get('consumable.material.in.use')
				consume_ids = context.get('active_ids', False)
				for consumable_id in consume_ids:
					consumable = consumable_obj.browse(consumable_id)
					if self.qty>consumable.qty:
						raise UserError(_(u'Тоо хэмжээ их байна.'))
					elif self.qty==consumable.qty:
						consumable.state = 'progress_done'
						consumable.end_date = self.date
						consumable.note_close = self.note_close  
						invoice_line = self.env['account.move.line']
						consumable.set_to_close(invoice_line_id=invoice_line, date=self.date, account_id=self.account_id if self.account_id else None, analytic_distribution=None, sell_type='dispose')
					else:
						history_obj = self.env['consume.order.history']
						history_vals = {'use_id':consumable.id,'type':'close'}
						history_vals.update({'name': self.note_close  + u' Хувааж актлав'})
						history_vals.update({'date': self.date})
						history_vals.update({'qty': self.qty})
						history_obj.create( history_vals)                          
						
						consumable.qty = consumable.qty-self.qty
						consumable.note_close = self.note_close  + u' Хувааж актлав'
						invoice_line = self.env['account.move.line']
						consumable.set_to_close(invoice_line_id=invoice_line, date=self.date, account_id=self.account_id if self.account_id else None, analytic_distribution=None, sell_type='dispose')
						
			else:
				context=dict(line._context)
				consumable_obj = line.env.get('consumable.material.in.use')
				consume_ids = context.get('active_ids', False)
				print('consume_ids', consume_ids)
				for consumable_id in consume_ids:
					print(consumable_id)
					consumable = consumable_obj.browse(consumable_id)
					consumable.state = 'progress_done'
					consumable.end_date = self.date
					consumable.note_close = self.note_close

					invoice_line = self.env['account.move.line']
					consumable.set_to_close(invoice_line_id=invoice_line, date=self.date, account_id=self.account_id if self.account_id else None, analytic_distribution=None, sell_type='dispose')
				return True 


class SaleOrderWizardAll(models.TransientModel):
	_name = 'consumable.material.in.use.wizard.all'
	_description = 'consumable.material.in.use.wizard.all'
	
	account_id = fields.Many2one('account.account', 'Account')
	date = fields.Date('Date', default=lambda self: fields.Datetime.now())
	note_close = fields.Char('Note close', required=True)

	def process(self):
#   Олноор сонгоод батлах товч дархад ашиглалтанд буй хангамжийн материал дээр журналын бичилт үүсгэж холбоотой барааны хөдөлгөөнийг хийгдсэн төлөвт оруулна.
		context=dict(self._context)
		active_ids = self._context.get('active_ids', False) or []
		consumable_obj = self.env.get('consumable.material.in.use')
		for wizard in self:
			for consumable in consumable_obj.browse(active_ids):
				consumable.state = 'progress_done'
				consumable.end_date = datetime.datetime.now()
				consumable.note_close = wizard.note_close
				note = 10000 + int(consumable.id)
				stock_obj = consumable.env['stock.picking'].search([('note','=',note)],limit=1)
				check_value = False
				res = []
				for line in consumable:
					consume_obj = consumable.env['consumable.material.expense'].search([('doc_number', '=', line.doc_number)])
					res = consumable.env['consumable.material.in.use'].search([('doc_number', '=', line.doc_number)])
					for i in res:
						if i.state != 'progress_done':
							check_value = True
				if check_value == False:
					consume_obj.state = 'done'
					consume_obj.note_close = wizard.note_close
				if stock_obj:
						stock_obj.action_confirm()
						stock_obj.force_assign()
						wiz = self.env['stock.immediate.transfer'].create({'pick_id': stock_obj.id})
						wiz.force_date = self.date
						wiz.process()
						if stock_obj.state == 'done':
							consumable.state = 'progress_done'
							consumable.note_close = wizard.note_close
					
			return True 