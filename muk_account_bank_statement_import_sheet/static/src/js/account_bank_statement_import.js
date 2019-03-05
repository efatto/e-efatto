/**********************************************************************************
* 
*    Copyright (C) 2018 MuK IT GmbH
*
*    This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU Affero General Public License as
*    published by the Free Software Foundation, either version 3 of the
*    License, or (at your option) any later version.
*
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU Affero General Public License for more details.
*
*    You should have received a copy of the GNU Affero General Public License
*    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*
**********************************************************************************/

odoo.define('account_bank_statement.import', function (require) {
"use strict";

var core = require('web.core');

var BaseImport = require('base_import.import');
var Model = require('web.Model');

var _t = core._t;
var QWeb = core.qweb;

var AccountBankStatementImport = BaseImport.DataImport.extend({
    init: function (parent, action) {
        this._super.apply(this, arguments);
        this.filename = action.params.filename;
        action.display_name = _t('Import Bank Statement');
        this.Import = new Model('account.bank.statement.import.ex.wizard');
    },
    start: function () {
        var self = this;
        return this._super().then(function (res) {
        	self.loaded_file();
        });
    },
    create_model: function() {
    	return $.Deferred().resolve(this.parent_context.wizard_id);
    },
    onfile_loaded: function () {
    	this.$('.oe_import_file_show').val(this.filename);
        this.$('label[for=my-file-selector], input#my-file-selector').hide();
        this.$('label[for=my-file-selector]').parent().append(
        		$('<span/>' , {class: "btn btn-default disabled", text: "File loaded!"}));
        this.$('.oe_import_file_reload').hide();
        this.settings_changed();
    },
});

core.action_registry.add('import_bank_statement', AccountBankStatementImport);

});

