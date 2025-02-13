odoo.define('saleorder.BarcodeView', function (require) {
"use strict";

var BarcodeEvents = require('barcodes.BarcodeEvents'); // handle to trigger barcode on bus
var core = require('web.core');
var FormController = require('web.FormController');

var _t = core._t;

// SO дээр баркод унших
FormController.include({
    _barcodeScanned: function (barcode, target) {
        // Event барих ==============================================
        console.log("===================Event====SO======",this);
        var self = this;
        var res_id = this.initialState.res_id;
        console.log("======", this.modelName, this.mode, this.initialState.data.state, res_id);
        if(this.modelName === 'sale.order' && this.mode === 'readonly'){
            if(this.initialState.data.state === 'draft' && res_id > 0){
                console.log("=================Add product=====", barcode);
                this._rpc({
                    model: 'sale.order',
                    method: 'create_line_from_scanner',
                    args: [ '===', res_id, barcode],
                }).then(function () {
                    self.trigger_up('reload');
                });
                return true
            }
        }
        // ========================================
        var res = this._super.apply(this, arguments);
        return res
    },
});

});