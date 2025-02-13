# -*- coding: utf-8 -*-

from odoo import api, models, fields
  
class stock_move(models.Model):
    _inherit = 'stock.move'
    
    power_product_id = fields.Many2one('power.product', 'Цахилгааны бүртгэлд')

class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    power_product_id = fields.Many2one('power.product', related='move_ids.power_product_id', string='Цахилгааны Барааны бүртгэл')
    power_workorder_id = fields.Many2one('power.workorder', related='move_ids.power_product_id.workorder_id', string='Цахилгааны EO')
    
    def action_view_power(self):
        eo_ids = self.power_product_id.mapped('workorder_id')
        if eo_ids:
            action = self.env.ref('mw_power.action_power_workorder_tree').read()[0]
            action['domain'] = [('id', 'in', eo_ids.ids)]
            return action
    
    def get_user_signature(self,ids):
        if self.browse(ids).power_workorder_id:
            return self.get_user_signature_eo(ids)
        return super(stock_picking, self).get_user_signature(ids)

    def get_user_signature_eo(self,ids):
        report_id = self.browse(ids)
        if report_id.power_workorder_id:
            html = '<table>'
            image_str = '________________________'
            user_id = report_id.power_workorder_id.open_user_id
            image_str = ''
            if user_id.digital_signature:
                image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,'+user_id.digital_signature+'" />'
            user_str =  '________________________'
            if user_id:
                user_str = user_id.name
            html += u'<tr><td><p>Нээсэн </p></td><td>'+image_str+u'</td><td> <p>/'+user_str+u'/</p></td></tr>'

            image_str = '________________________'
            user_id = report_id.power_workorder_id.confirmed_user_id
            image_str = ''
            if user_id.digital_signature:
                image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,'+user_id.digital_signature+'" />'
            user_str =  '________________________'
            if user_id:
                user_str = user_id.name
            html += u'<tr><td><p>Баталгаажуулсан </p></td><td>'+image_str+u'</td><td> <p>/'+user_str+u'/</p></td></tr>'

            image_str = '________________________'
            user_id = report_id.power_workorder_id.done_user_id
            image_str = ''
            if user_id.digital_signature:
                image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,'+user_id.digital_signature+'" />'
            user_str =  '________________________'
            if user_id:
                user_str = user_id.name
            html += u'<tr><td><p>Хаасан </p></td><td>'+image_str+u'</td><td> <p>/'+user_str+u'/</p></td></tr>'

            html += '</table>'   
            return html
        return ''