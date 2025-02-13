from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError

class RidaCheck(models.Model):
    _name = 'rida.check'
    _description = 'RIDA CHECK'
    _inherit = ["mail.thread", "mail.activity.mixin"]


    def _default_name(self):
        name = self.env['ir.sequence'].next_by_code('rida.check')
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

    review = fields.Char(string='Дүгнэлт', readonly=True, states={'draft':[('readonly',False)]})
    company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
    rida_check_line_ids = fields.One2many('rida.check.line', 'parent_id', string='Lines', readonly=True, states={'draft':[('readonly',False)]})

    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise UserError('Устгах боломжгүй зөвхөн ноорог төлөвтэйг устгана !!!')
            if line.rida_check_line_ids:
                raise UserError('Мөр дээр  мэдээлэл байгаа тул устгах боломжгүй !!!')
        return super(RidaCheck, self).unlink()

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_done(self):
        self.write({'state': 'done'})

class RidaCheckLine(models.Model):
    _name = 'rida.check.line'
    _description = 'RIDA CHECK LINE'

    parent_id = fields.Many2one('rida.check', string='RIDA CHECK', index=True)

    surface_area = fields.Selection([
        ('tea_cup', 'Цайны аяга'),
        ('dinner_plate', 'Хоолны тавга'),
        ('soup_cup', 'Шөлний аяга'),
        ('snack_plate', 'Зуушны тавга'),
        ('spoon', 'Халбага'),
        ('fork', 'Сэрээ'),
        ('knife', 'Хутга'),
    ], string='Арчдас авах гадаргуу', default=False)

    pollution_level = fields.Selection([
        ('clean', 'Цэвэр'),
        ('not_noticeable', 'Мэдэгдэхгүй'),
        ('slightly_dirty', 'Бага бохирдсон'),
        ('very_dirty', 'Их бохирдсон')
    ], string='Бохирдолын түвшин', default=False)
    

    description = fields.Char(string='Тайлбар')