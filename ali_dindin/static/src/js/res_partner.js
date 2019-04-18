odoo.define('dingding.res.partner.synchronous.button', function (require) {
    "use strict";

    let KanbanController = require('web.KanbanController');
    let ListController = require('web.ListController');
    let Dialog = require('web.Dialog');
    let core = require('web.core');
    let QWeb = core.qweb;
    let rpc = require('web.rpc');

    let start_synchronous_partner = function () {
        rpc.query({
            model: 'res.partner',
            method: 'synchronous_dingding_res_partner',
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
            if (tree_model == 'res.partner') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'res.partner'\" class=\"btn btn-primary\">同步钉钉联系人</button>";
                let button2 = $(but).click(this.proxy('synchronous_dingding_partner_list'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        synchronous_dingding_partner_list: function () {
            new Dialog(this, {
                title: "同步钉钉联系人",
                size: 'medium',
                buttons: [
                    {
                        text: "开始",
                        classes: 'btn-primary',
                        close: true,
                        click: start_synchronous_partner
                    }, {
                        text: "取消",
                        close: true
                    }
                ],
                $content: $(QWeb.render('SynchronousDingPartnerTemplate', {widget: this, data: []}))
            }).open();
        },
    });

    KanbanController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'res.partner') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'res.partner'\" class=\"btn btn-primary\">同步钉钉联系人</button>";
                let button2 = $(but).click(this.proxy('synchronous_dingding_partner_kanban'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        synchronous_dingding_partner_kanban: function () {
            new Dialog(this, {
                title: "同步钉钉联系人",
                size: 'medium',
                buttons: [
                    {
                        text: "开始",
                        classes: 'btn-primary',
                        close: true,
                        click: start_synchronous_partner
                    }, {
                        text: "取消",
                        close: true
                    }
                ],
                $content: $(QWeb.render('SynchronousDingPartnerTemplate', {widget: this, data: []}))
            }).open();
        },
    });

});
