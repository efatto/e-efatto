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
    });

    var FieldFloatTimeNumericModeOnReturn = basic_fields.FieldFloatTime.extend({
        events: _.extend({}, basic_fields.FieldFloatTime.prototype.events, {
            "focusin": "_onFocusIn",
        }),
        _onFocusIn: function () {
            // Auto select all content when user enters into fields with this
            // widget.
            this.$input.select();
        },
        _prepareInput: function ($input) {
            // Set numeric mode to display numeric keyboard in mobile devices
            var $input_numeric = this._super($input);
            $input_numeric.attr({'inputmode': 'numeric'});
            return $input_numeric;
        },
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
    field_registry.add('FieldFloatTimeNumericModeOnReturn', FieldFloatTimeNumericModeOnReturn);

});
