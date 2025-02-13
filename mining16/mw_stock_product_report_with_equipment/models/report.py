# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
from odoo.addons.mw_technic_equipment.models.technic_equipment import TECHNIC_TYPE
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE

# class StockReportDetail(models.Model):
#     _inherit = "stock.report.detail"

#     equipment_id = fields.Many2one('technic.equipment', 'Техник', readonly=True, groups="mw_technic_equipment.group_technic_module_user")
#     technic_type = fields.Selection(TECHNIC_TYPE, readonly=True, string=u'Техникийн төрөл', store=True, groups="mw_technic_equipment.group_technic_module_user")
#     equipment_setting_id = fields.Many2one('technic.equipment.setting', string=u'Техникийн тохиргоо', readonly=True, groups="mw_technic_equipment.group_technic_module_user")
#     owner_type = fields.Selection(OWNER_TYPE, string=u'Техникийн эзэмшил',readonly=True, store=True, groups="mw_technic_equipment.group_technic_module_user")
#     vin_number = fields.Char(string=u'Техникийн сериал', readonly=True, store=True, groups="mw_technic_equipment.group_technic_module_user")
#     t_partner_id = fields.Many2one('res.partner', string=u'Техникийн эзэмшигч', readonly=True, groups="mw_technic_equipment.group_technic_module_user")

#     def _select(self):
#         select_str = super(StockReportDetail, self)._select()
#         select_str += """
#             ,sm.technic_id
#             ,tech.technic_type
#             ,tech.technic_setting_id
#             ,tech.owner_type
#             ,tech.vin_number
#             ,tech.partner_id as t_partner_id
#         """
#         return select_str

#     def _select2(self):
#         select_str = super(StockReportDetail, self)._select2()
#         select_str += """
#             ,sm.technic_id
#             ,tech.technic_type
#             ,tech.technic_setting_id
#             ,tech.owner_type
#             ,tech.vin_number
#             ,tech.partner_id as t_partner_id
#         """
#         return select_str

#     def _select3(self):
#         select_str = super(StockReportDetail, self)._select3()
#         select_str += """
#             ,sm.technic_id
#             ,tech.technic_type
#             ,tech.technic_setting_id
#             ,tech.owner_type
#             ,tech.vin_number
#             ,tech.partner_id as t_partner_id
#         """
#         return select_str

#     def _select4(self):
#         select_str = super(StockReportDetail, self)._select4()
#         select_str += """
#             ,sm.technic_id
#             ,tech.technic_type
#             ,tech.technic_setting_id
#             ,tech.owner_type
#             ,tech.vin_number
#             ,tech.partner_id as t_partner_id
#         """
#         return select_str

#     def _select_main(self):
#         select_str = super(StockReportDetail, self)._select_main()
#         select_str += """
#             ,technic_id
#             ,technic_type
#             ,technic_setting_id
#             ,owner_type
#             ,vin_number
#             ,t_partner_id
#         """
#         return select_str

#     def _join(self):
#         select_str = super(StockReportDetail, self)._join()
#         select_str += """
#             LEFT JOIN technic_equipment tech ON (sm.technic_id=tech.id)
#         """
#         return select_str

#     def _join2(self):
#         select_str = super(StockReportDetail, self)._join2()
#         select_str += """
#             LEFT JOIN technic_equipment tech ON (sm.technic_id=tech.id)
#         """
#         return select_str

#     def _join3(self):
#         select_str = super(StockReportDetail, self)._join3()
#         select_str += """
#             LEFT JOIN technic_equipment tech ON (sm.technic_id=tech.id)
#         """
#         return select_str

#     def _join4(self):
#         select_str = super(StockReportDetail, self)._join4()
#         select_str += """
#             LEFT JOIN technic_equipment tech ON (sm.technic_id=tech.id)
#         """
#         return select_str

# class ProductBothIncomeExpenseReport(models.Model):
#     _inherit = "product.both.income.expense.report"

#     technic_id = fields.Many2one('technic.equipment', 'Техник', readonly=True, groups="mw_technic_equipment.group_technic_module_user")
#     technic_type = fields.Selection(TECHNIC_TYPE, readonly=True, string=u'Техникийн төрөл', store=True, groups="mw_technic_equipment.group_technic_module_user")
#     technic_setting_id = fields.Many2one('technic.equipment.setting', string=u'Техникийн тохиргоо', readonly=True, groups="mw_technic_equipment.group_technic_module_user")
#     owner_type = fields.Selection(OWNER_TYPE, string=u'Техникийн эзэмшил',readonly=True, store=True, groups="mw_technic_equipment.group_technic_module_user")
#     vin_number = fields.Char(string=u'Техникийн сериал', readonly=True, store=True, groups="mw_technic_equipment.group_technic_module_user")
#     t_partner_id = fields.Many2one('res.partner', string=u'Техникийн эзэмшигч', readonly=True, groups="mw_technic_equipment.group_technic_module_user")

#     def _select(self):
#         select_str = super(ProductBothIncomeExpenseReport, self)._select()
#         select_str += """
#             ,sm.technic_id
#             ,tech.technic_type
#             ,tech.technic_setting_id
#             ,tech.owner_type
#             ,tech.vin_number
#             ,tech.partner_id as t_partner_id
#         """
#         return select_str

#     def _select2(self):
#         select_str = super(ProductBothIncomeExpenseReport, self)._select2()
#         select_str += """
#             ,sm.technic_id
#             ,tech.technic_type
#             ,tech.technic_setting_id
#             ,tech.owner_type
#             ,tech.vin_number
#             ,tech.partner_id as t_partner_id
#         """
#         return select_str

#     def _join(self):
#         select_str = super(ProductBothIncomeExpenseReport, self)._join()
#         select_str += """
#             LEFT JOIN technic_equipment tech ON (sm.technic_id=tech.id)
#         """
#         return select_str

#     def _join2(self):
#         select_str = super(ProductBothIncomeExpenseReport, self)._join2()
#         select_str += """
#             LEFT JOIN technic_equipment tech ON (sm.technic_id=tech.id)
#         """
#         return select_str

# class ProductIncomeExpenseReport(models.Model):
#     _inherit = "product.income.expense.report"

#     technic_id = fields.Many2one('technic.equipment', 'Техник', readonly=True, groups="mw_technic_equipment.group_technic_module_user")
#     technic_type = fields.Selection(TECHNIC_TYPE, readonly=True, string=u'Техникийн төрөл', store=True, groups="mw_technic_equipment.group_technic_module_user")
#     technic_setting_id = fields.Many2one('technic.equipment.setting', string=u'Техникийн тохиргоо', readonly=True, groups="mw_technic_equipment.group_technic_module_user")
#     owner_type = fields.Selection(OWNER_TYPE, string=u'Техникийн эзэмшил',readonly=True, store=True, groups="mw_technic_equipment.group_technic_module_user")
#     vin_number = fields.Char(string=u'Техникийн сериал', readonly=True, store=True, groups="mw_technic_equipment.group_technic_module_user")
#     t_partner_id = fields.Many2one('res.partner', string=u'Техникийн эзэмшигч', readonly=True, groups="mw_technic_equipment.group_technic_module_user")

#     def _select(self):
#         select_str = super(ProductIncomeExpenseReport, self)._select()
#         select_str += """
#             ,sm.technic_id
#             ,tech.technic_type
#             ,tech.technic_setting_id
#             ,tech.owner_type
#             ,tech.vin_number
#             ,tech.partner_id as t_partner_id
#         """
#         return select_str

#     def _join(self):
#         select_str = super(ProductIncomeExpenseReport, self)._join()
#         select_str += """
#             LEFT JOIN technic_equipment tech ON (sm.technic_id=tech.id)
#         """
#         return select_str

# class ProductBalancePivotReport(models.Model):
#     _inherit = "product.balance.pivot.report"

#     technic_id = fields.Many2one('technic.equipment', 'Техник', readonly=True, groups="mw_technic_equipment.group_technic_module_user")
#     technic_type = fields.Selection(TECHNIC_TYPE, readonly=True, string=u'Техникийн төрөл', store=True, groups="mw_technic_equipment.group_technic_module_user")
#     technic_setting_id = fields.Many2one('technic.equipment.setting', string=u'Техникийн тохиргоо', readonly=True, groups="mw_technic_equipment.group_technic_module_user")
#     owner_type = fields.Selection(OWNER_TYPE, string=u'Техникийн эзэмшил',readonly=True, store=True, groups="mw_technic_equipment.group_technic_module_user")
#     vin_number = fields.Char(string=u'Техникийн сериал', readonly=True, store=True, groups="mw_technic_equipment.group_technic_module_user")
#     t_partner_id = fields.Many2one('res.partner', string=u'Техникийн эзэмшигч', readonly=True, groups="mw_technic_equipment.group_technic_module_user")

#     def _select(self):
#         select_str = super(ProductBalancePivotReport, self)._select()
#         select_str += """
#             ,sm.technic_id
#             ,tech.technic_type
#             ,tech.technic_setting_id
#             ,tech.owner_type
#             ,tech.vin_number
#             ,tech.partner_id as t_partner_id
#         """
#         return select_str

#     def _select2(self):
#         select_str = super(ProductBalancePivotReport, self)._select2()
#         select_str += """
#             ,sm.technic_id
#             ,tech.technic_type
#             ,tech.technic_setting_id
#             ,tech.owner_type
#             ,tech.vin_number
#             ,tech.partner_id as t_partner_id
#         """
#         return select_str

#     def _join(self):
#         select_str = super(ProductBalancePivotReport, self)._join()
#         select_str += """
#             LEFT JOIN technic_equipment tech ON (sm.technic_id=tech.id)
#         """
#         return select_str

#     def _join2(self):
#         select_str = super(ProductBalancePivotReport, self)._join2()
#         select_str += """
#             LEFT JOIN technic_equipment tech ON (sm.technic_id=tech.id)
#         """
#         return select_str

class factoryEquipmentInherit(models.Model):
    _inherit = 'factory.equipment'

    stock_move_ids = fields.One2many('stock.move', 'equipment_id', readonly=True, string=u'Хөдөлгөөн', domain=[('state','=','done')])
    account_move_line_ids = fields.One2many('account.move.line', 'equipment_id', readonly=True, string=u'Санхүү Хөдөлгөөн')
    all_cost = fields.Float(string='Нийт зардал', compute='_compute_all_cost', groups="mw_stock_account.group_stock_view_cost")
    all_cost_am = fields.Float(string='Нийт зардал AM', compute='_compute_all_cost_am', groups="mw_stock_account.group_stock_view_cost")

    @api.depends('stock_move_ids')
    def _compute_all_cost(self):
        for item in self:
            item.all_cost = sum([-abs(x.price_unit*x.product_qty) if x.location_id.usage=='internal' else abs(x.price_unit*x.product_qty) for x in item.sudo().stock_move_ids.filtered(lambda r:r.state=='done')])

    @api.depends('account_move_line_ids')
    def _compute_all_cost_am(self):
        for item in self:
            item.all_cost_am = sum(item.sudo().account_move_line_ids.filtered(lambda r:r.move_id.state=='posted' and r.account_id.account_type=='expense').mapped('balance'))

    def see_stock_move(self):
        action = self.env.ref('stock_account.stock_valuation_layer_action').read()[0]
        action['domain'] = [('stock_move_id','in', self.stock_move_ids.ids)]
        return action

    def see_account_move(self):
        action = self.env.ref('account.action_account_moves_all_a').read()[0]
        action['domain'] = [('id','in', self.account_move_line_ids.filtered(lambda r:r.move_id.state=='posted' and r.account_id.account_type=='expense').ids)]
        action['context'] = {'search_default_group_by_account':True}
        return action
    
    def see_parts(self):
        action = self.env.ref('mw_stock_product_report_with_equipment.equipment_stock_move_action').read()[0]
        action['domain'] = [('equipment_id','=', self.id)]
        return action