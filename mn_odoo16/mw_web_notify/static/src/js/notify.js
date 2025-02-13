odoo.define('mw_web_notify.notify', function (require) {
    "use strict";
    var WebClient = require('web.WebClient');
    var Notification = require('web.Notification');
    WebClient.include({
        on_message: function (message) {
            return this.call(
                'notification', 'notify', {
                    type: message.type,
                    title: message.title,
                    message: message.message,
                    sticky: message.sticky,
                    className: message.className,
                    mw_not_id: message.mw_not_id,
                }
            );
        },
    });
    var MwNotification = Notification.include({
        template: "MwNotification",
        xmlDependencies: (Notification.prototype.xmlDependencies || [])
            .concat(['/mw_web_notify/static/src/xml/notify.xml']),
        init: function(parent, params) {
            this._super(parent, params);
            this.event_id = params.eventID;
            this.mw_not_id = params.mw_not_id;
            this.events = _.extend(this.events || {}, {
                'click .link2event': function() {
                    var self = this;
                    var this_mw_not_id = this.mw_not_id;
                    var model_model = this_mw_not_id.mw_model_model;
                    var res_id = this_mw_not_id.mw_res_id;
                    this.do_action({
                        type: 'ir.actions.act_window',
                        res_model: model_model,
                        res_id: res_id,
                        views: [[false, 'form']],
                        target: 'current'
                    });
                    this.close();
                },
                'click .link2recall': function() {
                    this.close();
                },
                'click .link2showed': function() {
                    var this_mw_not_id = this.mw_not_id;
                    var res_id = this_mw_not_id.mw_id;
                    this._rpc({
                        model: 'mw.notify',
                        method: 'showed',
                        args: [ '===', res_id],
                    }).then(function () {
                        
                    });
                    this.close();
                },
            });
        },
    });
});