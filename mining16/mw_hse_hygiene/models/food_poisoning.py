from odoo import api, fields, models, _
from odoo.exceptions import UserError

class FoodPoisoning(models.Model):
    _name = 'food.poisoning'
    _description = 'FOOD CHECK'
    _inherit = ["mail.thread", "mail.activity.mixin"]


    def _default_name(self):
        name = self.env['ir.sequence'].next_by_code('food.poisoning')
        if name:
            return name
        else:
            False

    name = fields.Char(string='Нэр', readonly=True, default=_default_name)
    date = fields.Date(string='Огноо', default=fields.Date.context_today, tracking=True, required=True, readonly=True, states={'draft':[('readonly',False)]})
    state = fields.Selection([
     	('draft', 'Ноорог'), 
		('done', 'Батлагдсан')], 
    string='Төлөв', readonly=True, default='draft', tracking=True)
    description = fields.Char(string='Тайлбар', readonly=True, states={'draft':[('readonly',False)]})
    attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралт', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
    company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)

    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise UserError('Устгах боломжгүй зөвхөн ноорог төлөвтэйг устгана!')
        return super(FoodPoisoning, self).unlink()


    def action_draft(self):
        self.write({'state': 'draft'})

    def action_done(self):
        self.write({'state': 'done'})