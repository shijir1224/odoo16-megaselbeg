odoo.define('point_of_sale.mw_pos', function (require) {
    "use strict";
    var models = require('point_of_sale.models');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var utils = require('web.utils');

    var _t = core._t;
    var round_pr = utils.round_precision;

    models.load_fields("product.product", "tax_type");
    models.load_fields("res.partner", ["company_type", "nuat_no"]);
    models.load_fields("account.tax", "ebarimt_tax_type_id");

    var _superOrder = models.Order;
    models.Order = models.Order.extend({
        initialize: function(attributes, options) {
            this.bill_type = '1';
            return _superOrder.prototype.initialize.apply(this,arguments);
        },

        export_as_JSON: function() {
            var json = _superOrder.prototype.export_as_JSON.apply(this,arguments);
            if (!this.bill_type) { this.bill_type = '1'; }
            json.bill_type = this.bill_type;
            if (this.bill_type === '0'){
                json.amount_total = this.get_total_without_tax();
                json.amount_tax = 0;
            }
            json.customerReg = this.customerReg;
            json.customerName = this.customerName;
            return json;
        },

        export_for_printing: function() {
            var receipt = _superOrder.prototype.export_for_printing.apply(this,arguments);
            if (!this.bill_type) { this.bill_type = '1'; }
            receipt.bill_type = this.bill_type;
            receipt.config_name = this.pos.config.name;
            receipt.customer_reg = this.customerReg;
            receipt.customer_name = this.customerName;
            if (this.bill_type === '0'){
                receipt.total_with_tax = this.get_total_without_tax();
                receipt.total_tax = 0;
                receipt.tax_details = [];
            }
            return receipt;
        },

        get_due: function(paymentline) {
            let total = 0;
            if (this.bill_type === '0'){
                total = this.get_total_without_tax();
            } else {
                total = this.get_total_with_tax();
            }
            let due = 0;
            if (!paymentline) {
                due = total - this.get_total_paid() + this.get_rounding_applied();
            } else {
                due = total;
                let lines = this.paymentlines.models;
                for (let i = 0; i < lines.length; i++) {
                    if (lines[i] === paymentline) {
                        break;
                    } else {
                        due -= lines[i].get_amount();
                    }
                }
            }
            return round_pr(due, this.pos.currency.rounding);
        },

        get_change: function(paymentline) {
            let change = 0;
            if (this.bill_type === '0'){
                change = this.get_total_without_tax();
            } else {
                change = this.get_total_with_tax();
            }
            if (!paymentline) {
                change = this.get_total_paid() - change - this.get_rounding_applied();
            } else {
                change = -change;
                let lines  = this.paymentlines.models;
                for (let i = 0; i < lines.length; i++) {
                    change += lines[i].get_amount();
                    if (lines[i] === paymentline) {
                        break;
                    }
                }
            }
            return round_pr(Math.max(0,change), this.pos.currency.rounding);
        },
    });

    
    var _superOrderline = models.Orderline;
    models.Orderline = models.Orderline.extend({
        export_as_JSON: function() {
            var json = _superOrderline.prototype.export_as_JSON.apply(this,arguments);
            if (this.order.bill_type === '0'){
                json.price_subtotal_incl = this.get_price_without_tax();
                json.tax_ids = [];
            }
            return json;
        },

        export_for_printing: function() {
            var json = _superOrderline.prototype.export_for_printing.apply(this,arguments);
            json.tax_details = this.get_tax_details();
            json.product_id = this.product.id;
            if (this.order.bill_type === '0'){
                json.price_with_tax = this.get_price_without_tax();
            }
            return json;
        },

        get_all_prices: function(){
            var self = this;

            var price_unit = this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
            var taxtotal = 0;

            var product =  this.get_product();
            var taxes_ids = product.taxes_id;
            var taxes =  this.pos.taxes;
            var taxdetail = {};
            var product_taxes = [];

            _(taxes_ids).each(function(el){
                var tax = _.detect(taxes, function(t){
                    return t.id === el;
                });
                product_taxes.push.apply(product_taxes, self._map_tax_fiscal_position(tax));
            });
            product_taxes = _.uniq(product_taxes, function(tax) { return tax.id; });

            var all_taxes = this.compute_all(product_taxes, price_unit, this.get_quantity(), this.pos.currency.rounding);
            var all_taxes_before_discount = this.compute_all(product_taxes, this.get_unit_price(), this.get_quantity(), this.pos.currency.rounding);
            _(all_taxes.taxes).each(function(tax) {
                taxtotal += tax.amount;
                taxdetail[tax.id] = tax.amount;
            });

            var price_with_tax_before_discount = all_taxes_before_discount.total_included;
            var tax_total = taxtotal;
            var tax_details = taxdetail;
            if (this.order.bill_type === '0'){
                price_with_tax_before_discount = all_taxes_before_discount.total_excluded;
                tax_total = 0;
                tax_details = {};
            }
            var total_excluded=all_taxes.total_excluded;
            var total_void=all_taxes.total_void;
            var total_included=all_taxes.total_included;
            if (this.order.get_client() && this.order.get_client().nuat_no){
            	total_included=total_excluded;
            	tax_total=0;
            	total_void=undefined;
            }
            return {
                "priceWithTax": total_included,
                "priceWithoutTax": total_excluded,
                "priceSumTaxVoid": total_void,
                "priceWithTaxBeforeDiscount": price_with_tax_before_discount,
                "tax": tax_total,
                "taxDetails": tax_details,
            };
        },
        
//        get_all_prices: function(){
//            var self = this;
//            var res = '';
//            if (this.order.get_client() && this.order.get_client().nuat_no){
//                var res = _super_order_line.get_all_prices.apply(this, arguments);
//                // var unit_price_set = this.get_unit_price();
//                res = {
//                    'priceWithTax': res.priceWithoutTax,
//                    'priceWithoutTax': res.priceWithoutTax,
//                    'priceSumTaxVoid': undefined,
//                    'priceWithTaxBeforeDiscount': res.priceWithoutTax,
//                    'tax': 0,
//                    'taxDetails':{}
//                }
//            }else{
//                var res = _super_order_line.get_all_prices.apply(this, arguments);
//            }
//            return res;
//        },        
    });

    var _superPaymentline = models.Paymentline;
    models.Paymentline = models.Paymentline.extend({
        export_for_printing: function() {
            var json = _superPaymentline.prototype.export_for_printing.apply(this,arguments);
            json.payment_method_id = this.payment_method.id;
            return json;
        },


        export_as_JSON: function() {
            var json = _superPaymentline.prototype.export_as_JSON.apply(this,arguments);
            json.utga = this.order.utga;
            return json;
        },
                
    });

    var _superPos = models.PosModel;
    models.PosModel = models.PosModel.extend({
        _save_to_server: function (orders, options) {
            return _superPos.prototype._save_to_server.apply(this,arguments).then(function (server_ids){
                rpc.query({
                    model: 'pos.order',
                    method: 'get_ebarimt',
                    args: [server_ids],
                }).then(function(result){
                    if (result.length) {
                        $(".mn_class_bill_id").text(result[0]['bill_id']);
                        $(".mn_class_lottery").text(result[0]['lottery']);
                        $(".mn_class_qr_data").attr("src", "/report/barcode/?type=QR&value=" + result[0]['qr_data'] + "&width=150&height=150");
                    }
                });
                return server_ids;
            });
        },
    });
});
