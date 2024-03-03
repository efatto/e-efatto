odoo.define('sale_hide_section.hide_section_details', function (require) {
"use strict";

    var fieldRegistry = require('web.field_registry');
    var section_and_note_one2many = fieldRegistry.get('section_and_note_one2many');

    var SectionAndNoteListRenderer = {
        _renderBodyCell: function (record, node, index, options) {
            var $cell = this._super.apply(this, arguments);

            var field_info = this.state.fieldsInfo.list[node.attrs.name];
            var show_in_line_section = field_info && field_info.options.show_in_line_section;

            var isSection = record.data.display_type === 'line_section';
            var isNote = record.data.display_type === 'line_note';
            if (isSection || isNote) {
                if (show_in_line_section) {
                    return $cell.removeClass('o_hidden');
                } else if (node.attrs.name === "name") {
                    var nbrColumns = this._getNumberOfCols();
                    if (this.handleField) {
                        nbrColumns--;
                    }
                    if (this.addTrashIcon) {
                        nbrColumns--;
                    }
                    nbrColumns -= this._getNumberOfLineSectionFields();
                    $cell.attr('colspan', nbrColumns);
                }
            }
            return $cell;
        },
        _getNumberOfLineSectionFields: function () {
            var section_fields_count = 0;
            var self = this;
            this.columns.forEach(function(elem) {
                var field_info = self.state.fieldsInfo.list[elem.attrs.name];
                if (field_info && field_info.options.show_in_line_section)
                    section_fields_count ++;
            });
            return section_fields_count;
        },
        _renderHeaderCell: function (node) {
            var $th = this._super.apply(this, arguments);
            var field_info = this.state.fieldsInfo.list[node.attrs.name];
            if (field_info && field_info.options.show_in_line_section)
                $th.text("").removeClass('o_column_sortable');
            return $th
        },
        _renderBody: function (record) {
            var $body = this._super();
            var hide_details = false;
            // on clik on eye icon we hide/show the rows until next section
            _.each($body[0].childNodes, function (row) {
                _.each(row.childNodes, function(cell) {
                    for (var i = 0; i < cell.classList.length; i += 1) {
                        if (cell.classList[i] === 'o_boolean_fa_icon_cell') {
                            if (cell.firstChild && cell.firstChild.firstChild && cell.firstChild.firstChild.className === 'fa fa-eye-slash') {
                                hide_details = true;
                            } else if (cell.firstChild && cell.firstChild.firstChild && cell.firstChild.firstChild.className === 'fa fa-eye') {
                                hide_details = false;
                            }
                        }
                    }
                });
                if (hide_details && row.className === 'o_data_row') {
                    row.hidden = true;
                } else {
                    row.hidden = false;
                }
            });
            return $body;
        },
    };

    section_and_note_one2many.include({
        _getRenderer: function () {
            var result = this._super.apply(this, arguments);
            if (this.view.arch.tag === 'tree') {
                result.include(SectionAndNoteListRenderer)
            }
            return result
        },
    });
});
