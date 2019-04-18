odoo.define('dingding.res.employee.synchronous.button', function (require) {
    "use strict";

    let KanbanController = require('web.KanbanController');
    let ListController = require('web.ListController');
    let Dialog = require('web.Dialog');
    let core = require('web.core');
    let QWeb = core.qweb;
    let rpc = require('web.rpc');

    let start_synchronous_employee = function () {
        rpc.query({
            model: 'hr.employee',
            method: 'synchronous_dingding_employee',
            args: [],
        }).then(function (result) {
            if(result.state){
                location.reload();
            }else{
                alert(result.msg);
            }
        });
    };

    ListController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'hr.employee') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'hr.employee'\" class=\"btn btn-primary\">同步钉钉员工</button>";
                let button2 = $(but).click(this.proxy('synchronous_dingding_employee_list'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        synchronous_dingding_employee_list: function () {
            new Dialog(this, {
                title: "同步钉钉员工",
                size: 'medium',
                buttons: [
                    {
                        text: "开始同步",
                        classes: 'btn-primary',
                        close: true,
                        click: start_synchronous_employee
                    }, {
                        text: "取消同步",
                        close: true
                    }
                ],
                $content: $(QWeb.render('SynchronousDingEmployeeTemplate', {widget: this, data: []}))
            }).open();
        },
    });

    KanbanController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'hr.employee') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'hr.employee'\" class=\"btn btn-primary\">同步钉钉员工</button>";
                let button2 = $(but).click(this.proxy('synchronous_dingding_employee_kanban'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        synchronous_dingding_employee_kanban: function () {
            new Dialog(this, {
                title: "同步钉钉员工",
                size: 'medium',
                buttons: [
                    {
                        text: "开始同步",
                        classes: 'btn-primary',
                        close: true,
                        click: start_synchronous_employee
                    }, {
                        text: "取消同步",
                        close: true
                    }
                ],
                $content: $(QWeb.render('SynchronousDingEmployeeTemplate', {widget: this, data: []}))
            }).open();
        },
    });

});
