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
        _parseValue: function (value) {
            if (isNaN(value)) {
                return false;
            }
            return this._super.apply(this, arguments);
        },
    });

    field_registry.add('FieldFloatNumericModeOnReturn', FieldFloatNumericModeOnReturn);

});
