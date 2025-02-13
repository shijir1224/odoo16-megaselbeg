// odoo.define('mw_mining.mining_grid', function (require) {
//     'use strict';
//     var grid_render = require('web_grid.GridRenderer');
    
//     grid_render.include({
//         _format: function (value) {
//             var self = this;
//             if ((self.cellWidgetOptions.not_zero=='not_zero' && value === 0 ) || value === undefined ){
//                 return '';
//             }
//             return this._super.apply(this, arguments);;
//         }
//     });
// });