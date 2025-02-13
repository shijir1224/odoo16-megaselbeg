from odoo import models
from odoo.exceptions import UserError

class StockPicking(models.Model):
	_inherit = "stock.picking"

	def button_validate(self):
		for item in self:
			sales = self.env['sale.order'].search([('name','=',item.origin)], limit=1)
			if sales:
				if sales.amount_for_delivery:
					if not sales.invoice_ids:
						raise UserError('Нэхэмжлэл үүсээгүй байна!')
					if (sales.amount_total - sales.uldegdel_tulbur) < sales.amount_for_delivery:
						raise UserError('Хүргэлтийн гэрээний төлбөрийн нөхцөл хүрээгүй байна!')
		return super(StockPicking, self).button_validate()

	def write(self, vals):
		res = super(StockPicking, self).write(vals)
		for item in self:
			if item.state == 'assigned' and item.picking_type_id.code == 'outgoing' and item.sale_id:
				html = u"""<b>%s агуулахын зарлага БЭЛЭН төлөвт орлоо""" %(item.name)
				partners = self.env.ref('sales_team.group_sale_salesman').sudo().users.mapped('partner_id')
				self.env.user.send_chat(html,partners)
		return res