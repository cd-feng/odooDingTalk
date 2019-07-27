odoo.define('dingding.user.work.record.kanban', function (require) {
    "use strict";

    let viewRegistry = require('web.view_registry');
    let KanbanController = require('web.KanbanController');
    let KanbanView = require('web.KanbanView');

    function DingDingWorkRecordButtons($node) {
        var self = this;
        this.$buttons = $('<div/>');
        this.$buttons.html('<button class="btn btn-primary type="button">获取我的待办</button>');
        this.$buttons.on('click', function () {
            self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'get.user.dingding.work.record',
                target: 'new',
                views: [[false, 'form']],
                context: [],
            });
        });
        this.$buttons.appendTo($node);
    }

    let DingDingWorkRecordKanbanController = KanbanController.extend({
        renderButtons: function ($node) {
            return DingDingWorkRecordButtons.apply(this, arguments);
        },
    });

    let DingDingWorkRecordKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: DingDingWorkRecordKanbanController,
        }),
    });

    viewRegistry.add('dingding_work_record_kanban', DingDingWorkRecordKanbanView);
});
