odoo.define('google_contacts_sync.google_contacts_sync_button_kanban', function(require) {
   "use strict";
   var KanbanController = require('web.KanbanController');
   var KanbanView = require('web.KanbanView');
   var rpc = require('web.rpc');
   var viewRegistry = require('web.view_registry');
   var KanbanButton = KanbanController.include({
       buttons_template: 'google_contacts_sync_kanban.button',
       events: _.extend({}, KanbanController.prototype.events, {
           'click .send_sync_action': '_clickButton',
       }),
        _clickButton: function () {
            $.ajax({
                url: '/oauth/google/start',
                type: 'GET',
                success: function() {
                   window.location = '/oauth/google/start';
             }
            });
        },
   });
   var ResPartnerKanbanView = KanbanView.extend({
       config: _.extend({}, KanbanView.prototype.config, {
           Controller: KanbanButton
       }),
   });
   viewRegistry.add('button_in_kanban', ResPartnerKanbanView);
});