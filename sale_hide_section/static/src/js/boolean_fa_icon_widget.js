/* Copyright 2019 Tecnativa - Ernesto Tejeda
 * Copyright 2022 Tecnativa - Víctor Martínez
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
odoo.define(
  "sale_layout_category_hide_detail.boolean_fa_icon_widget",
  function (require) {
    "use strict";

    const core = require("web.core");
    const AbstractField = require("web.AbstractField");
    const registry = require("web.field_registry");

    const _t = core._t;

    const BooleanFaIconWidget = AbstractField.extend({
      className: "o_boolean_fa_icon_widget",
      events: {
        click: "_toggleValue",
      },
      supportedFieldTypes: ["boolean"],

      // --------------------------------------------------------------------------
      // Public
      // --------------------------------------------------------------------------

      /**
       * A boolean field is always set since false is a valid value.
       *
       * @override
       */
      isSet: function () {
        return true;
      },

      // --------------------------------------------------------------------------
      // Private
      // --------------------------------------------------------------------------

      _allowEdit: function () {
        return true;
      },

      /**
       * Render font-awesome icon based on state
       *
       * @override
       * @private
       */

      _render: function () {
        // Set icon class
        var fa_icons = this.attrs.options.fa_icons;
        var icon_true = (fa_icons && fa_icons.icon_true) || "fa-check-square-o";
        var icon_false = (fa_icons && fa_icons.icon_false) || "fa-square-o";
        var fa_class = this.value ? icon_true : icon_false;
        // Set tip message
        var terminology = this.attrs.options.terminology;
        var hover_true =
          (terminology && _t(terminology.hover_true)) || _t("Click to uncheck");
        var hover_false =
          (terminology && _t(terminology.hover_false)) || _t("Click to check");
        var tip = this.value ? hover_true : hover_false;
        var style = this._allowEdit() ? "" : "cursor:default";
        // Set template and add it to $el
        var template = "<span class='fa %s' title='%s' style='%s'></span>";
        this.$el.empty().append(_.str.sprintf(template, fa_class, tip, style));
      },

      // --------------------------------------------------------------------------
      // Handlers
      // --------------------------------------------------------------------------

      /**
       * Toggle value
       *
       * @private
       * @param {MouseEvent} event
       */
      _toggleValue: function (event) {
        event.preventDefault();
        event.stopPropagation();
        if (this._allowEdit()) this._setValue(!this.value);
      },
    });

    registry.add("boolean_fa_icon", BooleanFaIconWidget);
    return BooleanFaIconWidget;
  }
);
