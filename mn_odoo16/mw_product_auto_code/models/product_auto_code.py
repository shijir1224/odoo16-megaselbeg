from odoo import api, fields, models, _

class auto_code(models.Model):
    _inherit = "product.category"


    # @api.model
    # def _default_coding(self):
    #     seq_id = self.env['ir.sequence'].search([('code','=','auto.code'), ('name','=','auto.code.sec')], limit=1)
    #     if seq_id:
    #         return seq_id.next_by_id()


    auto_coding_id = fields.Many2one('ir.sequence', 'Авто дугаарлалт', tracking=True)


class product_template(models.Model):
    _inherit = "product.template"

    @api.onchange('categ_id')
    def onch_categ_seq(self):
        if self.categ_id.auto_coding_id and not self.default_code:
            self.default_code = self.categ_id.auto_coding_id.next_by_id()