==================
Odoo Progress Bar
==================

Progress bar for Odoo waiting screen, possibility to cancel an ongoing operation and a sys tray menu for all operations in progress.

.. class:: no-web

    .. image:: https://raw.githubusercontent.com/gmarczynski/odoo-web-progress/12.0/web_progress/static/description/progress_bar_loading.gif
        :alt: Progress Bar
        :width: 100%
        :align: center


**web_progress** exists for Odoo 11.0 and 12.0 (CE and EE).

Author: Grzegorz Marczyński

License: LGPL-3.

Copyright © 2019 Grzegorz Marczyński

Features
--------

- progress reporting for all standard Odoo import and export operations
- sys tray menu that lists ongoing operations initiated by the logged user (all operations visible to Administrator)
- support for all operations initiated through UI and executed by planned activities (cron)
- generator-like method to simply add progress reporting to any iteration (support for sub-iterations)

For developers
---------------

Typically when your code executes any long-term operation there is a loop over a `collection` in your code.

In order to report progress of the operation, wrap the `collection` with `self.web_progress_iter(collection, msg="Message")`

Say, your operation's main method looks as follows:

.. code-block::

    @api.multi
    def action_operation(self):
        for rec in self:
            rec.do_somethig()


Then a progress-reporting-ready version would be:

.. code-block::

    @api.multi
    def action_operation(self):
        for rec in self.web_progress_iter(self, msg="Message"):
            rec.do_something()


or a simpler version for recordsets:

.. code-block::

    @api.multi
    def action_operation(self):
        for rec in self.with_progress(msg="Message"):
            rec.do_something()

Progress tracking may be added to sub-operations as well:

.. code-block::

    @api.multi
    def action_operation(self):
        for rec in self.with_progress(msg="Message"):
            lines = rec.get_lines()
            for line in lines.with_progress("Sub-operation")
                line.do_something()


