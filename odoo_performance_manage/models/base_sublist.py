# -*- coding: utf-8 -*-
from odoo import api
from odoo import fields
from odoo import models
from copy import deepcopy

import collections


class BaseSublist(models.Model):
    _name = 'base.sublist'
    _description = 'Base Sublist Model'
    _ps_sublist_field = ''
    _ps_sublist_model = ''

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """
        重写以支持tree试图sublist列表
        """
        res = super(BaseSublist, self).fields_get(allfields, attributes)

        # 导入的时候不获取sublist字段
        if not self.env.context.get('base_import') and not allfields \
                and self._ps_sublist_field and self._ps_sublist_model:
            line_fields = self.env[self._ps_sublist_model].fields_get()
            for line_field in line_fields:
                line_fields[line_field].update({'sortable': False})
                if 'currency_field' in line_fields[line_field]:
                    line_fields[line_field]['currency_field'] = self._ps_sublist_field + '.' + \
                                                                line_fields[line_field]['currency_field']
            res.update({
                self._ps_sublist_field + '.' + key: value for key, value in list(line_fields.items())
            })
        return res

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """
        重写，一并读出子表中需要展示的字段数据
        """
        if fields:

            # sublist 字段的前缀
            pre_fix = self._ps_sublist_field + '.'

            # 需要展示的sublist字段名
            sublist_fields = [sublist_field for sublist_field in fields if sublist_field.startswith(pre_fix)]

            # 主表读数据之前先清掉sublist字段
            fields = list(set(fields) - set(sublist_fields))

            # 读主表数据
            reads = super(BaseSublist, self).search_read(domain, fields, offset, limit, order)

            res = []
            if sublist_fields:
                # 要读取的子表的字段名（去掉pre_fix前缀）
                line_fields = [line_field.replace(pre_fix, '') for line_field in sublist_fields]

                if line_fields:
                    # 取出要读取的所有子表数据的id
                    line_ids = [line_id for record in reads for line_id in record[self._ps_sublist_field]]

                    # 读子表数据
                    line_records = self.env[self._ps_sublist_model].search_read([('id', 'in', line_ids)], line_fields)

                    # 转成id为键值的字典，方便处理
                    records_dict = {line_record['id']: line_record for line_record in line_records}

                    # 组装数据
                    for res_record in reads:
                        line_records = [{
                            sublist_field: records_dict[line_id][sublist_field.replace(pre_fix, '')] for sublist_field in sublist_fields
                        } for line_id in res_record[self._ps_sublist_field]]

                        # line_records 所有的sublist 数据
                        for line_index, line_record in enumerate(line_records):
                            res_record = deepcopy(res_record)
                            res_record.update(line_record)
                            res_record.update({
                                'record_nrows': len(line_records),
                                'record_rowno': line_index,
                            })
                            res.append(res_record)

                        if len(res_record[self._ps_sublist_field]) == 0:
                            for sublist_field in sublist_fields:
                                res_record[sublist_field] = 0
                            res.append(res_record)
            # 获取相同的ID
            ids = [item for item, count in collections.Counter([record.get('id') for record in res]).items() if count > 1]
            for id in ids:
                i = 0
                for res_dict in res:
                    if id == res_dict.get('id'):
                        if i == 0:
                            i += 1
                        else:
                            # 更新此字典
                            res_dict.update({
                                'amount_untaxed_signed': 0,
                                'residual': 0,
                                'ps_residual_signed': 0,
                            })
            return res or reads
        else:
            return super(BaseSublist, self).search_read(domain, fields, offset, limit, order)
