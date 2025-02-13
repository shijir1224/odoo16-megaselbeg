odoo.define('easy_pdf_creator.ActionMenus', function (require) {
    'use strict';
    // ------
    // var _t = require('web.core');
    var ActionMenus = require('web.ActionMenus');
    var data = require('web.data');
    const { patch } = require('web.utils');
    var DropdownMenuItem = require('web.DropdownMenuItem');
    const { useListener } = require('web.custom_hooks');
    // var CrashManager = require('web.CrashManager').CrashManager;
    
    var core = require('web.core');

    var _t = core._t;

    // SideBar ==> ActionMenus
    async function easyPrintPropsGetter(props, env, rpc) {
        const [activeId] = props.activeIds;
        const { context } = props;
        if (env.view.type !== "form" || !activeId) {
            return false;
        }
        const items = await rpc({
            args: [env.action.res_model, activeId],
            context,
            method: 'get_google_drive_config',
            model: 'google.drive.config',
        });
        return Boolean(items.length) && { activeId, context, items };
    }

    patch(ActionMenus.prototype, 'easy_pdf_creator.ActionMenus', {

        on_click_easy_print: function(item) {
            var view = this.getParent();
            launch_easy_print(this, view); // function
        }
    });
    
    class EasyPrintMenu extends ActionMenus {
        setup() {
            super.setup();
            console.log('XIXI');
            on_click_easy_print();
        }
        on_click_easy_print() {
            console.log('XAXA');
            var view = this.getParent();
            console.log('XOXO');
            launch_easy_print(this, view); // function
        }
    }
    // ActionMenus.include({
    //     init: function (parent, options) {
    //         this._super.apply(this, arguments);
    //         var item = {
    //             label: _t('EasyPrint'),
    //             callback: this.on_click_easy_print, // function,
    //             classname: 'oe_easy_print',
    //         };
    //         this.items['print'].push(item);
    //     },
    //     // Event
    //     on_click_easy_print: function(item) {
    //         var view = this.getParent();
    //         launch_easy_print(this, view); // function
    //     },
    // });

    // to Python - Check pdf template
    
    function launch_easy_print(self, view) {
        var res_model = self.env.model;
        var res_id = self.env.activeIds[0];
        console.log('----data--', res_model, res_id);
        var template_id;
        var ds = new data.DataSet(self, 'pdf.template.generator');
        ds.call("search_default_template", ['pdf.template.generator', res_model])
            .then(function (template) {
                console.log('-----temp-----', template, res_model, res_id);
                if(template != false){
                    ds.call("print_template", [ template, res_id])
                            .then(function(result){
                                view.do_action(result);
                        });
                }else{
                    // Not found, Warning
                    // new CrashManager().show_warning({data: {
                    //     exception_type: _t("Анхааруулга"),
                    //     message: _t("Хэвлэх загвар олдсонгүй!, Загварын нэр 'default' байх ёстой.")
                    // }});
                    console.log('Crash')
                }
                try {
                    ds.call("print_template", [ template, res_id])
                            .then(function(result){
                                view.do_action(result);
                        });
                } catch(e) {
                    // avoid error toast (crashmanager)
                    e.event.preventDefault();
                    // try to unwrap mess of an error object to a usable error message
                    throw new Error(
                        !e.message ? e.toString()
                      : !e.message.data ? e.message.message
                      : e.message.data.message || _t("Хэвлэх загвар олдсонгүй!, Загварын нэр 'default' байх ёстой.")
                    );
                }
            });
        return "TEXT";
    }

    // return {
    //     launch_easy_print: launch_easy_print,
    // };
    EasyPrintMenu.template = 'EasyPrintMenu';

    Registries.Component.add(EasyPrintMenu);

    return EasyPrintMenu;
    

});
