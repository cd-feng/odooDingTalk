odoo.define('dingding.add.employee.button', function (require) {
    "use strict";

    let KanbanController = require('web.KanbanController');
    let ListController = require('web.ListController');
    let core = require('web.core');

    ListController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'hr.employee') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'hr.employee'\" class=\"btn btn-secondary\">添加待入职员工</button>";
                let button2 = $(but).click(this.proxy('add_dingding_employee_list'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        add_dingding_employee_list: function () {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'dingding.add.employee',
                target: 'new',
                views: [[false, 'form']],
                context: [],
            });
        }
    });

    KanbanController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'hr.employee') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'hr.employee'\" class=\"btn btn-secondary\">添加待入职员工</button>";
                let button2 = $(but).click(this.proxy('add_dingding_employee_list'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        add_dingding_employee_list: function () {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'dingding.add.employee',
                target: 'new',
                views: [[false, 'form']],
                context: [],
            });
        }
    });

});
