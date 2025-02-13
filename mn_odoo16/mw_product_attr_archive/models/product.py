# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    # 
    def _unlink_or_archive(self, check_access=True):
        """Unlink or archive products.
        Try in batch as much as possible because it is much faster.
        Use dichotomy when an exception occurs.
        """

        # Avoid access errors in case the products is shared amongst companies
        # but the underlying objects are not. If unlink fails because of an
        # AccessError (e.g. while recomputing fields), the 'write' call will
        # fail as well for the same reason since the field has been set to
        # recompute.
        if check_access:
            self.check_access_rights('unlink')
            self.check_access_rule('unlink')
            self.check_access_rights('write')
            self.check_access_rule('write')
            self = self.sudo()

        try:
            with self.env.cr.savepoint(), tools.mute_logger('odoo.sql_db'):
                self.unlink()
        except Exception:
            # We catch all kind of exceptions to be sure that the operation
            # doesn't fail.
            if len(self) > 1:
                self[:len(self) // 2]._unlink_or_archive(check_access=False)
                self[len(self) // 2:]._unlink_or_archive(check_access=False)
            else:
                if self.active:
                    # Note: this can still fail if something is preventing
                    # from archiving.
                    # This is the case from existing stock reordering rules.
                    raise ValidationError(u'%s барааг хувилбар нэмж идэвхигүй болгох гэж байна эсвэл хувилбараа нэг нэгээр нэм'%(self.display_name))
                    self.write({'active': False})
        return super(ProductProduct, self)._unlink_or_archive(check_access)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def view_attr_change(self):
        obj = self.env['product.attr.wizard']
        obj_id = obj.create({})
        view = self.env.ref('mw_product_attr_archive.product_attr_wizard_form')
        view_id = view and view.id or False
        context=dict(self._context or {})
        return {
                'name': 'Хувилбар шилжүүлэх',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'product.attr.wizard',
                'views': [(view.id,'form')],
                'view_id': view_id,
                'res_id': obj_id.id,
                'target': 'new',
                'context': context
        }
        
class ProductProduct(models.Model):
    _inherit = "product.product"

    def view_attr_change(self):
        obj = self.env['product.attr.wizard']
        obj_id = obj.create({})
        view = self.env.ref('mw_product_attr_archive.product_attr_wizard_form')
        view_id = view and view.id or False
        context=dict(self._context or {})
        return {
                'name': 'Хувилбар шилжүүлэх',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'product.attr.wizard',
                'views': [(view.id,'form')],
                'view_id': view_id,
                'res_id': obj_id.id,
                'target': 'new',
                'context': context
        }
        
class ProductAttrWizard(models.TransientModel):
    _name = 'product.attr.wizard'
    _description = 'product attr wizard'

    # type = fields.Selection([('negtgeh','Нэгт')], string='Төрөл', required=True)
    product_id = fields.Many2one('product.product', string='Бараа хувилбар')
    product_tmpl_id = fields.Many2one('product.template', string='Нэгтгэх темплати')

    def change(self):
        tmpl_id = self.product_id.product_tmpl_id
        to_tmpl_id = self.product_tmpl_id
        attr = self.env['product.attribute']
        attr_value = self.env['product.attribute.value']
        tmpl_value = self.env['product.template.attribute.value']
        tmpl_line = self.env['product.template.attribute.line']
        aa = attr.search([], limit=1)
        attr_value_id = attr_value.search([('attribute_id','=',aa.id), ('name','=',self.product_id.default_code)], limit=1)
        if not attr_value_id:
            attr_value_id = attr_value.create({
                'attribute_id': aa.id,
                'name': self.product_id.default_code
            })
        tml_value_id = False
        
        if attr_value_id and len(to_tmpl_id.product_variant_ids)==1 and not to_tmpl_id.attribute_line_ids:
            p_id = to_tmpl_id.product_variant_ids[0]
            attr_value_id_to = attr_value.search([('attribute_id','=',aa.id), ('name','=',p_id.default_code)], limit=1)
            if not attr_value_id_to:
                attr_value_id_to = attr_value.create({
                    'attribute_id': aa.id,
                    'name': p_id.default_code
                })
            tmpl_line_id = tmpl_line.create({
                'product_tmpl_id': to_tmpl_id.id,
                'attribute_id': aa.id,
                'value_ids': [(6, 0, [attr_value_id_to.id])],
            })
            source_tmpl_line_id2 = tmpl_line.create({
                'product_tmpl_id': tmpl_id.id,
                'attribute_id': aa.id,
                'value_ids': [(6, 0, [attr_value_id.id])],
            })
            to_tmpl_id.attribute_line_ids.value_ids += attr_value_id
            self.product_id.product_tmpl_id = to_tmpl_id.id
            delete_p = self.env['product.product'].search([('product_tmpl_id','=',to_tmpl_id.id)], order='id desc', limit=1)
            # print ('')
            if delete_p:
                delete_p.unlink()
            tmpl_id.available_in_pos = False
            tmpl_id.active = False

        view = self.env.ref('mw_product_attr_archive.product_attr_wizard_form')
        view_id = view and view.id or False
        return {
                'name': 'Хувилбар шилжүүлэх',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'product.attr.wizard',
                'views': [(view.id,'form')],
                'view_id': view_id,
                'res_id': self.id,
                'target': 'new',
                'context': self.env.context
        }
