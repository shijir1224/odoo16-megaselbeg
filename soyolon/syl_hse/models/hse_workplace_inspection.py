from odoo import api, fields, models, _



class hseWorkplaceInspection(models.Model):
	_inherit = 'hse.workplace.inspection'

	def _get_name(self):
		return self.env['ir.sequence'].next_by_code('hse.workplace.inspection')

	name = fields.Char(string='Дугаар' , default=_get_name, readonly=True)
	state = fields.Selection(selection_add=[('cancel', 'Цуцлагдсан'),])
	workplace_hierarchy = fields.Selection([
		('2', '2-р шат'),
		('3', '3-р шат'),
		('4', '4-р шат')], string='Үзлэгийн шатлал')

	def action_to_cancel(self):
		for item in self:
			item.state = 'cancel'