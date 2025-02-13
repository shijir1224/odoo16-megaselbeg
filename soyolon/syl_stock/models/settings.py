from odoo import fields, models, api
from odoo.exceptions import UserError

class StockNormTypes(models.Model):
  _name = 'stock.norm.types'
  _rec_name = 'name'
  _description = 'Норм төрлүүд'

  name = fields.Char(string='Төрөл', required='1')
  active_is = fields.Boolean(string='Ашиглагдаж байгаа эсэх', default=True)

class PurchaseRequestMailSettings(models.Model):
  _name = 'pr.mail.settings'
  _description = 'Mail settings from purchase request'

  name = fields.Char(string='Нэр')
  user_id = fields.Many2one('res.users', string='Үүсгэсэн хэрэглэгч', default=lambda self:self.env.user.id)
  date = fields.Date(string='Үүсгэсэн огноо', default=fields.Date.today())
  user_ids = fields.One2many('pr.mail.settings.user.ids', 'pr_mail_id', string='Батлах хэрэглэгчид')
  category_ids = fields.Many2many('product.category', string='Барааны ангилал')
  state = fields.Selection([('draft','Үүссэн'),('approved','Батлагдсан'),('cancel','Цуцалсан')], default='draft', string='Төлөв')

  def action_approve(self):
    for i in self:
      if self.env.user.id == i.user_id.id:
        items = self.env['pr.mail.settings'].search([('state','=','approved')])
        if items:
          raise UserError('Тухайн бүртгэлд батлагдсан мэдээлэл байгаа тул та өмнөх бүртгэлийг цуцлаад батлана уу!')
        else:
          if i.state == 'draft':
            i.state = 'approved'             
      else:
        raise UserError('Та уг бүртгэлийг батлах эрхгүй байна. Бүртгэлийг үүсгэсэн хэрэглэгчид хандана уу!')
  
  def action_cancel(self):
    for i in self:
      if self.env.user.id == i.user_id.id:
        if i.state == 'approved':
          i.state = 'cancel'
      else:
        raise UserError('Та уг бүртгэлийг батлах эрхгүй байна. Бүртгэлийг үүсгэсэн хэрэглэгчид хандана уу!')

class PurchaseRequestMailSettingsUserIds(models.Model):
  _name = 'pr.mail.settings.user.ids'
  _description = 'Mail settings send users'

  pr_mail_id = fields.Many2one('pr.mail.settings')
  partner_id = fields.Many2one('res.partner', domain="[('employee','=',True)]", string='Ажилтан')
  job_position = fields.Many2one('hr.job', string='Албан тушаал', related='partner_id.user_ids.employee_id.job_id')
  department_id = fields.Many2one('hr.department', string='Алба хэлтэс', related='partner_id.user_ids.employee_id.department_id')