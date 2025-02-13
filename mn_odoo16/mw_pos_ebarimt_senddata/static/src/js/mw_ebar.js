odoo.define('mw_pos_ebarimt_senddata.mw_ebar', function (require) {
"use strict";
    var models = require('point_of_sale.models');
    var rpc = require('web.rpc');
    models.load_fields('pos.session',['last_ebarimt_senddata']);

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        
        load_orders: function () {
            _super_posmodel.load_orders.apply(this, arguments);
            var self = this;
            var today = new Date();
            var now_date = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
            if (now_date!=this.pos_session.last_ebarimt_senddata){
                var data = JSON.stringify({"":""});
                var settings = { 
                    "async": true,
                    "crossDomain": true,
                    "url": this.config.vatps_url+"/posapi_senddata",
                    "method": "POST",
                    "headers": {
                        "content-type": "application/json", 
                        "posapi_method":"posapi_senddata",
                    },
                    "processData": false,
                    "data":  data
                } 
                $.ajax(settings).done(function (response) { 
                    rpc.query({
                        model: 'pos.session',
                        method: 'set_last_ebarimt_senddata',
                        args: [self.pos_session.id, self.pos_session.id]
                    }).then(function (datas) {
                        console.log(datas);
                    });
                }).fail(function (type, error){
                    
                });
            }
        },
    });


});