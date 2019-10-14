odoo.define('dingding.base.tree.fields', function (require) {
    var AbstractField = require('web.AbstractField');
    var registry = require('web.field_registry');

    var FieldApprovalState = AbstractField.extend({
        supportedFieldTypes: ['char'],

        isSet: function () {
            return true;
        },
        _render: function () {
            this.value && this.$el.html(this.value);
        }
    });
    registry.add('dd_approval_widget', FieldApprovalState)
});

