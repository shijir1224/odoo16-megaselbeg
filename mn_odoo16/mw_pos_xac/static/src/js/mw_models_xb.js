odoo.define('mw_pos_xac.mw_models_xb', function (require) {
    "use strict";
    var models = require('point_of_sale.models');
    models.Order = models.Order.extend({
        get_xac_ok_payment: function(){
            var order = this.pos.get_order();
            var plines = order.get_paymentlines();
            for (var i = 0; i < plines.length; i++) {
                if (plines[i].payment_method.xac_ok && this.pos.config.epos_ok) {
                    return true;
                }
            }
            return false;
        },
        get_xac_data: function(operationcode, send_amount, ecrRefNo){
            var vals = {
                "operation": "SALE",
                "ecrRefNo": ecrRefNo,
            }
            if (send_amount){
                vals["amount"] = send_amount
            }
            return vals
        },
        get_xac_settings: function(data){
            var terminalID = this.pos.config.xac_url;
            return { 
                "url": "http://127.0.0.1:8088/ecrt1000/",
                "Content-Type": "application/x-www-form-urlencoded",
                // "headers": {
                //     // "content-type": "application/json; charset=utf-8", 
                //     // "posapi_method":"posapi_put",
                //     "Access-Control-Allow-Origin": "*",
                // },
                "method": "POST",
                "data": data,
                // "operation": "Sale",
            }
        },
    });
});