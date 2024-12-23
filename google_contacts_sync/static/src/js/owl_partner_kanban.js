
/** @odoo-module */
import { registry } from '@web/core/registry'
import { kanbanView } from '@web/views/kanban/kanban_view'
import { KanbanController } from "@web/views/kanban/kanban_controller"
import { useService } from "@web/core/utils/hooks"


class ResPartnerKanbanController extends KanbanController {
    setup() {
        super.setup();
        this.orm = useService("orm");

    }

    async clickSyncButton() {
        const orm = this.env.services.orm;
        const result = await orm.call("res.partner", "google_contacts_trigger", [this.env.res_id]).then(function (result) {
                window.open(result)
            });}

}

export const resPartnerKanbanView = {
    ...kanbanView,
    Controller: ResPartnerKanbanController,
    buttonTemplate: "google_contacts_sync_kanban_view",

};

registry.category('views').add('button_in_kanban_view', resPartnerKanbanView);
