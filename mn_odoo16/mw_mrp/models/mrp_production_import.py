# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools, Command
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections
from calendar import monthrange
from io import BytesIO
import base64
# import encodestring
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd
import logging

_logger = logging.getLogger(__name__)


class mrp_production_import(models.Model):
    _name = 'mrp.production.import'
    _inherit = ['mail.thread']
    _description = 'mrp production import'
    _order = 'date desc,name'

    name = fields.Char('Нэр')
    date = fields.Date('Огноо', required=True)
    state = fields.Selection([('draft','Ноорог'), ('done','Дууссан')], default='draft', string='Төлөв')
    is_bom = fields.Boolean('BOM оос тооцох?')
    company_id = fields.Many2one('res.company', string='Компани', required=True, default=lambda self: self.env.company)
    import_data = fields.Binary('Импортлох эксел', copy=False)
    export_data = fields.Binary('Export excel file')
    line_ids = fields.Many2many('mrp.production','mrp_production_import_move_res','import_id','move_id','Moves')
    # journal_id = fields.Many2one('account.journal','Journal')
    branch_id = fields.Many2one('res.branch', string='Салбар')
    
    def action_done(self):
        self.write({'state':'done'})


    def action_post(self):
        for item in self:
            for line in item.line_ids:
                line.post()
#         self.write({'state':'done'})

    
    def action_draft(self):
        self.write({'state':'draft'})

    
    def action_export(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(u'moves')
        
        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(9)
        h1.set_align('center')
        h1.set_font_name('Arial')

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#9ad808')
        header.set_text_wrap()
        header.set_font_name('Arial')
        
        header_wrap = workbook.add_format({'bold': 1})
        header_wrap.set_text_wrap()
        header_wrap.set_font_size(11)
        header_wrap.set_align('center')
        header_wrap.set_align('vcenter')
        header_wrap.set_border(style=1)
        # header_wrap.set_fg_color('#6495ED')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_right = workbook.add_format()
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)
        contest_right.set_num_format('#,##0.00')

        contest_center = workbook.add_format()
        contest_center.set_text_wrap()
        contest_center.set_font_size(9)
        contest_center.set_align('center')
        contest_center.set_align('vcenter')
        contest_center.set_border(style=1)
        contest_center.set_font_name('Arial')

        cell_format2 = workbook.add_format({
        'border': 1,
        'align': 'right',
        'font_size':9,
        'font_name': 'Arial',
        # 'text_wrap':1,
        'num_format':'#,####0'
        })

        row = 0
        last_col = 9
        if self.is_bom:
            worksheet.write(row, 0, u"Дугаар", header)
            worksheet.write(row, 1, u"Огноо", header)
            worksheet.write(row, 2, u"ББ барааны код", header)
            worksheet.write(row, 3, u"ББ Агуулах код", header)
            # worksheet.write(row, 4, u"Утга", header)
            worksheet.write(row, 4, u"Тоо хэмжээ", header)
            worksheet.write(row, 5, u"Ээлж", header)
        else:
            worksheet.write(row, 0, u"Дугаар", header)
            worksheet.write(row, 1, u"Огноо", header)
            worksheet.write(row, 2, u"ББ барааны код", header)
            worksheet.write(row, 3, u"ББ Агуулах код", header)
            # worksheet.write(row, 4, u"Утга", header)
            worksheet.write(row, 4, u"Тоо хэмжээ", header)            
            worksheet.write(row, 5, u"ТЭМ код", header)  
            worksheet.write(row, 6, u"ТЭМ тоо", header)  
            worksheet.write(row, 7, u"ТЭМ байрлал нэр", header)  
            worksheet.write(row, 8, u"Ээлж", header)
        workbook.close()

        out = base64.encodebytes(output.getvalue())
        excel_id = self.write({'export_data': out})

        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=mrp.production.import&id=" + str(self.id) + "&filename_field=filename&download=true&field=export_data&filename=" + self.name+'.xlsx',
             'target': 'new',
        }

    def _get_move_raw_import_values(self, product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        """ Warning, any changes done to this method will need to be repeated for consistency in:
            - Manually added components, i.e. "default_" values in view
            - Moves from a copied MO, i.e. move.create
            - Existing moves during backorder creation """
        source_location = self.location_src_id
        data = {
            'sequence': bom_line.sequence if bom_line else 10,
            'name': _('New'),
            'date': self.date_planned_start,
            'date_deadline': self.date_planned_start,
            'bom_line_id': bom_line.id if bom_line else False,
            'picking_type_id': self.picking_type_id.id,
            'product_id': product_id.id,
            'product_uom_qty': product_uom_qty,
            'product_uom': product_uom.id,
            'location_id': source_location.id,
            'location_dest_id': self.product_id.with_company(self.company_id).property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': operation_id,
            'price_unit': product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self._get_origin(),
            'state': 'draft',
            'warehouse_id': source_location.warehouse_id.id,
            'group_id': self.procurement_group_id.id,
            'propagate_cancel': self.propagate_cancel,
            'manual_consumption': self.env['stock.move']._determine_is_manual_consumption(product_id, self, bom_line),
        }
        return data


    def _get_moves_raw_import_values(self,productions,tem_qty,tem):
        moves = []
        for production in productions:
            # if not production.bom_id:
            #     continue
                
            # factor = production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id) / production.bom_id.product_qty
            # boms, lines = production.bom_id.explode(production.product_id, factor, picking_type=production.bom_id.picking_type_id)
            # for bom_line, line_data in lines:
            #     if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom' or\
            #             bom_line.product_id.type not in ['product', 'consu']:
            #         continue
                # operation = bom_line.operation_id.id or line_data['parent_line'] and line_data['parent_line'].operation_id.id
                bom_line =production.bom_id.bom_line_ids.filtered(lambda m: m.product_id == tem)
                print ('bom_line11 ',bom_line)
                
                moves.append(production._get_move_raw_values(
                    tem,
                    tem_qty,
                    tem.uom_id,
                    bom_line,
                    False
                ))
        print ('moves ',moves)
        return moves
    
    def action_import(self):
        if not self.import_data:
            raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')

        try:
            fileobj = NamedTemporaryFile('w+b')
            fileobj.write(base64.b64decode(self.import_data))
            fileobj.seek(0)
            book = xlrd.open_workbook(fileobj.name)
        except ValueError:
            raise UserError(
                _('Error loading data file. \ Please try again!'))
        

        
        try :
            sheet = book.sheet_by_index(0)
        except:
            raise osv.except_osv(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
        nrows = sheet.nrows
        
        rowi = 1
        production_obj = self.env['mrp.production']
        picking_type_obj = self.env['stock.picking.type']
        product_obj = self.env['product.product']
        
        warehouse_obj = self.env['stock.warehouse']
        location_obj = self.env['stock.location']
        moves={}
        line_vals=[]
        debit_sum=credit_sum=0
        recon_aml_ids=[]
        partners=''
        if not self.is_bom:
            for item in range(rowi,nrows):
                row = sheet.row(item)
                move_id = row[0].value
                excel_date = row[1].value
                product_code = row[2].value
                picking_type = row[3].value
                # name = row[4].value
                qty = row[4].value
                tem_code = row[5].value
                tem_qty = row[6].value
                location_tem = row[7].value
                shift = row[8].value
                if shift and shift=='Шөнө':
                    shift='night'
                else:
                    shift='day'
                product_code = str(product_code).split('.')[0]
                tem_code = str(tem_code).split('.')[0]
                _logger.info('loggg wh code {}'.format(picking_type))
                
                wh_id = warehouse_obj.search([('code','=',str(picking_type))], limit=1)
                
                _logger.info('loggg wh wh_id {}'.format(wh_id))
                if wh_id:
                    picking_type_id=wh_id.manu_type_id
                else:
                    raise UserError(_(u'Агуулах олдсонгүй {0}.'.format(picking_type)))
                print ('picking_type_id0 ',picking_type_id)
    
                if not self.date:
                    raise UserError(_(u'Огноо оруулана уу.'))
                date=self.date
                if excel_date:
                    dd=excel_date
                    try:
                        if type(dd)==float:
                            serial = dd
                            seconds = (serial - 25569) * 86400.0
                            date=datetime.utcfromtimestamp(seconds)
                        else:
                            date = datetime.strptime(dd, '%Y-%m-%d')
                    except ValueError:
                        raise ValidationError(_('Date error %s row! \n \
                        format must \'YYYY-mm-dd\'' % rowi))
                if picking_type_id:
                    picking_type_id=picking_type_id.id
                else:
                    raise UserError(_(u'Агуулахын ажилбар олдсонгүй {0}.'.format(picking_type)))
                
                product_id=False
                product=False
                location_id=False
                tem_id=False
                tem=False
                
                if location_tem:
                    location_id = location_obj.search([('name','=',location_tem),('usage','=','internal')], limit=1)
                    _logger.info('loggg  location_id {}'.format(location_id))
                if not location_id:
                    raise UserError(_('Location not found: {0}'.format(location_tem)))
                if product_code:
                    product = self.env['product.product'].search([('default_code', '=', product_code)])
                    if not product:
                        raise UserError(_("No product matching '%s'.") % product_code)
                    elif len(product.ids)>1:
                        raise UserError(_("Too many product matching '%s'.") % product_code)
                        
                    product_id = product.id
                if tem_code:
                    tem = self.env['product.product'].search([('default_code', '=', tem_code)])
                    if not tem:
                        raise UserError(_("Кодтой бараа олдсонгүй '%s'.") % tem_code)
                    elif len(tem.ids)>1:
                        raise UserError(_("Too many product matching '%s'.") % tem_code)
                        
                    tem_id = tem.id                    
                picking_type = picking_type_id and self.env['stock.picking.type'].browse(picking_type_id)
                # boms_by_product = self.env['mrp.bom'].with_context(active_test=True)._bom_find(product, picking_type=picking_type, company_id=self.env.user.company_id.id, bom_type='normal')
                # print ('boms_by_product ',boms_by_product)
                # bom = boms_by_product[product]
                bom=self.env['mrp.bom'].search([('product_tmpl_id','=',product.product_tmpl_id.id)],limit=1)
                
                if moves.get(move_id):
                    continue
                else:
                    production_dict = {
                        'product_id': product_id,
                        'product_qty':qty,
                        'date_planned_start': date,
                        'picking_type_id':picking_type_id,
                        'bom_id':bom.id,
                        'shift_select':shift,
                        'branch_id':self.branch_id.id
                    }
                    new_move_id = production_obj.with_context(check_move_validity=False).create(production_dict)  
                    moves[move_id]=new_move_id            
                    self.line_ids+=new_move_id     
        print ('moves ',moves)
                    
        for item in range(rowi,nrows):
            row = sheet.row(item)
            move_id = row[0].value
            excel_date = row[1].value
            product_code = row[2].value
            picking_type = row[3].value
            # name = row[4].value
            qty = row[4].value
            # credit = row[6].value
            # currency = row[7].value
            # currency_amount = row[8].value
            # analytic_code = row[9].value
            # technic_code = row[10].value
            # is_vat = row[11].value
            # is_vat = str(is_vat).split('.')[0]
            # reconcile_num = row[12].value   
            # branch_name = row[13].value    
            product_code = str(product_code).split('.')[0]
            
            # analytic_code = str(analytic_code).split('.')[0]
            # technic_code = str(technic_code).split('.')[0]
            # analytic_id = analytic_obj.search([('code','=',analytic_code)], limit=1)
            # account_id = account_obj.search([('code','=',account_code)], limit=1)
            # branch_id = self.env['res.branch'].search([('name','=',branch_name)], limit=1)
            
            print ('picking_type ',picking_type)
            wh_id = warehouse_obj.search([('code','=',picking_type)], limit=1)
            print ('wh_id ',wh_id)
            if wh_id:
                picking_type_id=wh_id.manu_type_id
            else:
                raise UserError(_(u'Агуулах олдсонгүй2 {0}.'.format(picking_type)))
            # picking_type_id = wh_id #picking_type_obj.with_context(lang='en_EN').search([('name','=',picking_type)], limit=1)
            print ('picking_type_id ',picking_type_id)

            if not self.date:
                raise UserError(_(u'Огноо оруулана уу.'))
            date=self.date
            if excel_date:
                dd=excel_date
                try:
                    if type(dd)==float:
                        serial = dd
                        seconds = (serial - 25569) * 86400.0
                        date=datetime.utcfromtimestamp(seconds)
                    else:
                        date = datetime.strptime(dd, '%Y-%m-%d')
                except ValueError:
                    raise ValidationError(_('Date error %s row! \n \
                    format must \'YYYY-mm-dd\'' % rowi))

            if picking_type_id:
                picking_type_id=picking_type_id.id
            else:
                raise UserError(_(u'Агуулахын ажилбар олдсонгүй2 {0}.'.format(picking_type)))
            
            product_id=False
            product=False
            if product_code:
                product = self.env['product.product'].search([('default_code', '=', product_code)])
                if not product:
                    raise UserError(_("No product matching '%s'.") % product_code)
                elif len(product.ids)>1:
                    raise UserError(_("Too many product matching '%s'.") % product_code)
                    
                product_id = product.id
            # print ('product_id ',product_id)
                                        
            # if moves.get(move_id):
            #     new_move_id=moves[move_id]
            # print ('partner_id ',partner_id)

            # picking_type_id = self._context.get('default_picking_type_id')
            picking_type = picking_type_id and self.env['stock.picking.type'].browse(picking_type_id)
            # boms_by_product = self.env['mrp.bom'].with_context(active_test=True)._bom_find(product, picking_type=picking_type, company_id=self.env.user.company_id.id, bom_type='normal')
            # print ('boms_by_product ',boms_by_product)
            # bom = boms_by_product[product]
            bom=self.env['mrp.bom'].search([('product_tmpl_id','=',product.product_tmpl_id.id)],limit=1)
            
                # production.bom_id = bom.id or False
            # print ('bom12 ',bom)
            if  self.is_bom:
                shift = row[5].value
                if shift and shift=='Шөнө':
                    shift='night'
                else:
                    shift='day'
                
                production_dict = {
                    # 'name': name,
                    'product_id': product_id,
                    'product_qty':qty,
                    'date_planned_start': date,
                    'picking_type_id':picking_type_id,
                    'bom_id':bom.id,
                    'shift_select':shift,
                    'branch_id':self.branch_id.id
                    # 'product_id':product_id 
                }
                production_id = production_obj.with_context(check_move_validity=False).create(production_dict)       
                production_id._onchange_product_id()   
                production_id._compute_cost_id()    
                
                # production_id._compute_move_finished_ids()  
                self.line_ids+=production_id
            else:
                if moves.get(move_id):
                    new_move_id=moves[move_id]
                
                tem_code = row[5].value
                tem_qty = row[6].value
                location_id=False
                location_tem = row[7].value
                if location_tem:
                    location_id = location_obj.search([('name','=',location_tem)], limit=1)
                    _logger.info('loggg  location_id2 {}'.format(location_id))
                
                product_code = str(product_code).split('.')[0]
                tem_code = str(tem_code).split('.')[0]
                tem=False
                if tem_code:
                    tem = self.env['product.product'].search([('default_code', '=', tem_code)])
                    if not tem:
                        raise UserError(_("Кодтой бараа олдсонгүй '%s'.") % tem_code)
                    elif len(tem.ids)>1:
                        raise UserError(_("Too many product matching '%s'.") % tem_code)
                        
                    tem_id = tem.id      
                print ('new_move_id ',new_move_id)  
                # bom_line =new_move_id.bom_id.bom_line_ids.filtered(lambda m: m.product_id == tem)
                move_raw_id=new_move_id.move_raw_ids.filtered(lambda m: m.product_id == tem)
                print ('move_raw_id ',move_raw_id)
                if move_raw_id:
                    move_raw_id.write({'product_uom_qty':tem_qty})
                if location_id:
                    new_move_id.move_raw_ids.filtered(lambda m: m.product_id == tem).write({'location_id':location_id.id})
                # self._get_moves_raw_import_values(new_move_id,tem_qty,tem)               
            # self.line_ids+= production_obj.with_context(check_move_validity=False).new(production_dict)    
            # self.line_ids._onchange_product_id()   
            # self.line_ids._onchange_product_id()   
            # self.line_ids._compute_move_raw_ids()    
            # self.line_ids._compute_move_finished_ids()  
            
        return True            
         
    
         
    
