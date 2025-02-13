# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class StockReportDetail(models.Model):
    _inherit = "stock.report.detail"

    qty_product_uom_out = fields.Float(u'Тоо Барааны Нэгжээр Зарлага', readonly=True)
    qty_product_uom_in = fields.Float(u'Тоо Барааны Нэгжээр Орлого', readonly=True)
    qty_product_uom_first = fields.Float(u'Тоо Барааны Нэгжээр Эхний', readonly=True)
    qty_product_uom_last = fields.Float(u'Тоо Барааны Нэгжээр Үлдэгдэл', readonly=True)

    def _select(self):
        select_str = super(StockReportDetail, self)._select()
        select_str += """
            ,sml.qty_done / uu.factor * uom_product.factor as qty_product_uom_out
            ,0 as qty_product_uom_in
            ,0 as qty_product_uom_first
        """
        return select_str

    def _select2(self):
        select_str = super(StockReportDetail, self)._select2()
        select_str += """
            ,0 as qty_product_uom_out
            ,sml.qty_done / uu.factor * uom_product.factor as qty_product_uom_in
            ,0 as qty_product_uom_first
        """
        return select_str
    
    def _select3(self):
        select_str = super(StockReportDetail, self)._select3()
        select_str += """
            ,0 as qty_product_uom_out
            ,0 as qty_product_uom_in
            ,sml.qty_done / uu.factor * uom_product.factor as qty_product_uom_first
           
        """
        return select_str

    def _select4(self):
        select_str = super(StockReportDetail, self)._select4()
        select_str += """
            ,0 as qty_product_uom_out
            ,0 as qty_product_uom_in
            ,-sml.qty_done / uu.factor * uom_product.factor as qty_product_uom_first
            
        """
        return select_str

    def _join(self):
        select_str = super(StockReportDetail, self)._join()
        select_str += """
            LEFT JOIN uom_uom uom_product ON (uom_product.id=pt.uom_id)
        """
        return select_str

    def _join2(self):
        select_str = super(StockReportDetail, self)._join2()
        select_str += """
            LEFT JOIN uom_uom uom_product ON (uom_product.id=pt.uom_id)
        """
        return select_str
    
    def _join3(self):
        select_str = super(StockReportDetail, self)._join3()
        select_str += """
            LEFT JOIN uom_uom uom_product ON (uom_product.id=pt.uom_id)
        """
        return select_str
    def _join4(self):
        select_str = super(StockReportDetail, self)._join4()
        select_str += """
            LEFT JOIN uom_uom uom_product ON (uom_product.id=pt.uom_id)
        """
        return select_str

    def _select_main(self):
        select_str = super(StockReportDetail, self)._select_main()
        select_str += """
            ,qty_product_uom_out
            ,qty_product_uom_in
            ,qty_product_uom_first
            ,(qty_product_uom_first+qty_product_uom_in-qty_product_uom_out) as qty_product_uom_last
        """
        return select_str

class ProductBothIncomeExpenseReport(models.Model):
    _inherit = "product.both.income.expense.report"

    qty_product_uom_out = fields.Float(u'Тоо Барааны Нэгжээр Зарлага', readonly=True)
    qty_product_uom_in = fields.Float(u'Тоо Барааны Нэгжээр Орлого', readonly=True)
    
    def _select(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._select()
        select_str += """
            ,sml.qty_done / uu.factor * uom_product.factor as qty_product_uom_out
            ,0 as qty_product_uom_in
        """
        return select_str

    def _select2(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._select2()
        select_str += """
            ,0 as qty_product_uom_out
            ,sml.qty_done / uu.factor * uom_product.factor as qty_product_uom_in
        """
        return select_str

    def _join(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._join()
        select_str += """
            LEFT JOIN uom_uom uom_product ON (uom_product.id=pt.uom_id)
        """
        return select_str

    def _join2(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._join2()
        select_str += """
            LEFT JOIN uom_uom uom_product ON (uom_product.id=pt.uom_id)
        """
        return select_str

class ProductIncomeExpenseReport(models.Model):
    _inherit = "product.income.expense.report"

    qty_product_uom = fields.Float(u'Тоо Барааны Нэгжээр', readonly=True)
    
    def _select(self):
        select_str = super(ProductIncomeExpenseReport, self)._select()
        select_str += """
            ,sml.qty_done / uu.factor * uom_product.factor as qty_product_uom
        """
        return select_str

    def _join(self):
        select_str = super(ProductIncomeExpenseReport, self)._join()
        select_str += """
            LEFT JOIN uom_uom uom_product ON (uom_product.id=pt.uom_id)
        """
        return select_str

class ProductBalancePivotReport(models.Model):
    _inherit = "product.balance.pivot.report"

    qty_product_uom = fields.Float(u'Тоо Барааны Нэгжээр', readonly=True)
    
    def _select(self):
        select_str = super(ProductBalancePivotReport, self)._select()
        select_str += """
            ,sml.qty_done / uu.factor * uom_product.factor as qty_product_uom
        """
        return select_str

    def _select2(self):
        select_str = super(ProductBalancePivotReport, self)._select2()
        select_str += """
            ,-sml.qty_done / uu.factor * uom_product.factor as qty_product_uom
        """
        return select_str

    def _join(self):
        select_str = super(ProductBalancePivotReport, self)._join()
        select_str += """
            LEFT JOIN uom_uom uom_product ON (uom_product.id=pt.uom_id)
        """
        return select_str

    def _join2(self):
        select_str = super(ProductBalancePivotReport, self)._join2()
        select_str += """
            LEFT JOIN uom_uom uom_product ON (uom_product.id=pt.uom_id)
        """
        return select_str
