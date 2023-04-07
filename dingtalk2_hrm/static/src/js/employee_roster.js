/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { listView } from '@web/views/list/list_view';
import { ListController } from "@web/views/list/list_controller";


export class Dingtalk2HrmRosterKanbanController extends KanbanController {

    setup() {
        super.setup();
        this.orm = useService("orm");
    }

   async synchronizeInsuredSchemeEmployee(){
        // await this.model.notificationService.add('.....', { type: 'success' });
        this.actionService.doAction({
            name: '同步花名册',
            type: 'ir.actions.act_window',
            res_model: 'dingtalk.employee.roster.synchronous',
            target: 'new',
            views: [[false, 'form']],
            context: [],
        });
    }

    async addPendingEnding(){
        this.actionService.doAction({
            name: '添加待入职员工',
            type: 'ir.actions.act_window',
            res_model: 'dingtalk.addpreentry.roster',
            target: 'new',
            views: [[false, 'form']],
            context: []
        });
    }

}
registry.category("views").add("dingtalk_employee_roster_kanban", {
    ...kanbanView,
    Controller: Dingtalk2HrmRosterKanbanController,
    buttonTemplate: "DingTalk2HrmKanbanView.Buttons",
});


export class Dingtalk2HrmRosterListController extends ListController {
    setup() {
        super.setup();
        this.orm = useService("orm");
    }

    async synchronizeInsuredSchemeEmployee(){
        const selectedIds = await this.getSelectedResIds();
        this.actionService.doAction({
            name: '同步花名册',
            type: 'ir.actions.act_window',
            res_model: 'dingtalk.employee.roster.synchronous',
            target: 'new',
            views: [[false, 'form']],
            context: [],
        });
    }

    async addPendingEnding(){
        this.actionService.doAction({
            name: '添加待入职员工',
            type: 'ir.actions.act_window',
            res_model: 'dingtalk.addpreentry.roster',
            target: 'new',
            views: [[false, 'form']],
            context: []
        });
    }

}
registry.category('views').add('dingtalk_employee_roster_tree', {
    ...listView,
    Controller: Dingtalk2HrmRosterListController,
    buttonTemplate: 'DingTalk2HrmListView.Buttons',
})
