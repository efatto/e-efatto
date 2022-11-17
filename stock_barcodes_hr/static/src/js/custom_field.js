odoo.define('stock_barcodes_hr.FieldFloatNumericModeOnReturn', function (require) {
"use strict";

    var FieldFloatNumericMode = require('stock_barcodes.FieldFloatNumericMode').FieldFloatNumericMode;
    var field_registry = require('web.field_registry');

    var FieldFloatNumericModeOnReturn = FieldFloatNumericMode.extend({
        _onKeydown: function (ev) {
            if (ev.which === $.ui.keyCode.ENTER) {
                if (self.document.getElementsByClassName('btn-primary')) {
                    const button = self.$('#action_done_button');
                    button.click();
                }
            }
            this._super.apply(this, arguments);
        },
    });

    field_registry.add('FieldFloatNumericModeOnReturn', FieldFloatNumericModeOnReturn);

});
//
// odoo.define('stock_barcodes_hr.FormControllerOnEnter', function (require) {
// "use strict";
//
//     var BasicController = require('web.BasicController');
//     var FormController = require('web.FormController')
//
//     FormController.extend({
//         custom_events: _.extend({}, FormController.prototype.custom_events, {
//             return_clicked: '_onKeydownClicked',
//         }),
//         _onKeydownClicked: function (ev) {
//             if (ev.which === $.ui.keyCode.ENTER) {
//                 if (this.getElementsByClassName('btn-primary')) {
//                     this.getElementsByClassName('btn-primary').click()
//                 }
//             }
//         },
//     });
//
// });
