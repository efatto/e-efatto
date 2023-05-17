odoo.define( "mail_activity_timeline.info", function (require) {
"use strict";

var TimelineRenderer = require('web_timeline.TimelineRenderer');
var core = require('web.core');
var _t = core._t;
var qweb = core.qweb;

TimelineRenderer.include({
    _onSelect: function (ev) {
        var notSelectedIds = _.difference(
            this.timeline.itemsData.getIds(),
            ev.items
        );
        _.each(notSelectedIds, function (id) {
            this.$(_.str.sprintf('.oe_timeline_info[data-id="%s"]', id)).remove();
        }.bind(this));

        var r = this._super(ev);
        _.each(ev.items, function (id) {
            var $deleteButton = $(this.timeline.itemSet.items[id].dom.deleteButton);
            var $Info = $(qweb.render('TimelineView.Info', {
                id: id,
                info: $(this.timeline.itemSet.items[id])[0].data.evt.info,
            }));
            $deleteButton.after($Info);
        }.bind(this));
        return r;
    },
});
});
