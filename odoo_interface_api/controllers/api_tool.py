# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

from odoo.http import request


def check_api_access(app_id):
    """
    验证外部appid在本系统中是否允许访问
    :param app_id: appid
    :return:  boolean
    """
    if not app_id:
        return False
    result = request.env['api.alow.access'].sudo().search([('app_id', '=', app_id), ('active', '=', True)], limit=1)
    return False if not result else True


def create_employee_data(employee):
    """
    返回员工dict类型
    :param employee:
    :return:
    """
    return {
        'name': employee.name,
        'id': employee.id,
    }

