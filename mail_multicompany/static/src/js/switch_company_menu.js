/** @odoo-module **/

import { registry } from "@web/core/registry";
import { SwitchCompanyMenu } from "@web/webclient/switch_company_menu/switch_company_menu";

var rpc = require('web.rpc');

class ExtendedSwitchCompanyMenu extends SwitchCompanyMenu {
    logIntoCompany(companyId) {
        super.logIntoCompany(companyId);

        rpc.query({
            model: 'res.users',
            method: 'set_current_company',
            args: [companyId],
        }).then((result) => {
            console.log('RPC Success: ', result);
        }).catch((error) => {
            console.log('RPC Error: ', error);
        });
    }
}

const systrayItem = {

    Component: ExtendedSwitchCompanyMenu,
    isDisplayed(env) {
        const { availableCompanies } = env.services.company;
        return Object.keys(availableCompanies).length > 1;
    },
};

registry.category("systray").remove("SwitchCompanyMenu");
registry.category("systray").add("ExtendedSwitchCompanyMenu", systrayItem, { sequence: 1 });
