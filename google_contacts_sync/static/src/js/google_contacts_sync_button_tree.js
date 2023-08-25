odoo.define('google_contacts_sync.google_contacts_sync_button_tree', function (require) {
    "use strict";
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var rpc = require('web.rpc');
    var viewRegistry = require('web.view_registry');
    var TreeButton = ListController.extend({

         buttons_template: 'google_contacts_sync_tree.buttons',
         events: _.extend({}, ListController.prototype.events,
         {
            'click .send_sync_action': '_clickButton',
         }),
       _clickButton: function () {
        rpc.query({
                model: 'res.partner',
                method: 'google_contacts_trigger',
                args: ['self'],
            }).then(function (result) {
                window.open(result)
            })
         },
   });
    var ResPartnerViewList = ListView.extend({
         config: _.extend({}, ListView.prototype.config, {
            Controller: TreeButton,
         }),
    });
    viewRegistry.add('button_in_tree', ResPartnerViewList);
});