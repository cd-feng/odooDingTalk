odoo.define('dingding_approval.oa_approval_button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let FormController = require('web.FormController');
    let Dialog = require('web.Dialog');
    let core = require('web.core');
    let QWeb = core.qweb;
    let rpc = require('web.rpc');
    var show_button_model = ['oa.leave.application'];
    var  Widget = require('web.Widget');

    ListController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let self = this;
            let def = rpc.query({
                model: 'dindin.approval.control',
                method: 'get_oa_model',
                args: [],
            }).then(function (data) {
                console.log(data);
                show_button_model = data;
            });
            var tree_model = this.modelName;
            for(var i=0; i<show_button_model.length; i++) {
                if (tree_model == show_button_model[i]){
                    var button2 = $("<button type='button' class='btn btn-sm btn-default'>发起审批</button>")
                        .click(this.proxy('popup_import_wizard'));
                    this.$buttons.append(button2);
                }
            }
            return $buttons;
        },
        popup_import_wizard: function () {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'import.wizard',
                views: [[false, 'form']],
                view_mode: "form",
                view_type: 'form',
                view_id: 'import_wizard_form',
                target: 'new',
            });
        },

    });

    FormController.include({
        renderButtons: function ($node) {
            console.log("renderButtons");
            console.log(this.modelName);
            let $buttons = this._super.apply(this, arguments);
            console.log("renderButtons--end");
        }

    });

});
