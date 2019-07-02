# -*- coding: utf-8 -*-

from . import models
from . import wizard

def uninstall_hook(cr, registry):
    cr.execute(
        "DELETE FROM ir_config_parameter WHERE key like 'ali_dindin%'"
    )