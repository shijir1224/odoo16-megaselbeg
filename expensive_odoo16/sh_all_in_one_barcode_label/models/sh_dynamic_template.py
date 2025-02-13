# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ShProductLabelDynamicTemplate(models.Model):
    _name = 'sh.dynamic.template'
    _description = "Dynamic Label Template"
    _rec_name = 'name'

    name = fields.Char("Name", required=True)
    sh_print_barcode_or_qr = fields.Selection(
        [('qr', 'QR'), ('barcode', 'Barcode')], default='qr', string='Barcode/QR Type')
    sh_barcode_type = fields.Selection([
        ('Code128', 'Code 128'),
        ('EAN13', 'EAN-13'),
        ('EAN8', 'EAN-8'),
        ('Code11', 'Code11'),
        ('Extended39', 'Extended39'),
        ('Extended93', 'Extended93'),
        ('FIM', 'FIM'),
        ('I2of5', 'I2of5'),
        ('MSI', 'MSI'),
        ('POSTNET', 'POSTNET'),
        ('Standard39', 'Standard39'),
        ('Standard93', 'Standard93'),
        ('UPCA', 'UPCA'),
        ('USPS_4State', 'USPS_4State')
    ], default='Code128', string='Type of Barcode')
    sh_page_height = fields.Integer('PDF Page Height', required=True)
    sh_page_width = fields.Integer('PDF Page Width', required=True)
    sh_page_orientation = fields.Selection([('Portrait', 'Portrait'), (
        'Landscape', 'Landscape')], default='Portrait', string='Page Orientation', required=True)
    sh_barcode_height = fields.Char("Barcode Height")
    sh_barcode_width = fields.Char("Barcode Width")
    paperformat_id = fields.Many2one(
        'report.paperformat', string='Paper Format')
    sh_barcode_field_id = fields.Many2one('ir.model.fields', domain=[('model_id.model', '=', 'product.product'), ('ttype', 'not in', [
                                          'binary', 'many2many', 'many2one_reference', 'one2many', 'reference'])], string='Barcode Field', ondelete='cascade')
    sh_label_display = fields.Boolean(string='Is Label Display ?')
    sh_template_line_ids = fields.One2many(
        'sh.dynamic.template.line', 'template_id', string='Template Line')
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 default=lambda self: self.env.company)
    is_valid = fields.Boolean('Is Valid ?', compute='_compute_valid_field')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ShProductLabelDynamicTemplate, self).create(vals_list)
        for vals in vals_list:
            paperformat_id = self.env['report.paperformat'].sudo().create({
                'name': res.name,
                'format': 'custom',
                'page_height': res.sh_page_height,
                'page_width': res.sh_page_width,
                'orientation': res.sh_page_orientation,
                'dpi': 90,
                'margin_top': 5.00,
                'margin_bottom': 5.00,
                'header_spacing': 15,
            })
            res.paperformat_id = paperformat_id.id
            if res.is_valid:
                raise UserError(_("You can not Add Duplicate Fields"))
            if res.sh_barcode_field_id and not res.sh_template_line_ids:
                raise UserError(_(
                    "Please select fields which you have defined in dynamic barcode lines, If you have not added pls add field first in dynamic barcode label lines."))
            elif res.sh_barcode_field_id and res.sh_template_line_ids:
                lines = []
                for line in res.sh_template_line_ids:
                    if line.sh_field_id.id == res.sh_barcode_field_id.id:
                        lines.append(line.sh_field_id.id)
                if len(lines) == 0:
                    raise UserError(_(
                        "Please select fields which you have defined in dynamic barcode lines, If you have not added pls add field first in dynamic barcode label lines."))
        return res

    def write(self, vals):
        paperformat_vals = {}
        if vals.get('sh_page_height'):
            paperformat_vals.update({
                'page_height': vals.get('sh_page_height')
            })
        if vals.get('sh_page_width'):
            paperformat_vals.update({
                'page_width': vals.get('sh_page_width')
            })
        if vals.get('sh_page_orientation'):
            paperformat_vals.update({
                'orientation': vals.get('sh_page_orientation')
            })
        if self.paperformat_id and paperformat_vals:
            self.paperformat_id.sudo().write(paperformat_vals)
        res = super(ShProductLabelDynamicTemplate, self).write(vals)
        if self:
            for rec in self:
                if rec.is_valid:
                    raise UserError(_("You can not Add Duplicate Fields"))
                if rec.sh_barcode_field_id and not rec.sh_template_line_ids:
                    raise UserError(_(
                        "Please select fields which you have defined in dynamic barcode lines, If you have not added pls add field first in dynamic barcode label lines."))
                elif rec.sh_barcode_field_id and rec.sh_template_line_ids:
                    lines = []
                    for line in rec.sh_template_line_ids:
                        if line.sh_field_id.id == rec.sh_barcode_field_id.id:
                            lines.append(line.sh_field_id.id)
                    if len(lines) == 0:
                        raise UserError(_(
                            "Please select fields which you have defined in dynamic barcode lines, If you have not added pls add field first in dynamic barcode label lines."))
        return res

    def unlink(self):
        for rec in self:
            rec.paperformat_id.unlink()
        return super(ShProductLabelDynamicTemplate, self).unlink()

    @api.depends('sh_template_line_ids')
    def _compute_valid_field(self):
        """Decide the one2many duplicate line added or not with same field"""
        if self:
            for rec in self:
                rec.is_valid = False
                field_ids = []
                for rec_line in rec.sh_template_line_ids:
                    if rec_line.sh_field_id.id in field_ids:
                        rec.is_valid = True
                        break
                    else:
                        field_ids.append(rec_line.sh_field_id.id)


class ShProductLabelDynamicTemplateLine(models.Model):
    _name = 'sh.dynamic.template.line'
    _description = 'Template Lines'
    _order = 'sequence'

    template_id = fields.Many2one('sh.dynamic.template', string='Template')
    sequence = fields.Integer('Sequence', default=1,
                              help="Used to handle lines.")
    type = fields.Selection([('field','Field'),('text','Text')],default='field',string='Display Type')
    sh_field_type= fields.Selection([('product_type','Product Type'),('customer_type','Customer Type')],default='product_type',string='field Type')
    sh_custom_domain= fields.Char('Sample Text ')
    name = fields.Char('Sample Text')
    image_height = fields.Char('Height')
    image_width = fields.Char('Width')
    sh_field_id = fields.Many2one('ir.model.fields', ondelete='cascade', string='Field')
    ttype = fields.Selection(related='sh_field_id.ttype')
    sh_margin = fields.Char(string='Margin')
    sh_font_size = fields.Char(string='Font Size')
    sh_font_color = fields.Char(string='Font Color')
    sh_position = fields.Selection(
        [('left', 'Left'), ('center', 'Center'), ('right', 'Right')], default='left', string='Position')
    sh_font_bold = fields.Boolean('Font Bold')
    sh_font_underline = fields.Boolean('Font Underline')
    sh_font_italic = fields.Boolean('Font Italic')
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 default=lambda self: self.env.company)
    sh_is_price_field = fields.Boolean(string='Is Price Field ?')
    currency_id = fields.Many2one('res.currency', string='Currency')
    sh_currency_position = fields.Selection(
        [('after', 'After'), ('before', 'Before')], string='Currency Symbol Position', default='after')
    sh_pricelist_id = fields.Many2one('product.pricelist',string='Pricelist')

    @api.onchange('sh_field_type','type')
    def return_domain(self):
        """Return domain on ir.model.fields display either product field or customer field in the list"""
        field_list = []
        if self.type and self.type=='text':
            self.sh_field_id = False
        if self.sh_field_type == 'product_type':
            field_obj = self.env['ir.model.fields'].search([('ttype', 'not in', ['many2many', 'many2one_reference', 'one2many', 'reference']),('model','=','product.product')])
            if field_obj:
                for field_id in field_obj:
                    field_list.append(field_id.id)
        elif self.sh_field_type == 'customer_type':
            field_obj = self.env['ir.model.fields'].search([('ttype', 'not in', ['many2many', 'many2one_reference', 'one2many', 'reference']),('model','=','res.partner')])
            if field_obj:
                for field_id in field_obj:
                    field_list.append(field_id.id)
        domain = {'sh_field_id': [('id', 'in', field_list)]}
        return {'domain': domain}
