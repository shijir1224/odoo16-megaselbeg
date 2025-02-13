from odoo import fields, models, _, api
from odoo.exceptions import UserError
from datetime import date




# Урсгал тус бүр дээр санал дүгнэлт оруулдаг хэсэг нэмэх

class PromotionRequest(models.Model):
	_inherit = "promotion.request"

	s_date = fields.Char('Хэрэгжиж эхлэх огноо', tracking=True)
	start_date= fields.Date('Хэрэгжиж эхлэх огноо', tracking=True, required=True)
	emp_type = fields.Selection([('type1', 'Туршилтын хугацааг сунгах'), ('type2', 'Үндсэн ажилтан болгох'), ('type3', 'Туршилтын хугацаанд ажилд тэнцээгүй ажилтны ажлаас чөлөөлөх')], 'Туршилтын ажилтныг үндсэн ажилтан болгох эсэх ?', tracking=True)
	pro_type = fields.Selection([('type1', 'Албан тушаал дэвшүүлэх'), ('type2', 'АТ бууруулах'), ('type3', 'АТ шилжүүлэх')], 'Шилжилт хөдөлгөөний төрөл', tracking=True)
	level_id = fields.Many2one('salary.level','Цалингийн шатлал')
	

class DynamicFlowHistory(models.Model):
    _inherit = 'dynamic.flow.history'

    desc = fields.Char('Санал дүгнэлт')