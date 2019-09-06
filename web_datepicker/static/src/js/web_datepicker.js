odoo.define('web_datepicker.web.datepicker', function(require) {
	"use strict";
	var core = require('web.core');
	var DatePicker = require('web.datepicker');
	var fieldUtils = require('web.field_utils');
	var time = require('web.time');

	var _t = core._t;

	DatePicker.DateWidget.include({
		init: function(parent, options) {
			this._super.apply(this, arguments);
			var _options = {};
			if (options && (options.showType === "months" || options.showType === "years")) {
				var l10n = _t.database.parameters;
				_options.viewMode = options.showType;
				_options.format = time.strftime_to_moment_format(options.format)
			}
			this.options = _.defaults(_options || {}, this.options)
		},

		_formatClient: function(v) {
			return fieldUtils.format.date(v, null, {timezone: false, datepicker: {showType: this.options.showType, format:this.options.format}});
		},
		_parseClient: function(v) {
			return fieldUtils.parse.date(v, null, {timezone: false, datepicker: {showType: this.options.showType, format: this.options.format}});
		}

	});
	return DatePicker;
});

odoo.define('web_datepicker.web.field_utils', function(require) {
	"use strict";

	var core = require('web.core');
	var fieldUtils = require('web.field_utils');
	var time = require('web.time');
	var origin_format_date = fieldUtils.format.date
	var origin_parse_date = fieldUtils.parse.date;
	var prigin_
	var _t = core._t;

	fieldUtils.format.date = function(value, field, options) {
		if (value && options) {
			var showType;
			if ('datepicker' in options && 'showType' in options.datepicker) {
				showType = options.datepicker.showType;
			}
			if (showType === 'months' || showType === 'years') {
				var _format = time.strftime_to_moment_format(options.datepicker.format)
				return value.format(_format);
			}
		}
		return origin_format_date(value, field, options);
	},

	fieldUtils.parse.date = function(value, field, options) {
		if (value && options) {
			var showType;
			if ('datepicker' in options && 'showType' in options.datepicker) {
				showType = options.datepicker.showType;
			}
			if (showType === 'months' || showType === 'years') {
				var date_pattern = options.datepicker.format;
				var date_pattern_wo_zero = date_pattern.replace('MM', 'M').replace('DD', 'D');
				var date;
				if (options && options.isUTC) {
					date = moment.utc(value);
				} else {
					date = moment.utc(value, [date_pattern, date_pattern_wo_zero, moment.ISO_8601], true);
				}
				if (date.isValid()) {
					if (date.year() === 0) {
						date.year(moment.utc().year());
					}
					if (date.year() >= 1900) {
						date.toJSON = function() {
							return this.clone().locale('en').format('YYYY-MM-DD');
						};
						return date;
					}
				}
				throw new Error(_.str.sprintf(core._t("'%s' is not a correct date"), value));
			}else
				{
					var datePattern = time.getLangDateFormat();
					var datePatternWoZero = datePattern.replace('MM', 'M').replace('DD', 'D');
					var date;
					if (options && options.isUTC) {
						date = moment.utc(value);
					} else {
						date = moment.utc(value, [datePattern, datePatternWoZero, moment.ISO_8601], true);
					}
					if (date.isValid()) {
						if (date.year() === 0) {
							date.year(moment.utc().year());
						}
						if (date.year() >= 1900) {
							date.toJSON = function() {
								return this.clone().locale('en').format('YYYY-MM-DD');
							};
							return date;
						}
					}
					throw new Error(_.str.sprintf(core._t("'%s' is not a correct date"), value));
				}
		}
		return origin_parse_date(value, field, options);
	}

});

odoo.define('web_datepicker.web.ListRenderer', function(require) {
	"use strict";

	var ListRenderer = require('web.ListRenderer');
	var field_utils = require('web.field_utils');
	var FIELD_CLASSES = {
		float: 'o_list_number',
		integer: 'o_list_number',
		monetary: 'o_list_number',
		text: 'o_list_text',
	};
	ListRenderer.include({
		_renderBodyCell: function(record, node, colIndex, options) {
			var tdClassName = 'o_data_cell';
			if (node.tag === 'button') {
				tdClassName += ' o_list_button';
			} else if (node.tag === 'field') {
				var typeClass = FIELD_CLASSES[this.state.fields[node.attrs.name].type];
				if (typeClass) {
					tdClassName += (' ' + typeClass);
				}
				if (node.attrs.widget) {
					tdClassName += (' o_' + node.attrs.widget + '_cell');
				}
			}
			var $td = $('<td>', {class: tdClassName});

			// We register modifiers on the <td> element so that it gets the correct
			// modifiers classes (for styling)
			var modifiers = this._registerModifiers(node, record, $td, _.pick(options, 'mode'));
			// If the invisible modifiers is true, the <td> element is left empty.
			// Indeed, if the modifiers was to change the whole cell would be
			// rerendered anyway.
			if (modifiers.invisible && !(options && options.renderInvisible)) {
				return $td;
			}

			if (node.tag === 'button') {
				return $td.append(this._renderButton(record, node));
			} else if (node.tag === 'widget') {
				return $td.append(this._renderWidget(record, node));
			}
			if (node.attrs.widget || (options && options.renderWidgets)) {
				var $el = this._renderFieldWidget(node, record, _.pick(options, 'mode'));
				this._handleAttributes($el, node);
				return $td.append($el);
			}
			var name = node.attrs.name;
			var field = this.state.fields[name];
			var value = record.data[name];
			var tmp = {
				data: record.data,
				escape: true,
				isPassword: 'password' in node.attrs,
			};
			if (field.type === 'date' && node.attrs.options) {
				var json;
				try {
					json = JSON.parse(node.attrs.options);
				} catch(e) {
					json = JSON.parse(node.attrs.options.replace(/\'/g, "\""));
				}
				if (json) {
					tmp = _.defaults(tmp, json)
				}
			}
			var formattedValue = field_utils.format[field.type](value, field, tmp);
			this._handleAttributes($td, node);
			return $td.html(formattedValue);
		}
	})

});

