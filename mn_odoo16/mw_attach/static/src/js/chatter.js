odoo.define('mw_attach.Chatter_sc', function(require) {
//odoo.define('mail.Chatter', function (require) {
"use strict";
console.log('taaaaaaaaaaaa');

var AttachmentBox = require('mail.AttachmentBox');

var core = require('web.core');

var _t = core._t;
var QWeb = core.qweb;

var Chatter = require('mail.Chatter');

Chatter.include({
    /**
     * @override
     */
//	events: _.extend({}, Chatter.prototype.events, {
//        'click .o_chatter_button_attachment': '_onClickAttachmentButton',
//    }),

    init: function () {
        this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    start: function () {
    	return this._super.apply(this, arguments);    	
    },
    
    _fetchAttachments: function () {
        /*
    	    serverees attach achaallahdaa attachement_ids iig nemj avah
	    */
        console.log('_fetchAttachments mw---');
    	
        var self = this;
        var domain = [
            ['res_id', '=', this.record.res_id],
            ['res_model', '=', this.record.model],
        ];
        return this._rpc({
            model: 'ir.attachment',
            method: 'search_read_all',
            args: [domain,domain,['id', 'name', 'mimetype'],this.record.model,this.record.res_id],
        }).then(function (result) {
            //self._areAttachmentsLoaded = true; //Байнга reload хийх
            self.attachments = result;
        });        
//        return this._rpc({
//            model: 'ir.attachment',
//            method: 'search_read_all',
//            domain: domain,
//            fields: ['id', 'name', 'mimetype'],
//        }).then(function (result) {
//            self._areAttachmentsLoaded = true;
//            self.attachments = result;
//        });

    },
});

return Chatter;

});
