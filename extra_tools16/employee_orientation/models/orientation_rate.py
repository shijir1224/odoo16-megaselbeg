from odoo import models, fields, _

class OrientationRate(models.Model):
    _name = 'orientation.rate.line'
    _description = "Orientation Rate line"
    _inherit = 'mail.thread'    

    rate_id = fields.Many2one('employee.orientation',string='Rate')
    question_id = fields.Many2one('rate.question',string='Questions')
    percent = fields.Selection([
        ('0','Огт үгүй'),
        ('1','Үгүй'),
        ('2','Дундаж'),
        ('3','Сайн'),
        ('4','Хангалттай сайн'),
    ], string='Percent', tracking=True
    )
    add_offer = fields.Text(string='Нэмэлт санал')
class RateQuestion(models.Model):
    _name = 'rate.question'
    _description = "Rate Question"
    _inherit = 'mail.thread'

    name = fields.Text(string='Question',required=True)

