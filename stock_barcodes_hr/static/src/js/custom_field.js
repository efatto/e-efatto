odoo.define('stock_barcodes_hr.FieldFloatNumericModeOnReturn', function (require) {
"use strict";

    var FieldFloatNumericMode = require('stock_barcodes.FieldFloatNumericMode').FieldFloatNumericMode;
    var basic_fields = require('web.basic_fields');
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

    var FieldFloatTimeIgnoreBarcode = basic_fields.FieldFloatTime.extend({
        _parseValue: function (value) {
            var regex = /([0-9]+):([0-9]+)/;
            if (value.match(regex) && value.length > 5) {
                var cleaned_value = value.match(regex)[0];
                arguments[0] = cleaned_value;
                this.$input[0].value = cleaned_value;
            }
            return this._super.apply(this, arguments);
        },
    });

    field_registry.add('FieldFloatNumericModeOnReturn', FieldFloatNumericModeOnReturn);
    field_registry.add('FieldFloatTimeIgnoreBarcode', FieldFloatTimeIgnoreBarcode);

});
