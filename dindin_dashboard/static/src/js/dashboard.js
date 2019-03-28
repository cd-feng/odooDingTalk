odoo.define('dindin.blackboard.info', function (require) {
    "use strict";

    let AbstractAction = require('web.AbstractAction');
    let core = require('web.core');
    let DinDinDashboard = AbstractAction.extend({
        template: 'DindinDashboardInfo',
        start: function () {
            // alert('1212');
        }

    });


    core.action_registry.add('dindin_dashboard', DinDinDashboard);
    return DinDinDashboard;


});