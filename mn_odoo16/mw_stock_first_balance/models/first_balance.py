# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from io import BytesIO
import base64
from tempfile import NamedTemporaryFile
import os,xlrd
from odoo.exceptions import UserError,Warning
from odoo.tools import float_is_zero

import logging
_logger = logging.getLogger(__name__)

# 1 dotood code
# 2 product code
# 3 hooson baranii ner
# 4 location name
# 5 too hemjee
# 6 technic
# 7 price_unit
# 8 serial lot

class first_balance(models.Model):
    _name = "first.balance"
    _description = 'first balance'

    name = fields.Char('Нэр')
    state = fields.Selection([('draft','Draft'),('price_unit','Нэгж өртөг оруулсан'),('done','Үлдэгдэл оуулсан')], 'State', default='draft')
    date = fields.Date('Огноо')
    import_data = fields.Binary('Импортлох эксел', copy=False)
    result = fields.Text('Үр дүн', readonly=True)
    line_ids = fields.One2many('first.balance.line', 'parent_id', 'Мөрүүд')
    total_amount = fields.Float('Нийт өртөг', compute='_compute_all', store=True)
    total_qty = fields.Float('Нийт тоо хэмжээ', compute='_compute_all', store=True)
    is_technic = fields.Boolean('Техниктэй эсэх', default=False)

    type = fields.Selection([('default_code','Дотоод кодоор'), ('barcode','Баркодоор')], 'Бараа Импортлох төрөл', default='default_code')

    count_move = fields.Integer('Хөдөлгөөний тоо', compute='compute_count_move')
    
    desc = fields.Text('Template', default="""# 1 dotood code
# 2 baraanii ner hooson bj bolno
# 3 location name
# 4 too hemjee
# 5 technic hooson bj bolno
# 6 price_unit
# 7 serial lot hooson bj bolno
# 8 serial date hooson bj bolno
# 9 partner hooson baij bolno """, readonly=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)

    is_picking = fields.Boolean('Шууд агуулахын гүйлгээ', default=True)

    def update_date(self):
        for item in self.line_ids.filtered(lambda r: r.stock_move_id):
            # stock_move_id = item.inventory_id.move_ids[0]
            stock_move_id = item.stock_move_id
            # print 'stock_move_id.date',stock_move_id.date
            # print '---',stock_move_id.date[:10]

            check_date = str(stock_move_id.date)[:10]
            time_date = str(stock_move_id.date)[10:20]
            time_date = ' 08:00:00'
            time_date = ' %s:%s:%s'%(str(datetime.now().hour).zfill(2),str(datetime.now().minute).zfill(2),str(datetime.now().second).zfill(2))
            # print time_date
            # # if check_date!=self.date:
            # print '-----',check_date
            set_date = str(self.date)+time_date
            print ('stock_move_id.date',stock_move_id.date)
            print ('set_date',set_date)
            stock_move_id.date = set_date
            stock_move_id.date_deadline = set_date
            print ('stock_move_id.date',stock_move_id.date)
            if item.inventory_id:
                item.inventory_id.date = set_date
            move_line_ids = self.env['stock.move.line'].search([('move_id','=',stock_move_id.id)])
            if move_line_ids:
                move_line_ids.write({'date':set_date})

            if stock_move_id.picking_id:
                stock_move_id.picking_id.scheduled_date = set_date
                stock_move_id.picking_id.date_done = set_date

            move_id = self.env['account.move'].search([('stock_move_id','=',stock_move_id.id)], limit=1)
            if move_id:
                query = """
                UPDATE account_move set date='%s' where id=%s
                """%(self.date,move_id.id)

                self._cr.execute(query)
                query = """
                UPDATE account_move_line set date='%s' where move_id=%s
                """%(self.date,move_id.id)
                self._cr.execute(query)

    def update_lot_serial(self):
        for item in self.line_ids.filtered(lambda r: r.ser_and_lot):
            if item.product_id.tracking=='none':
                item.product_id.tracking = 'lot'

    def update_lot_serial_date(self):
        for item in self.line_ids.filtered(lambda r: r.lot_id):
            if not item.ser_end_date:
                raise UserError('%s baraanii duusgah ognoo alga'%(item.product_id.display_name))
            item.lot_id.life_date = str(item.ser_end_date)+' 08:00:00'
            item.lot_id.alert_date = str(item.ser_end_date)+' 08:00:00'
            
    def view_stock_move(self):
        picking_obj = self.env['stock.picking']
        context = dict(self._context)
        context['create'] = False
        tree_view_id = self.env.ref('stock.view_move_tree').id
        form_view_id = self.env.ref('stock.view_move_form').id
        action = {
            'name': self.name,
            'view_mode': 'tree',
            'res_model': 'stock.move',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_id': tree_view_id,
            'domain': [('id', 'in', self.line_ids.mapped('stock_move_id').ids)],
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'current'
        }
        return action
    

    def view_line_edit_move(self):
        context = dict(self._context)
        context['create']= False
        tree_view_id = self.env.ref('mw_stock_first_balance.first_balance_line_tree_view').id
        if self.state=='done':
            context['delete']= False
            # context['edit']= False
        if self.state=='price_unit':
            context['delete']= False
        action = {
                'name': self.name,
                'view_mode': 'tree',
                'res_model': 'first.balance.line',
                'views': [(tree_view_id, 'tree')],
                'view_id': tree_view_id,
                'domain': [('parent_id','=',self.id)],
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'current'
            }
        return action

    @api.depends('line_ids')
    def compute_count_move(self):
        for item in self:
            item.count_move = len(item.line_ids.mapped('stock_move_id'))

    def action_not_create_account_move(self):
        query = """
        select fl.id from first_balance_line fl
left join stock_move sm on (fl.stock_move_id=sm.id) 
left join account_move am on (am.stock_move_id=fl.stock_move_id)
left join product_product pp on (pp.id=fl.product_id)
left join product_template pt on (pt.id=pp.product_tmpl_id)
where fl.parent_id=%s and fl.stock_move_id is not null and am.id is null
        """%(self.id)
        self._cr.execute(query)
        res = self._cr.dictfetchall()
        for item in res:
            line_id = self.env['first.balance.line'].browse(item['id'])
            stock_valuation_layers = line_id.stock_move_id.stock_valuation_layer_ids
            for svl in stock_valuation_layers:
                if not svl.product_id.valuation == 'real_time' or svl.account_move_id:
                    continue
                # svl.stock_move_id._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)
                svl.stock_move_id.create_account_move_hand() # үүсэхгүй байхаар нь сольж үзэв                
            # ._account_entry_move()

    def create_inventory(self, env_product, env_location_id, env_lot_id, product_qty):
        Inventory = self.env['stock.inventory']
        InventoryLine = self.env['stock.inventory.line']
        inventory_id = Inventory.create({
            'name': _('FIRST BALANCE: %s') % (env_product.display_name),
            'product_ids': [env_product.id],
            'location_ids': [env_location_id.id],
            'company_id': self.company_id.id,
            'state': 'confirm',
        })
        InventoryLine.create({
            'prod_lot_id': env_lot_id.id if env_lot_id else False,
            'location_id': env_location_id.id,
            'product_id': env_product.id,
            'product_uom_id': env_product.uom_id.id,
            'product_qty': product_qty,
            'company_id': self.company_id.id,
            'inventory_id': inventory_id.id,
        })
        inventory_id.action_validate()

    def create_move(self, line):
        """Create move."""
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
#             for line in order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding)):
#         line_ids = self.env['first.balance.line'].search([('parent_id','=',self.id),('inventory_id','=',False)], limit=500)
#         i = len(line_ids)
#         _logger.info(u'Uldsen uldegdel batlahе 222----- %s '%(i))
        moves = Move
        inv_location = self.env['stock.location'].search([('usage', '=', 'supplier'), ('company_id', '=', self.company_id.id)], limit=1)
        if not inv_location:
            inv_location = self.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
        if line:
            if not line.stock_move_id:
                lot_id = False
                if line.product_id.tracking in ['lot', 'serial']:
                    if not line.ser_and_lot:
                        raise UserError(u'%s Baraa lotgui bna' % (line.product_id.name))
                    lot_id = self.env['stock.production.lot'].search([
                        ('name', '=', line.ser_and_lot),
                        ('product_id', '=', line.product_id.id),
                        ('company_id', '=', self.company_id.id)
                    ], limit=1)
                    if not lot_id:
                        lot_id = self.env['stock.production.lot'].create({
                            'name': line.ser_and_lot,
                            'product_id': line.product_id.id,
                            'company_id': self.company_id.id,
                        })
                    product_qty = line.product_qty
                    line.lot_id = lot_id.id
                    lot_id = lot_id.id

    #         for line in line_ids:
                price_unit=line.price_unit_average>0 and line.price_unit_average or line.price_unit
                print ('price_unit:::::: ',price_unit)
                moves |= Move.create({
                    'name': line.product_id.name+' '+self.name,
                    'product_uom': line.product_id.uom_id.id,
                    #                     'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                    #                     'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': abs(line.product_qty),
                    'state': 'confirmed',
                    'partner_id': line.partner_id and line.partner_id.id or False,
                    'price_unit': price_unit,
                    'location_id': inv_location.id,
                    'location_dest_id': line.location_id.id,
                    'move_line_ids': [(0, 0, {
                        'product_id': line.product_id.id,
                        'lot_id': lot_id,
                        'reserved_uom_qty': 0,  # bypass reservation here
                        'product_uom_id': line.product_id.uom_id.id,
                        'qty_done': abs(line.product_qty),
                        #                         'package_id': out and self.package_id.id or False,
                        #                         'result_package_id': (not out) and self.package_id.id or False,
                        'location_id': inv_location.id,
                        'location_dest_id': line.location_id.id,
                        # 'owner_id': line.partner_id and line.partner_id.id or False,
                    })]
                })
                moves.filtered(lambda move: move.state != 'done')._action_done()
                line.stock_move_id = moves.id
        return True

    def action_done(self):

        Inventory = self.env['stock.inventory']
        stock_move_obj = self.env['stock.move']
        line_ids = self.env['first.balance.line'].search([('parent_id', '=', self.id), ('inventory_id', '=', False)], limit=1000)
        if self.is_picking:
            line_ids = self.env['first.balance.line'].search([('parent_id', '=', self.id), ('stock_move_id', '=', False)], limit=1000)
        i = len(line_ids)
        _logger.info(u'Uldsen uldegdel batlahе ----- %s ' % (i))
        zero_cost = line_ids.filtered(lambda r: r.product_id.type=='product' and r.product_id.cost_method in ['standard','average'] and r.product_id.standard_price==0).mapped('product_id')
        if zero_cost:
            raise UserError(u'Zero cost %s '%(', '.join(zero_cost.mapped('display_name'))))
        
        lotgui_baraanuud = line_ids.filtered(lambda r: r.product_id.tracking in ['lot', 'serial'] and not r.ser_and_lot)
        if lotgui_baraanuud:
            raise UserError(u'%s Baraa lotgui bna' % (', '.join(lotgui_baraanuud.mapped('name'))))

        for item in line_ids:
            lot_id = False
            _logger.info(u'Uldsen uldegdel batlah %s ---- ID %s product_name  %s' % (i, item.id, item.product_id.display_name))
            i -= 1
            if self.is_picking:
                self.create_move(item)
                continue
            else:
                if not item.inventory_id:
                    if item.product_qty > 0:

                        if item.product_id.tracking in ['lot', 'serial']:
                            if not item.ser_and_lot:
                                raise UserError(u'%s Baraa lotgui bna' % (item.product_id.name))
                            lot_id = self.env['stock.lot'].search([
                                ('name', '=', item.ser_and_lot),
                                ('product_id', '=', item.product_id.id),
                                ('company_id', '=', self.company_id.id)
                            ], limit=1)
                            if not lot_id:
                                lot_id = self.env['stock.lot'].create({
                                    'name': item.ser_and_lot,
                                    'product_id': item.product_id.id,
                                    'company_id': self.company_id.id,
                                })
                            product_qty = item.product_qty
                            item.lot_id = lot_id.id
                        else:
                            product_qty = sum(line_ids.filtered(lambda r: r.product_id.id == item.product_id.id and r.location_id.id == item.location_id.id).mapped('product_qty'))

                        # change_id = change_obj.with_context(active_id=item.product_id.id, active_model='product.product').create({
                        #     'product_tmpl_id': item.product_id.product_tmpl_id.id,
                        #     'location_id': item.location_id.id,
                        #     'new_quantity': product_qty,
                        #     'lot_id': lot_id.id if lot_id else False
                        #     })
                        self.create_inventory(item.product_id, item.location_id, lot_id, product_qty)
                        # change_id.change_product_qty()

                        query = 'SELECT max(id) from stock_inventory where create_uid=%s' % (self.env.user.id)
                        self._cr.execute(query)
                        p_max_id = self._cr.fetchone()[0]

                        inventory_id = Inventory.browse(p_max_id)
                        if item.inventory_id:
                            raise UserError('Үлдэгдэл орсон байна')
                        if item.product_id.tracking in ['lot', 'serial']:
                            item.inventory_id = p_max_id
                        else:
                            for item_id in line_ids.filtered(lambda r: r.product_id.id == item.product_id.id and r.location_id.id == item.location_id.id and not r.inventory_id):
                                item_id.inventory_id = p_max_id

                        stock_move_id = False
                        if inventory_id.move_ids:
                            stock_move_id = inventory_id.move_ids[0]

                        if self.is_technic:
                            if stock_move_id:
                                stock_move_id.technic_id = item.technic_id.id
                        if stock_move_id:
                            if item.product_id.tracking in ['lot', 'serial']:
                                item.stock_move_id = stock_move_id.id
                            else:
                                for item_id in line_ids.filtered(lambda r: r.product_id.id == item.product_id.id and r.location_id.id == item.location_id.id and not r.stock_move_id):
                                    item_id.stock_move_id = stock_move_id.id

        if self.is_picking and not self.env['first.balance.line'].search([('parent_id', '=', self.id), ('stock_move_id', '=', False)]):
            self.state = 'done'
        elif not self.env['first.balance.line'].search([('parent_id', '=', self.id), ('inventory_id', '=', False)]):
            self.state = 'done'

    def action_price_unit(self):
        not_found_product = []
        ll = len(self.line_ids)
        for item in self.line_ids:
            _logger.info(u'negj urtug batlah uldsen %s', ll)
            ll -= 1
            if item.price_unit_average>0:
                item.product_id.standard_price = item.price_unit_average
                if self.line_ids.filtered(lambda r: r.product_id.id == item.product_id.id and r.id != item.id and item.price_unit_average != r.price_unit_average):
                    not_found_product.append('[' + item.product_id.default_code + '] ' + item.product_id.name)
            else:
                item.product_id.standard_price = item.price_unit
                if self.line_ids.filtered(lambda r: r.product_id.id == item.product_id.id and r.id != item.id and item.price_unit != r.price_unit):
                    not_found_product.append('[' + item.product_id.default_code + '] ' + item.product_id.name)
                
        if not_found_product != []:
            not_found_product = set(not_found_product)
            raise UserError('Baraanuudiin negj urtug uur bna %s ' % (', '.join(not_found_product)))

        self.state = 'price_unit'


    def action_price_unit_average(self):
        not_found_product = []
        ll = len(self.line_ids)
        data={}
        for item in self.line_ids:
            _logger.info(u'negj urtug batlah uldsen %s', ll)
            ll -= 1
            if data.get(item.product_id,False):
                data[item.product_id]['subtotal']+=item.price_unit*item.product_qty
                data[item.product_id]['product_qty']+=item.product_qty
            else:
                data[item.product_id] = {'subtotal':item.price_unit*item.product_qty,
                                         'product_qty':item.product_qty
                                         }
        for item in self.line_ids:
            if data.get(item.product_id,False) and data[item.product_id]['product_qty']>0:
                item.price_unit_average = data[item.product_id]['subtotal']/data[item.product_id]['product_qty']
                


    def action_draft(self):
        self.state = 'draft'


    @api.depends('line_ids.subtotal')
    def _compute_all(self):
        for item in self:
            item.total_amount = sum(item.line_ids.mapped('subtotal'))
            item.total_qty = sum(item.line_ids.mapped('product_qty'))

    def remove_line(self):
        self.line_ids.unlink()

    def action_import(self):
        if not self.import_data:
            raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')

        fileobj = NamedTemporaryFile('w+b')
        fileobj.write(base64.decodebytes(self.import_data))

        if not os.path.isfile(fileobj.name):
            raise UserError(u'Алдаа Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        book = xlrd.open_workbook(fileobj.name)

        try:
            sheet = book.sheet_by_index(0)
        except Exception:
            raise UserError(u'Алдаа Sheet -ны дугаар буруу байна.')
        nrows = sheet.nrows

        product_obj = self.env['product.product']
        technic_obj = False
        if self.is_technic:
            technic_obj = self.env['technic.equipment']
        attr_obj = self.env['product.attribute.value']
        categ_obj = self.env['product.category']
        tmp_obj = self.env['product.template']
        line_obj = self.env['first.balance.line']
        location_obj = self.env['stock.location']

        not_found_def_code = []
        not_found_tech = []
        not_found_location = []
        not_found_partner = []
        rowi = 1
        for item in range(rowi, nrows):
            row = sheet.row(item)
            _logger.info('shalgalt uldsen %s' % (nrows - item))
            str_location_name = row[3].value
            str_product_code = row[1].value
            str_technic_name = row[5].value if row[5] and row[5].value else ''
            partner_name = row[9].value if row[9] and row[9].value else ''

            if type(str_product_code) in [float]:
                default_code = str(str_product_code).strip().split('.')[0]
            elif type(str_product_code) in [int]:
                default_code = str(str_product_code).strip()
            else:
                default_code = str_product_code.strip()

            if self.type == 'barcode':
                product_id = product_obj.search([('barcode', '=', default_code)], limit=1)
            else:
                product_id = product_obj.search([('default_code', '=', default_code)], limit=1)
            if not product_id and default_code:
                not_found_def_code.append(default_code)

            if partner_name:
                partner = self.env['res.partner'].search([('name', '=', partner_name)], limit=1)
                if partner:
                    partner_id = partner.id
                else:
                    not_found_partner.append(partner_name)

            if self.is_technic:
                tech_name = str_technic_name
                if tech_name:
                    if type(tech_name) in [float]:
                        technic_name = str(tech_name).split('.')[0]
                        technic_id = technic_obj.search([('park_number', '=', technic_name)], limit=1)
                        if not technic_id:
                            not_found_tech.append(technic_name)
                    else:
                        technic_name = tech_name.strip()
                        technic_id = technic_obj.search([('park_number', '=', technic_name)], limit=1)
                        if not technic_id:
                            not_found_tech.append(technic_name)

            loc_name = str_location_name
            if loc_name:
                if type(loc_name) in [float]:
                    location_name = str(loc_name).split('.')[0]
                    location_id = location_obj.search([('name', '=', location_name), ('usage', '=', 'internal')], limit=1)
                    if not location_id:
                        not_found_location.append(location_name)
                else:
                    location_name = loc_name.strip()
                    location_id = location_obj.search([('name', '=', location_name), ('usage', '=', 'internal')], limit=1)
                    if not location_id:
                        not_found_location.append(location_name)

        if self.is_technic:
            if not_found_def_code != [] or not_found_tech != [] or not_found_location != []:
                not_found_def_code = list(set(not_found_def_code))
                not_found_tech = list(set(not_found_tech))
                not_found_location = list(set(not_found_location))
                raise UserError(u'Олдоогүй Бараанууд \n %s \nОлдоогүй техникүүд \n %s \nОлдоогүй Байрлалууд \n %s' % (', '.join(not_found_def_code), ', '.join(not_found_tech), ', '.join(not_found_location)))
        else:
            if not_found_def_code != [] or not_found_location != [] or not_found_partner != []:
                not_found_def_code = list(set(not_found_def_code))
                not_found_location = list(set(not_found_location))
                not_found_partner = list(set(not_found_partner))
                raise UserError(u'Олдоогүй Бараанууд \n %s \nОлдоогүй Байрлалууд \n %s\nОлдоогүй Харилцагч \n %s' % (', '.join(not_found_def_code), ', '.join(not_found_location), ', '.join(not_found_partner)))

        rowi = 1
        # print blblb
        for item in range(rowi, nrows):
            _logger.info('uusgelt uldsen %s' % (nrows - item))
            row = sheet.row(item)
            str_product_code = row[1].value
            str_location_name = row[3].value
            str_product_qty = row[4].value
            str_technic_name = row[5].value
            str_price_unit = row[6].value
            str_serial_lot = row[7].value if row[7].value else ''
            str_serial_lot_date = row[8].value if row[8].value else False
            partner_name = row[9].value

            if type(str_product_code) in [float]:
                default_code = str(str_product_code).strip().split('.')[0]
            elif type(str_product_code) in [int]:
                default_code = str(str_product_code).strip()
            else:
                default_code = str_product_code.strip()

            if self.type == 'barcode':
                product_id = product_obj.search([('barcode', '=', default_code)], limit=1)
            else:
                product_id = product_obj.search([('default_code', '=', default_code)], limit=1)
            partner = self.env['res.partner'].search([('name', '=', partner_name)], limit=1)
            partner_id = False
            if partner:
                partner_id = partner.id

            vals = {}
            if self.is_technic:
                tech_name = str_technic_name
                technic_id = False
                if tech_name:
                    if type(tech_name) in [float]:
                        technic_name = str(tech_name).split('.')[0]
                        technic_id = technic_obj.search([('park_number', '=', technic_name)], limit=1)
                    else:
                        technic_name = tech_name.strip()
                        technic_id = technic_obj.search([('park_number', '=', technic_name)], limit=1)
                vals['technic_id'] = technic_id.id if technic_id else False
            loc_name = str_location_name
            location_id = False
            if loc_name:
                if type(loc_name) in [float]:
                    location_name = str(loc_name).split('.')[0]
                    location_id = location_obj.search([('name', '=', location_name), ('usage', '=', 'internal')], limit=1)
                else:
                    location_name = loc_name.strip()
                    location_id = location_obj.search([('name', '=', location_name), ('usage', '=', 'internal')], limit=1)

            price_unit = str_price_unit
            product_qty = str_product_qty
            serial_lot = str_serial_lot
            serial_lot_date = str_serial_lot_date
            # print('partner_id', partner_id)
            vals.update({
                'parent_id': self.id,
                'location_id': location_id.id if location_id else False,
                'product_id': product_id.id,
                'price_unit': price_unit,
                'product_qty': product_qty,
                'ser_and_lot': serial_lot,
                'ser_end_date': serial_lot_date,
                'partner_id': partner_id if partner_id else False
            })

            line_obj.create(vals)


class first_balance_line(models.Model):
    _name = "first.balance.line"
    _description = 'first balance line'

    parent_id = fields.Many2one('first.balance', 'Parent', ondelete='cascade')
    location_id = fields.Many2one('stock.location', 'Байрлал', domain=[('usage','=','internal')])
    product_id = fields.Many2one('product.product', 'Бараа', required=True)
    price_unit = fields.Float('Нэгж өртөг', required=True)
    price_unit_average = fields.Float('Нэгж өртөг /дундаж/',)
    product_qty = fields.Float('Тоо хэмжээ', required=True, digits='Product Unit of Measure')
    stock_move_id = fields.Many2one(comodel_name='stock.move', string=u'Хөдөлгөөн', readonly=True)
    inventory_id = fields.Many2one(comodel_name='stock.inventory', string=u'Тооллого', readonly=True)
    # technic_id = fields.Many2one('technic.equipment', 'Техник')
    subtotal = fields.Float('Дэд дүн', compute='_compute_all', store=True)
    ser_and_lot = fields.Char('Сериал лот')
    ser_end_date = fields.Date('Сериал дуусах огноо')
    lot_id = fields.Many2one('stock.lot','Үүссэн Сериал лот', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner')

    @api.depends('price_unit', 'product_qty')
    def _compute_all(self):
        for item in self:
            item.subtotal = item.price_unit * item.product_qty
