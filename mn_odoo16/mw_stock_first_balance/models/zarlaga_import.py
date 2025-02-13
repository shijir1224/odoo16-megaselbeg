
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from io import BytesIO
import base64
from tempfile import NamedTemporaryFile
import os,xlrd
from odoo.exceptions import UserError,Warning

import logging
_logger = logging.getLogger(__name__)

# str_date = row[0].value
# str_location_name = row[1].value
# str_product_code = row[2].value
# str_product_qty = row[3].value

# 0 date
# 1 dotood code
# 2 location name
# 3 too hemjee
# 4 technic
# 5 price_unit
# 6 serial lot

class zarlaga_import(models.Model):
    _name = "zarlaga.import"
    _description = 'zarlaga import'

    name = fields.Char('Нэр')
    state = fields.Selection([('draft','Draft'),('create','Хөдөлгөөн үүссэн'),('done','Зарлага батлагдсан')], 'State', default='draft')
    
    import_data = fields.Binary('Импортлох эксел', copy=False)
    result = fields.Text('Үр дүн', readonly=True)
    line_ids = fields.One2many('zarlaga.import.line', 'parent_id', 'Мөрүүд')
    total_qty = fields.Float('Нийт тоо хэмжээ', compute="_compute_all", store=True)
    count_move = fields.Integer('Хөдөлгөөний тоо', compute="_compute_all", store=True)
    is_technic = fields.Boolean('Техниктэй эсэх', default=False)

    type = fields.Selection([('default_code','Дотоод кодоор'), ('barcode','Баркодоор')], 'Бараа Импортлох төрөл', default='default_code')
    import_type = fields.Selection([('zarlaga','Зарлага'), ('internal','Дотоод Хөдөлгөөн')], 'Импортлох төрөл', default='zarlaga', required=True)


    def action_draft(self):
        self.state='draft'

    @api.depends('line_ids.product_qty','line_ids')
    def _compute_all(self):
        for item in self:
            item.total_qty = sum(item.line_ids.mapped('product_qty'))
            item.count_move = len(item.line_ids.mapped('stock_move_id'))

    def remove_line(self):
        self.line_ids.unlink()

    def update_date(self):
        for item in self.line_ids.filtered(lambda r: r.stock_move_id):
            check_date = item.stock_move_id.date[:10]
            time_date = item.stock_move_id.date[10:20]
            set_date = item.date+time_date
            item.stock_move_id.date = set_date
            move_line_ids = self.env['stock.move.line'].search([('move_id','=',item.stock_move_id.id)])
            if move_line_ids:
                move_line_ids.write({'date':set_date})
            item.stock_move_id.date = set_date
            item.stock_move_id.date_expected = set_date
            if item.stock_move_id.picking_id:
                item.stock_move_id.picking_id.scheduled_date = set_date
                item.stock_move_id.picking_id.date_done = set_date

            move_id = self.env['account.move'].search([('stock_move_id','=',item.stock_move_id.id)], limit=1)
            if move_id:
                query = """
                UPDATE account_move set date='%s' where id=%s
                """%(item.date,move_id.id)

                self._cr.execute(query)
                query = """
                UPDATE account_move_line set date='%s' where move_id=%s
                """%(item.date,move_id.id)
                self._cr.execute(query)

    def view_stock_move(self):
        picking_obj = self.env['stock.picking']
        context = dict(self._context)
        context['create']= False
        tree_view_id = self.env.ref('stock.vpicktree').id
        form_view_id = self.env.ref('stock.view_picking_form').id
        action = {
                'name': self.name,
                'view_mode': 'tree',
                'res_model': 'stock.picking',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_id': tree_view_id,
                'domain': [('id','in',self.line_ids.mapped('stock_move_id.picking_id').ids)],
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'current'
            }
        return action

    def create_expense_picking(self, date, ware_id, line_ids, to_ware_id=False):
        picking_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        wh_id = self.env['stock.warehouse'].browse(ware_id)
        if not wh_id:
            raise UserError(u'Агуулах олдсонгүй Огноо: %s  Агуулах ID: %s '%(date,ware_id))
        picking_type_id = False
        location_dest_id = False
        if self.import_type=='zarlaga':
            location_dest_id = self.env['stock.location'].search([('usage','=','customer')], limit=1)
            picking_type_id = wh_id.out_type_id
        name = (u''+self.name+u' '+str(date)+u' '+wh_id.name) or ''
        if self.import_type=='internal':
            to_wh_id = self.env['stock.warehouse'].browse(to_ware_id)
            location_dest_id = to_wh_id.lot_stock_id
            picking_type_id = wh_id.int_type_id
            name+=u' internal'
        else:
            name+=u' zarlaga'
        
        picking_id = picking_obj.create({
                'picking_type_id': picking_type_id.id,
                'location_id': wh_id.lot_stock_id.id,
                'location_dest_id': location_dest_id.id,
                'scheduled_date': date,
                'move_ids': [],
                'origin': name
            })
        move_lines = []
        for item in line_ids:
            desc = item.desc if item.desc else ''
            move ={
                'name': name+u' '+item.product_id.name+u' '+desc,
                'product_id': item.product_id.id,
                'product_uom': item.product_id.uom_id.id,
                'product_uom_qty': item.product_qty,
                'picking_type_id': picking_type_id.id,
                'location_id': item.location_id.id,
                'location_dest_id': item.to_location_id.id if self.import_type=='internal' else location_dest_id.id,
                'picking_id': picking_id.id,

                # 'technic_id2': item.technic_id.id if item.technic_id else False
                }
            move_id = move_obj.create(move)
            move_id._action_confirm(merge=False, merge_into=False)
            if item.stock_move_id:
                raise UserError(u'stock_move_id %s ID bn'%(item.stock_move_id))
            item.stock_move_id = move_id.id
        

    def action_create(self):
        stock_pick_obj = self.env['stock.picking']
        stock_move_obj = self.env['stock.move']
        if self.import_type=='internal':
            query = """SELECT zil.date,sl.set_warehouse_id,sl_to.set_warehouse_id as to_set_warehouse_id
            from zarlaga_import_line zil 
            left join stock_location sl on zil.location_id=sl.id
            left join stock_location sl_to on zil.to_location_id=sl_to.id
             where zil.parent_id=%s and zil.stock_move_id is null
             group by 1,2,3"""%(self.id)

            self._cr.execute(query)
            group_line_ids = self.env.cr.dictfetchall()
            for item in group_line_ids:
                l_ids = self.line_ids.filtered(lambda r: r.date==item['date'] and r.location_id.set_warehouse_id.id==item['set_warehouse_id'] and r.to_location_id.set_warehouse_id.id==item['to_set_warehouse_id'] and not r.stock_move_id )
                self.create_expense_picking(item['date'], item['set_warehouse_id'], l_ids, item['to_set_warehouse_id'])
            self.state = 'create'
        else:    
            query = """SELECT zil.date,sl.set_warehouse_id 
            from zarlaga_import_line zil 
            left join stock_location sl on zil.location_id=sl.id
             where parent_id=%s
             group by 1,2"""%(self.id)

            self._cr.execute(query)
            group_line_ids = self.env.cr.dictfetchall()
            for item in group_line_ids:
                l_ids = self.line_ids.filtered(lambda r: r.date==item['date'] and r.location_id.set_warehouse_id.id==item['set_warehouse_id'] and not r.stock_move_id)
                self.create_expense_picking(item['date'], item['set_warehouse_id'], l_ids)
            self.state = 'create'

    def action_done_transfer(self, picking_ids):
        transfer = self.env['stock.immediate.transfer']
        transfer_id = transfer.create({'pick_ids':[]})
        transfer_id.pick_ids = picking_ids.ids 
        transfer_id.process()

    def action_done(self):
        picking_ids = self.line_ids.mapped('stock_move_id.picking_id')
        for item in picking_ids:
            if item.state in ['assigned']:
                self.action_done_transfer(item)
            elif item.state in ['draft','confirmed','waiting']:
                item.action_assign()
                if item.state in ['assigned']:
                    self.action_done_transfer(item)
        move_ids = self.line_ids.mapped('stock_move_id').filtered(lambda r:r.state!='done')
        
        if move_ids:
            raise UserError(u'Үлдэгдэл хүрээгүй бараанууд %s '%(', '.join(move_ids.mapped('product_id.default_code'))))
        else:
            self.state = 'done'   
    def action_import(self):
        if not self.import_data:
            raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')

        fileobj = NamedTemporaryFile('w+')
        fileobj.write(base64.decodebytes(self.import_data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise UserError(u'Алдаа Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        book = xlrd.open_workbook(fileobj.name)
        
        try :
            sheet = book.sheet_by_index(0)
        except:
            raise UserError(u'Алдаа Sheet -ны дугаар буруу байна.')
        nrows = sheet.nrows

        product_obj = self.env['product.product']
        technic_obj = self.env['technic.equipment']
        attr_obj = self.env['product.attribute.value']
        categ_obj = self.env['product.category']
        tmp_obj = self.env['product.template']
        line_obj = self.env['zarlaga.import.line']
        location_obj = self.env['stock.location']
        account_obj = self.env['account.account']

        not_found_def_code = []
        not_found_tech = []
        not_found_location = []
        not_found_account = []
        rowi = 1
        for item in range(rowi,nrows):
            _logger.info('shalgalt uldsen %s'%(nrows-item))
            row = sheet.row(item)
            str_date = row[0].value
            str_location_name = row[1].value
            str_to_location_name = row[2].value
            str_product_code = row[3].value
            str_product_qty = row[4].value
            
            
            if type(str_product_code) in [float]:
                default_code = str(str_product_code).strip().split('.')[0]
            elif type(str_product_code) in [int]:
                default_code = str(str_product_code).strip()
            else:
                default_code = str_product_code.strip()

            if self.type=='barcode':
                product_id = product_obj.search([('barcode','=',default_code)], limit=1)
            else:
                product_id = product_obj.search([('default_code','=',default_code)], limit=1)
            if not product_id and default_code:
                not_found_def_code.append(default_code)

            if self.is_technic:
                str_technic_name = row[4].value
                tech_name = str_technic_name
                if tech_name:
                    if type(tech_name) in [float]:
                        technic_name = str(tech_name).split('.')[0]
                        technic_id = technic_obj.search([('program_code','=',technic_name)], limit=1)
                        if not technic_id:
                            not_found_tech.append(technic_name)
                    else:
                        technic_name = tech_name.strip()
                        technic_id = technic_obj.search([('program_code','=',technic_name)], limit=1)
                        if not technic_id:
                            not_found_tech.append(technic_name)

            loc_name = str_location_name
            if loc_name:
                if type(loc_name) in [float]:
                    location_name = str(loc_name).split('.')[0]
                    location_id = location_obj.search([('name','=',location_name),('usage','=','internal')], limit=1)
                    if not location_id:
                        not_found_location.append(location_name)
                else:
                    location_name = loc_name.strip()
                    location_id = location_obj.search([('name','=',location_name),('usage','=','internal')], limit=1)
                    if not location_id:
                        not_found_location.append(location_name)

            loc_name = str_to_location_name
            if loc_name:
                if self.import_type=='internal':
                    if type(loc_name) in [float]:
                        location_name = str(loc_name).split('.')[0]
                        location_id = location_obj.search([('name','=',location_name),('usage','=','internal')], limit=1)
                        if not location_id:
                            not_found_location.append(location_name)
                    else:
                        location_name = loc_name.strip()
                        location_id = location_obj.search([('name','=',location_name),('usage','=','internal')], limit=1)
                        if not location_id:
                            not_found_location.append(location_name)
                elif self.import_type=='zarlaga':
                    if type(loc_name) in [float]:
                        account_name = str(loc_name).split('.')[0]
                        account_id = account_obj.search([('name','=',account_name)], limit=1)
                        if not account_id:
                            not_found_account.append(account_name)
                    else:
                        account_name = loc_name.strip()
                        account_id = account_obj.search([('name','=',account_name)], limit=1)
                        if not account_id:
                            not_found_account.append(account_name)

        if self.is_technic:     
            if not_found_def_code!=[] or not_found_tech!=[] or not_found_location!=[]:
                not_found_def_code = list(set(not_found_def_code))
                not_found_tech = list(set(not_found_tech))
                not_found_location = list(set(not_found_location))
                not_found_account = list(set(not_found_account))
                raise UserError(u'Олдоогүй Бараанууд \n %s \nОлдоогүй техникүүд \n %s \nОлдоогүй Байрлалууд \n %s \nОлдоогүй данс \n %s'%(', '.join(not_found_def_code),', '.join(not_found_tech),', '.join(not_found_location),', '.join(not_found_account)))
        else:
            if not_found_def_code!=[] or not_found_location!=[]:
                not_found_def_code = list(set(not_found_def_code))
                not_found_location = list(set(not_found_location))
                not_found_account = list(set(not_found_account))
                raise UserError(u'Олдоогүй Бараанууд \n %s \nОлдоогүй Байрлалууд \n %s \nОлдоогүй данс \n %s'%(', '.join(not_found_def_code),', '.join(not_found_location),', '.join(not_found_account)))
        
        rowi = 1
        # print blblb
        for item in range(rowi,nrows):
            _logger.info('uusgelt uldsen %s'%(nrows-item))
            row = sheet.row(item)
            
            str_date = row[0].value
            str_location_name = row[1].value
            str_to_location_name = row[2].value
            str_product_code = row[3].value
            str_product_qty = row[4].value
            str_to_desc = str(row[5].value) if row[5].value else ''

            if type(str_product_code) in [float]:
                default_code = str(str_product_code).strip().split('.')[0]
            elif type(str_product_code) in [int]:

                default_code = str(str_product_code).strip()
                
            else:
                default_code = str_product_code.strip()


            if self.type=='barcode':
                product_id = product_obj.search([('barcode','=',default_code)], limit=1)
            else:
                product_id = product_obj.search([('default_code','=',default_code)], limit=1)
            
            vals = {}
            if self.is_technic:
                str_technic_name = row[4].value
                tech_name = str_technic_name
                technic_id = False
                if tech_name:
                    if type(tech_name) in [float]:
                        technic_name = str(tech_name).split('.')[0]
                        technic_id = technic_obj.search([('program_code','=',technic_name)], limit=1)
                    else:
                        technic_name = tech_name.strip()
                        technic_id = technic_obj.search([('program_code','=',technic_name)], limit=1)
                vals['technic_id'] = technic_id.id if technic_id else False

            loc_name = str_location_name
            location_id = False
            if loc_name:
                if type(loc_name) in [float]:
                    location_name = str(loc_name).split('.')[0]
                    location_id = location_obj.search([('name','=',location_name),('usage','=','internal')], limit=1)
                else:
                    location_name = loc_name.strip()
                    location_id = location_obj.search([('name','=',location_name),('usage','=','internal')], limit=1)

            loc_name = str_to_location_name
            location_dest_id = False
            account_id = False
            if loc_name:
                if self.import_type=='internal':
                    if type(loc_name) in [float]:
                        location_name = str(loc_name).split('.')[0]
                        location_dest_id = location_obj.search([('name','=',location_name),('usage','=','internal')], limit=1)
                    else:
                        location_name = loc_name.strip()
                        location_dest_id = location_obj.search([('name','=',location_name),('usage','=','internal')], limit=1)
                
                elif self.import_type=='zarlaga':
                    if type(loc_name) in [float]:
                        account_name = str(loc_name).split('.')[0]
                        account_id = account_obj.search([('name','=',account_name)], limit=1)
                    else:
                        account_name = loc_name.strip()
                        account_id = account_obj.search([('name','=',account_name)], limit=1)
            


            product_qty = str_product_qty
            vals.update({
                'parent_id': self.id,
                'location_id': location_id.id if location_id else False,
                'to_location_id':  location_dest_id.id if location_dest_id else False,
                'account_id':  account_id.id if account_id else False,
                'desc':  str_to_desc,
                'product_id': product_id.id,
                'product_qty': product_qty,
                'date': str_date,
                })
            

            line_obj.create(vals)

class zarlaga_import_line(models.Model):
    _name = "zarlaga.import.line"
    _description = 'zarlaga import line'

    parent_id = fields.Many2one('zarlaga.import', 'Parent', ondelete='cascade')
    location_id = fields.Many2one('stock.location', 'Байрлал', domain=[('usage','=','internal')])
    to_location_id = fields.Many2one('stock.location', 'Хүрэх Байрлал', domain=[('usage','=','internal')])
    account_id = fields.Many2one('account.account', 'Зардал Гаргах Данс')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    product_id = fields.Many2one('product.product', 'Бараа', required=True)
    date = fields.Date('Огноо')
    desc = fields.Char('Тайлбар')
    product_qty = fields.Float('Тоо хэмжээ', required=True)
    stock_move_id = fields.Many2one('stock.move', 'Хөдөлгөөн', readonly=True)
    
    
