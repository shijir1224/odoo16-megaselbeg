odoo.define('mw_change_multi_company_id.SwitchCompanyMenu', function (require) {
    "use strict";

    const { SwitchCompanyMenu } = require("@web/webclient/switch_company_menu/switch_company_menu");
    const { patch } = require('web.utils');
    const { session } =  require("@web/session");
    const rpc  = require('web.rpc');

    function onSwitchCompanyClick(companyId) {
        var self = this;
        return rpc.query({
            model: 'res.users',
            method: 'write_company',
            args: [session.uid, {'company_id': companyId}],
        })
    }

    patch(SwitchCompanyMenu.prototype, 'mw_change_multi_company_id.SwitchCompanyMenu', {

        logIntoCompany(companyId) {             
            if (companyId){
                onSwitchCompanyClick(companyId);
            }
            this._super(...arguments);         
        }
    });

});