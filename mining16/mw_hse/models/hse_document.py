from odoo import  api, fields, models, _
from odoo.exceptions import UserError


class HseRulesDocument(models.Model):
	_name ='hse.rules.document'
	_description = 'Rules document'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'date DESC'

	@api.model
	def _default_name(self):
		name=self.env['ir.sequence'].next_by_code('hse.rules.document')
		return name
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
	user_id = fields.Many2one('res.users', string='Үүсгэсэн ажилтан', default=lambda self: self.env.user.id, copy=False, required=True, readonly=True)


	name = fields.Char(string='Гарчиг', readonly=True, default=_default_name)
	document_name = fields.Char(string='Нэр', readonly=True, states={'draft':[('readonly',False),]})
	state = fields.Selection([
		('draft', 'Ноорог'),
		('done', 'Батлагдсан')], 'Төлөв', readonly=True, default='draft', tracking=True)
	date = fields.Date(string='Огноо', required=True, default=fields.Date.context_today, readonly=True, states={'draft':[('readonly',False),]})
	branch_ids = fields.Many2many('res.branch', 'hse_rules_document_branch_rel', 'doc_id', 'branch_id', string='Салбар', required=False, readonly=True, states={'draft':[('readonly',False),]})
	type_id = fields.Many2one('hse.rules.document.type', string='Төрөл', readonly=True, states={'draft':[('readonly',False),]})
	attachment_ids = fields.Many2many('ir.attachment', 'hse_hse_rules_document_attachment_rel', 'document_id', 'attachment_id', string=u'Бичиг баримт', readonly=True, states={'draft':[('readonly',False),]})

	def unlink(self):
		for item in self:
			if item.state !='draft':
				raise UserError(_('Ноорог төлөвтэйг устгана!!!'))
		return super(HseRulesDocument, self).unlink()
			
	def action_to_draft(self):
		self.write({'state': 'draft'})
		return True
	
	def action_to_done(self):
		self.write({'state': 'done'})
		return True
