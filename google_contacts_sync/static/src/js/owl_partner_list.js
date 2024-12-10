
/** @odoo-module */
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { ListController } from '@web/views/list/list_controller';
import { useService } from "@web/core/utils/hooks";
const { Component } = owl;


class ResPartnerListController extends ListController {
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

export const resPartnerListView = {
    ...listView,
    Controller: ResPartnerListController,
    buttonTemplate: "google_contacts_sync_tree.buttons",

};

registry.category('views').add('button_in_tree', resPartnerListView);
