/** @odoo-module **/
import {NavBar} from "@web/webclient/navbar/navbar";
import {patch} from 'web.utils';
patch(NavBar.prototype, 'xf_dashboard/static/src/js/popular_menu.js', {
    /**
     * @override
     */
    onNavBarDropdownItemSelection(menu) {
        this._super(...arguments);
        if (menu) {
            this.saveMenuClick(menu.id);
        }
    },

    async saveMenuClick(menu_id) {
        await this.env.services.orm.call('xf.dashboard.popular.menu', 'save_menu', [menu_id]);
    },
});