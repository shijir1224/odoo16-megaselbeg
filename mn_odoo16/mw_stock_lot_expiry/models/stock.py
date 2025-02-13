# -*- coding: utf-8 -*-
#!/usr/bin/python
from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
_logger = logging.getLogger(__name__)

class stock_picking_type(models.Model):
    _inherit = 'stock.picking.type'

    lot_date_required_in = fields.Boolean('Орлого авахад заавал цуврал дуусах хугацаа оруулах', default=False, copy=False)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    warning_lot_messages = fields.Html(string='Warning Message', compute='_compute_lot_messages' )
    # Үлдэгдэл шалгах
    
    @api.depends('move_line_ids.product_id','move_line_ids.lot_name')
    def _compute_lot_messages(self):
        for obj in self:
            header = u'<table style="width: 100%; color: #FFA500;"><tr><th>Барааны нэр</th><th>LOT дугаар</th></tr>' 
            message = ""
            # Bayasaa zasav tuluvuus hamaarch bolon zuvhun orlogo deer shalgadag bolgov
            # for line in obj.move_line_ids:
            for line in obj.move_line_ids.filtered(lambda r: r.state not in ['done','cancel'] and r.location_id.usage not in ['internal', 'transit'] and r.location_dest_id.usage in ['internal', 'transit']):
                dup_ids = self.env['stock.lot'].search([
                    ('product_id','=',line.product_id.id),
                    ('name','=',line.lot_name)])
                if len(dup_ids) > 0:
                    temp =u'<tr>\
                                <td><b style="color:red">%s</b></td>\
                                <td><b style="color:red">%s</b></td>\
                            </tr>' % (line.product_id.display_name, line.lot_name)
                    message += temp
                elif obj.move_line_ids.filtered(lambda r: r.id!=line.id and r.product_id.id==line.product_id.id and r.lot_name==line.lot_name):
                    temp =u'<tr>\
                                <td><b style="color:blue">%s</b></td>\
                                <td><b style="color:blue">%s</b></td>\
                            </tr>' % (line.product_id.display_name, line.lot_name)
                    message += temp
            if message:
                message = header + message + "</table>"
                obj.warning_lot_messages = message
            else:
                obj.warning_lot_messages = False    


    def view_duplicate_lot_messages(self):
        for obj in self:
            header = u'' 
            message = ""
            for line in obj.move_line_ids.filtered(lambda r: r.state not in ['done','cancel'] and r.location_id.usage not in ['internal', 'transit'] and r.location_dest_id.usage in ['internal', 'transit']):
                dup_ids = self.env['stock.lot'].search([
                    ('product_id','=',line.product_id.id),
                    ('name','=',line.lot_name)])
                if len(dup_ids) > 0:
                    temp =u'%s  LOT: %s \n' % (line.product_id.display_name, line.lot_name)
                    message += temp

                elif obj.move_line_ids.filtered(lambda r: r.id!=line.id and r.product_id.id==line.product_id.id and r.lot_name==line.lot_name):
                    temp =u'ЭНЭ БАРИМТАН ДОТОРОО %s  LOT: %s \n' % (line.product_id.display_name, line.lot_name)
                    message += temp
            if message:
                message = u'Давхардаж байгаа бараанууд\n' + message 
                
                raise UserError(message)

    def action_change_view_lot_date(self):
        self.ensure_one()

        # if self.state not in ['done'] and self.picking_id.picking_type_code!='incoming':
        #     raise UserError(u'Хөдөлгөөний Төлөв "Хүлээгдэж буй", "Ноорог" төлөвт байх ёстой')
        tree_view_id = self.env.ref('mw_stock_lot_expiry.view_production_lot_tree_update_date').id
        view_ids = self.move_line_ids.mapped('lot_id')

        action = {
                'name': 'ЛОТ огноо өөрчлөх',
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'stock.lot',
                'views': [(tree_view_id, 'tree')],
                'view_id': tree_view_id,
                'domain': [('id','in',view_ids.ids)],
                'type': 'ir.actions.act_window',
                'context': dict(self.env.context),
                'target': 'current'
            }
        return action

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    life_date_sm = fields.Datetime(related='lot_id.expiration_date', readonly=True, string="Дуусах хугацаа")
    life_date_sml_update = fields.Datetime('Дуусах хугацаа')
    
    def _action_done(self):
        res = super(StockMoveLine, self)._action_done()
        for item in self:
            duusah_hugatsaa = item.lot_id.expiration_date or item.life_date_sml_update
            if item.picking_id.picking_type_id.lot_date_required_in and not duusah_hugatsaa  and item.product_id.tracking in ['lot','serial']:
                raise UserError(u'Орлого дээр заавал дуусах хугцаа оруулна. %s '%(item.product_id.display_name))
            try:
                if item.lot_id and not item.lot_id.expiration_date and item.life_date_sml_update:
                    item.lot_id.expiration_date = item.life_date_sml_update
                if item.lot_id and not item.lot_id.alert_date and item.life_date_sml_update:
                    item.lot_id.alert_date = item.life_date_sml_update
            except Exception as e:
                _logger.info('lot expiry aldaa %s'%(e))
                pass
        return res

class StockLot(models.Model):
    _inherit = 'stock.lot'

    def name_get(self):
        res = []
        for item in self:
            res_name = super(StockLot, item).name_get()
            if item.expiration_date:
                res_name = res_name[0][1]+' | ' + item.expiration_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                res.append((item.id, res_name))
            else:
                res.append(res_name[0])
        return res

    # Гэрээний хугацаа шалгах - Крон метод
    @api.model
    def _check_expire_date(self):
        # Дуусч байгаа Гэрээ шалгах
        today = fields.Datetime.now()
        contracts = self.env['stock.lot'].search([
            ('quant_ids.quantity','>',0),
            ('quant_ids.location_id.usage','=','internal'),
            '|',
            ('alert_date','<=',today),
            ('expiration_date','<=',today),
            ])
        msg = contracts
        # print (blblbl)
        if msg:
            # Get group
            res_model = self.env['ir.model.data'].search([
                ('module','=','mw_stock_lot_expiry'),
                ('name','=','group_stock_lot_expiry_notification')], limit=1)
            group = self.env['res.groups'].search([('id','=',res_model.res_id)])
            html = u"<span style='font-size:12pt; font-weight:bold; color:red;'>Хугацаа дуусч буй бараанууд:<br/></span>"
            table = u'<table style="font-size:9pt; color:#841313;"><tr><th style="text-align: center;">Бараа</th><th style="text-align: center;">Лот</th><th style="text-align: center;">Мэдээлэх Огноо</th></tr>'
            for item in msg:
                table+=u'<tr>'
                table+= u'<td>'+item.product_id.display_name+u'</td>'
                table+= u'<td style="text-align: center; padding-left: 10px;">%s</td>'%(item.name)
                table+= u'<td style="text-align: center; padding-left: 10px;">%s</td>'%(item.alert_date)
                table+=u'</tr>'
            table += '</table><br/>'
            html+=table

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            action_id = self.env['ir.model.data'].get_object_reference('mw_stock_lot_expiry', 'action_production_lot_form_expiry')[1]
            html += u"""<b><a target="_blank" href=%s/web#view_type=list&model=stock.lot&action=%s>%s</a></b>"""% (base_url,action_id,u'Дэлгэрэнгүй Харах')
        
            for receiver in group.users:
                self.env['res.users'].send_chat(html, receiver.partner_id)

class StockQuantReport(models.Model):
    _inherit = "stock.quant.report"
    
    expiration_date = fields.Datetime('Дуусах Хугацаа', readonly=True)

    def _select(self):
        select_str = super(StockQuantReport, self)._select()
        select_str += """
            ,
            spl.expiration_date
        """
        return select_str

    def _from(self):
        select_str = super(StockQuantReport, self)._from()
        select_str += """
            LEFT JOIN stock_lot spl ON (spl.id=sq.lot_id)
        """
        return select_str