odoo.define('mail_activity_timeline.brightness', function (require) {
"use strict";

var TimelineRenderer = require('web_timeline.TimelineRenderer');

TimelineRenderer.include({
    event_data_transform: function (evt) {
        var self = this;
        var r = this._super(evt);
        if (self.arch.attrs.color_field !== undefined) {
            var color = evt[self.arch.attrs.color_field];
            if (color) {
                const rgb = [255, 0, 0];
                const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(color);
                if (result) {
                    const red = parseInt(result[1], 16);
                    const green = parseInt(result[2], 16);
                    const black = parseInt(result[3], 16);
                    // http://www.w3.org/TR/AERT#color-contrast
                    const brightness = Math.round(((parseInt(red) * 299) +
                        (parseInt(green) * 587) +
                        (parseInt(black) * 114)) / 1000);
                    const textColor = (brightness > 125) ? 'black' : 'white';
                    r.style = r.style + 'color: ' + textColor + ';'
                }
            }
        }
        return r;
    },
});

});
