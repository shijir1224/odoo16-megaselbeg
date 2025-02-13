odoo.define('mw_pos.ClientDetailsEdit', function(require) {
    'use strict';

    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit');
    const Registries = require('point_of_sale.Registries');

    const EBarimtClientDetailsEdit = ClientDetailsEdit => class extends ClientDetailsEdit {
        constructor() {
            super(...arguments);
        }

        async getPartnerInformation() {
            if (this.changes.vat) {
                let result = await this.rpc({
                                          model: 'pos.config',
                                          method: 'get_partner_info',
                                          args: [this.changes.vat],
                             });
                if (result['found'] == false){
                    this.showPopup('ErrorPopup', {
                        'title': this.env._t('Register Check'),
                        'body': this.changes.vat + this.env._t(' company register number is not registered!'),
                        });
                    this.props.partner.name = "";
                }
                else if (result['registered'] == true) {
                    this.showPopup('ErrorPopup', {
                        'title': this.env._t('Customer Check'),
                        'body': this.env._t('Customer registered in the system.'),
                        });
                    }
                else {
                     this.props.partner.name = result['name'];
                     }
                this.props.partner.company_type = result['company_type'];
                this.render();
            }
        }
        changeCompanyType(event) {
            this.changes.company_type = event.target.value;
        }
    }

    Registries.Component.extend(ClientDetailsEdit, EBarimtClientDetailsEdit);

    return ClientDetailsEdit;
});
