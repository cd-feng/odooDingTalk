import logging #line:3:import logging
from odoo import models ,api #line:4:from odoo import models, api
from odoo .exceptions import UserError #line:5:from odoo.exceptions import UserError
from .import dingtalk_api #line:6:from . import dingtalk_api
_OOO0O0000O0OOO0O0 =logging .getLogger (__name__ )#line:8:_logger = logging.getLogger(__name__)
def approval_result (OO00OO000O000OOO0 ):#line:11:def approval_result(self):
    ""#line:16:"""
    O00000OO0O0OO00OO =dingtalk_api .check_dingtalk_authorization ('dingtalk_approval')#line:18:result = dingtalk_api.check_dingtalk_authorization('dingtalk_approval')
    if not O00000OO0O0OO00OO ['state']:#line:19:if not result['state']:
        raise UserError (O00000OO0O0OO00OO ['msg'])#line:20:raise UserError(result['msg'])
    O0O0OO0O0O0O0O00O =OO00OO000O000OOO0 .env ['ir.model'].sudo ().search ([('model','=',OO00OO000O000OOO0 ._name )]).id #line:22:model_id = self.env['ir.model'].sudo().search([('model', '=', self._name)]).id
    O00OO0O00O000OOO0 =OO00OO000O000OOO0 .env ['dingtalk.approval.control'].sudo ().search ([('oa_model_id','=',O0O0OO0O0O0O0O00O )],limit =1 )#line:23:approval = self.env['dingtalk.approval.control'].sudo().search([('oa_model_id', '=', model_id)], limit=1)
    _OOO0O0000O0OOO0O0 .info ("提交'%s'单据至钉钉进行审批..."%O00OO0O00O000OOO0 .name )#line:24:_logger.info("提交'%s'单据至钉钉进行审批..." % approval.name)
    OOO00OO0OO0000000 =O00OO0O00O000OOO0 .template_id .process_code #line:26:process_code = approval.template_id.process_code
    O000OO0O00O000O00 ,O0O0000000O00000O =get_originator_user_id (OO00OO000O000OOO0 )#line:28:user_id, dept_id = get_originator_user_id(self)
    O0OO0OOOO000O0OOO =get_form_values (OO00OO000O000OOO0 ,O00OO0O00O000OOO0 )#line:30:form_values = get_form_values(self, approval)
    _OOO0O0000O0OOO0O0 .info (O0OO0OOOO000O0OOO )#line:31:_logger.info(form_values)
    O00OOOOOO00000OOO =dingtalk_api .get_client ()#line:33:client = dingtalk_api.get_client()
    try :#line:34:try:
        O0O00OOO00O00OOO0 ='topapi/processinstance/create'#line:35:url = 'topapi/processinstance/create'
        O00000OO0O0OO00OO =O00OOOOOO00000OOO .post (O0O00OOO00O00OOO0 ,{'process_code':OOO00OO0OO0000000 ,'originator_user_id':O000OO0O00O000O00 ,'dept_id':O0O0000000O00000O ,'form_component_values':O0OO0OOOO000O0OOO })#line:41:})
    except Exception as O0OO0OOO00OOOOOO0 :#line:42:except Exception as e:
        raise UserError (O0OO0OOO00OOOOOO0 )#line:43:raise UserError(e)
    _OOO0O0000O0OOO0O0 .info (O00000OO0O0OO00OO )#line:44:_logger.info(result)
    return O00000OO0O0OO00OO ,O00OO0O00O000OOO0 #line:45:return result, approval
def _O0O00O00OO00OO0OO (O0OOO00OO0OO00OO0 ):#line:48:def _commit_dingtalk_approval(self):
    ""#line:53:"""
    O0OOO00OO0OO00OO0 .ensure_one ()#line:54:self.ensure_one()
    OO0O000000OO0O00O ,OO00000O0O0O0O00O =approval_result (O0OOO00OO0OO00OO0 )#line:55:result, approval = approval_result(self)
    if OO0O000000OO0O00O .get ('errcode')!=0 :#line:56:if result.get('errcode') != 0:
        raise UserError ('提交审批实例失败，失败原因:{}'.format (OO0O000000OO0O00O .get ('errmsg')))#line:57:raise UserError('提交审批实例失败，失败原因:{}'.format(result.get('errmsg')))
    OOO0000000000OOOO =O0OOO00OO0OO00OO0 ._name .replace ('.','_')#line:58:model_name = self._name.replace('.', '_')
    O0OOO0O00O000000O ="""UPDATE {} 
                SET 
                    dd_approval_state='{}', 
                    dd_doc_state='{}', 
                    dd_process_instance='{}' 
                WHERE 
                    id={}""".format (OOO0000000000OOOO ,'approval','等待审批',OO0O000000OO0O00O .get ('process_instance_id'),O0OOO00OO0OO00OO0 .id )#line:65:id={}""".format(model_name, 'approval', '等待审批', result.get('process_instance_id'), self.id)
    O0OOO00OO0OO00OO0 ._cr .execute (O0OOO0O00O000000O )#line:66:self._cr.execute(sql)
    if OO00000O0O0O0O00O .approval_start_function :#line:68:if approval.approval_start_function:
        for OOOO0O0O00OO0OOOO in OO00000O0O0O0O00O .approval_start_function .split (','):#line:69:for method in approval.approval_start_function.split(','):
            try :#line:70:try:
                getattr (O0OOO00OO0OO00OO0 ,OOOO0O0O00OO0OOOO )()#line:71:getattr(self, method)()
            except Exception as O00OOOO000000000O :#line:72:except Exception as e:
                _OOO0O0000O0OOO0O0 .info (O00OOOO000000000O )#line:73:_logger.info(e)
    O0OOO00OO0OO00OO0 .message_post (body =u"提交钉钉成功，请等待审批人进行审批！",message_type ='notification')#line:74:self.message_post(body=u"提交钉钉成功，请等待审批人进行审批！", message_type='notification')
    return True #line:75:return True
Model =models .Model #line:78:Model = models.Model
setattr (Model ,'commit_dingtalk_approval',_O0O00O00OO00OO0OO )#line:79:setattr(Model, 'commit_dingtalk_approval', _commit_dingtalk_approval)
def get_form_values (OO0O00000O00OOOO0 ,O0000O0O000O000OO ):#line:82:def get_form_values(self, approval):
    ""#line:88:"""
    O0OO0OO000OOO0OO0 =list ()#line:89:fcv_list = list()
    for O00OOO00O0O0OOO00 in O0000O0O000O000OO .line_ids :#line:90:for line in approval.line_ids:
        if O00OOO00O0O0OOO00 .ttype =='many2one':#line:92:if line.ttype == 'many2one':
            O00O000O0OO0O0OOO =OO0O00000O00OOOO0 [O00OOO00O0O0OOO00 .field_id .name ]#line:93:ding_field = self[line.field_id.name]
            if O00OOO00O0O0OOO00 .is_dd_id :#line:94:if line.is_dd_id:
                O0OO0OO000OOO0OO0 .append ({'name':O00OOO00O0O0OOO00 .dd_field ,'value':[O00O000O0OO0O0OOO .ding_id ]})#line:95:fcv_list.append({'name': line.dd_field, 'value': [ding_field.ding_id]})
            else :#line:96:else:
                O0OO0OO000OOO0OO0 .append ({'name':O00OOO00O0O0OOO00 .dd_field ,'value':O00O000O0OO0O0OOO .name })#line:97:fcv_list.append({'name': line.dd_field, 'value': ding_field.name})
        elif O00OOO00O0O0OOO00 .ttype =='many2many':#line:99:elif line.ttype == 'many2many':
            OO0O00O00000O00O0 =OO0O00000O00OOOO0 [O00OOO00O0O0OOO00 .field_id .name ]#line:100:many_models = self[line.field_id.name]
            O0000OOO0000000O0 =list ()#line:101:line_list = list()
            for O0OO0OO0O00O000OO in OO0O00O00000O00O0 :#line:102:for many_model in many_models:
                if O00OOO00O0O0OOO00 .is_dd_id :#line:104:if line.is_dd_id:
                    O0000OOO0000000O0 .append (O0OO0OO0O00O000OO .ding_id )#line:105:line_list.append(many_model.ding_id)
                else :#line:106:else:
                    O0000OOO0000000O0 .append (O0OO0OO0O00O000OO .name )#line:107:line_list.append(many_model.name)
            O0OO0OO000OOO0OO0 .append ({'name':O00OOO00O0O0OOO00 .dd_field ,'value':O0000OOO0000000O0 })#line:108:fcv_list.append({'name': line.dd_field, 'value': line_list})
        elif O00OOO00O0O0OOO00 .ttype =='date':#line:110:elif line.ttype == 'date':
            O0OO0OO000OOO0OO0 .append ({'name':O00OOO00O0O0OOO00 .dd_field ,'value':OO0O00000O00OOOO0 [O00OOO00O0O0OOO00 .field_id .name ].strftime ('%Y-%m-%d')})#line:111:fcv_list.append({'name': line.dd_field, 'value': self[line.field_id.name].strftime('%Y-%m-%d')})
        elif O00OOO00O0O0OOO00 .ttype =='datetime':#line:113:elif line.ttype == 'datetime':
            O0OO0OO000OOO0OO0 .append ({'name':O00OOO00O0O0OOO00 .dd_field ,'value':OO0O00000O00OOOO0 [O00OOO00O0O0OOO00 .field_id .name ].strftime ('%Y-%m-%d %H:%M')})#line:114:fcv_list.append({'name': line.dd_field, 'value': self[line.field_id.name].strftime('%Y-%m-%d %H:%M')})
        elif O00OOO00O0O0OOO00 .ttype in ['char','text','integer','float','monetary','selection']:#line:116:elif line.ttype in ['char', 'text', 'integer', 'float', 'monetary', 'selection']:
            O0OO0OO000OOO0OO0 .append ({'name':O00OOO00O0O0OOO00 .dd_field ,'value':OO0O00000O00OOOO0 [O00OOO00O0O0OOO00 .field_id .name ]})#line:117:fcv_list.append({'name': line.dd_field, 'value': self[line.field_id.name]})
        elif O00OOO00O0O0OOO00 .ttype =='one2many':#line:119:elif line.ttype == 'one2many':
            OO0OO0OO0O0000OOO =OO0O00000O00OOOO0 [O00OOO00O0O0OOO00 .field_id .name ]#line:120:model_lines = self[line.field_id.name]
            O000000OOO0OO000O =list ()#line:121:fcv_line = list()   # 子表容器列表
            for O0O0O0O000O000000 in OO0OO0OO0O0000OOO :#line:122:for model_line in model_lines:      # 遍历对象示例列表
                OOOO0O00OO0OOOOO0 =list ()#line:123:fcv_line_list = list()
                for OOOOO00O0OOOOO00O in O00OOO00O0O0OOO00 .list_ids :#line:124:for list_id in line.list_ids:   # 遍历配置项中的字段列表字段
                    if OOOOO00O0OOOOO00O .field_id .ttype =='many2one':#line:126:if list_id.field_id.ttype == 'many2one':
                        OOO0O0O0OO00OO000 =O0O0O0O000O000000 [OOOOO00O0OOOOO00O .field_id .name ]#line:127:list_ding_field = model_line[list_id.field_id.name]
                        if OOOOO00O0OOOOO00O .is_dd_id :#line:128:if list_id.is_dd_id:
                            OOOO0O00OO0OOOOO0 .append ({'name':OOOOO00O0OOOOO00O .dd_field ,'value':[OOO0O0O0OO00OO000 .ding_id ]})#line:129:fcv_line_list.append({'name': list_id.dd_field, 'value': [list_ding_field.ding_id]})
                        else :#line:130:else:
                            OOOO0O00OO0OOOOO0 .append ({'name':OOOOO00O0OOOOO00O .dd_field ,'value':OOO0O0O0OO00OO000 .name })#line:131:fcv_line_list.append({'name': list_id.dd_field, 'value': list_ding_field.name})
                    elif OOOOO00O0OOOOO00O .field_id .ttype =='many2many':#line:133:elif list_id.field_id.ttype == 'many2many':
                        O00O00000OOO00O0O =O0O0O0O000O000000 [OOOOO00O0OOOOO00O .field_id .name ]#line:134:list_id_models = model_line[list_id.field_id.name]
                        OO00O0O00O0OO000O =list ()#line:135:field_list = list()
                        for OOO0OO0OOOO0O0O00 in O00O00000OOO00O0O :#line:136:for list_id_model in list_id_models:
                            if OOOOO00O0OOOOO00O .is_dd_id :#line:138:if list_id.is_dd_id:
                                OO00O0O00O0OO000O .append (OOO0OO0OOOO0O0O00 .ding_id )#line:139:field_list.append(list_id_model.ding_id)
                            else :#line:140:else:
                                OO00O0O00O0OO000O .append (OOO0OO0OOOO0O0O00 .name )#line:141:field_list.append(list_id_model.name)
                        OOOO0O00OO0OOOOO0 .append ({'name':OOOOO00O0OOOOO00O .dd_field ,'value':OO00O0O00O0OO000O })#line:142:fcv_line_list.append({'name': list_id.dd_field, 'value': field_list})
                    elif OOOOO00O0OOOOO00O .field_id .ttype =='date':#line:144:elif list_id.field_id.ttype == 'date':
                        OOOO0O00OO0OOOOO0 .append ({'name':OOOOO00O0OOOOO00O .dd_field ,'value':O0O0O0O000O000000 [OOOOO00O0OOOOO00O .field_id .name ].strftime ('%Y-%m-%d')})#line:145:fcv_line_list.append({'name': list_id.dd_field, 'value': model_line[list_id.field_id.name].strftime('%Y-%m-%d')})
                    elif OOOOO00O0OOOOO00O .field_id .ttype =='datetime':#line:147:elif list_id.field_id.ttype == 'datetime':
                        OOOO0O00OO0OOOOO0 .append ({'name':OOOOO00O0OOOOO00O .dd_field ,'value':O0O0O0O000O000000 [OOOOO00O0OOOOO00O .field_id .name ].strftime ('%Y-%m-%d %H:%M')})#line:148:fcv_line_list.append({'name': list_id.dd_field, 'value': model_line[list_id.field_id.name].strftime('%Y-%m-%d %H:%M')})
                    elif OOOOO00O0OOOOO00O .field_id .ttype in ['char','text','integer','float','monetary','selection']:#line:150:elif list_id.field_id.ttype in ['char', 'text', 'integer', 'float', 'monetary', 'selection']:
                        OOOO0O00OO0OOOOO0 .append ({'name':OOOOO00O0OOOOO00O .dd_field ,'value':O0O0O0O000O000000 [OOOOO00O0OOOOO00O .field_id .name ]})#line:151:fcv_line_list.append({'name': list_id.dd_field, 'value': model_line[list_id.field_id.name]})
                O000000OOO0OO000O .append (OOOO0O00OO0OOOOO0 )#line:152:fcv_line.append(fcv_line_list)
            O0OO0OO000OOO0OO0 .append ({'name':O00OOO00O0O0OOO00 .dd_field ,'value':O000000OOO0OO000O })#line:153:fcv_list.append({'name': line.dd_field, 'value': fcv_line})
    return O0OO0OO000OOO0OO0 #line:154:return fcv_list
def get_originator_user_id (OOO0OOOOO00OOO00O ):#line:157:def get_originator_user_id(self):
    ""#line:162:"""
    O000O0OO0OO000OO0 =OOO0OOOOO00OOO00O .env ['hr.employee'].search ([('user_id','=',OOO0OOOOO00OOO00O .env .user .id )],limit =1 )#line:163:emp = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
    if not O000O0OO0OO000OO0 :#line:164:if not emp:
        raise UserError ("当前登录用户无对应员工，请使用员工账号登录系统再发起审批。  *_*!!")#line:165:raise UserError("当前登录用户无对应员工，请使用员工账号登录系统再发起审批。  *_*!!")
    if not O000O0OO0OO000OO0 .ding_id :#line:166:if not emp.ding_id:
        raise UserError ("当前员工{}不存在钉钉ID，请使用钉钉下的员工进行提交,或则先将员工上传至钉钉后在操作。  *_*!!".format (O000O0OO0OO000OO0 .name ))#line:167:raise UserError("当前员工{}不存在钉钉ID，请使用钉钉下的员工进行提交,或则先将员工上传至钉钉后在操作。  *_*!!".format(emp.name))
    if not O000O0OO0OO000OO0 .department_id :#line:168:if not emp.department_id:
        raise UserError ("当前员工{}不存在钉钉部门，请维护后再发起审批。  *_*!!".format (O000O0OO0OO000OO0 .name ))#line:169:raise UserError("当前员工{}不存在钉钉部门，请维护后再发起审批。  *_*!!".format(emp.name))
    if not O000O0OO0OO000OO0 .department_id .ding_id :#line:170:if not emp.department_id.ding_id:
        raise UserError ("当前员工{}的部门{}不存在钉钉ID，请注意更正。  *_*!!".format (O000O0OO0OO000OO0 .name ,O000O0OO0OO000OO0 .department_id .name ))#line:171:raise UserError("当前员工{}的部门{}不存在钉钉ID，请注意更正。  *_*!!".format(emp.name, emp.department_id.name))
    return O000O0OO0OO000OO0 .ding_id ,O000O0OO0OO000OO0 .department_id .ding_id #line:172:return emp.ding_id, emp.department_id.ding_id
def _O0O0OO0OOOOO00OOO (O0O000000OOOOOO00 ):#line:175:def _restart_commit_approval(self):
    ""#line:180:"""
    O0O000000OOOOOO00 .ensure_one ()#line:181:self.ensure_one()
    O0O0O000OOOO0O000 ,O000OO000O0OOOO0O =approval_result (O0O000000OOOOOO00 )#line:182:result, approval = approval_result(self)
    if O0O0O000OOOO0O000 .get ('errcode')!=0 :#line:183:if result.get('errcode') != 0:
        raise UserError ('重新提交失败，失败原因:{}'.format (O0O0O000OOOO0O000 .get ('errmsg')))#line:184:raise UserError('重新提交失败，失败原因:{}'.format(result.get('errmsg')))
    O000000OOO0000O0O =O0O000000OOOOOO00 ._name .replace ('.','_')#line:185:model_name = self._name.replace('.', '_')
    OO000O0OO0OO0OO00 ="""UPDATE {} 
             SET 
                 dd_approval_state='{}', 
                 dd_doc_state='{}', 
                 dd_approval_result='load', 
                 dd_process_instance='{}' 
             WHERE 
                 id={}""".format (O000000OOO0000O0O ,'approval','重新提交审批',O0O0O000OOOO0O000 .get ('process_instance_id'),O0O000000OOOOOO00 .id )#line:193:id={}""".format(model_name, 'approval', '重新提交审批', result.get('process_instance_id'), self.id)
    O0O000000OOOOOO00 ._cr .execute (OO000O0OO0OO0OO00 )#line:194:self._cr.execute(sql)
    O0O000000OOOOOO00 .message_post (body =u"已重新提交，请等待审批人审批！",message_type ='notification')#line:195:self.message_post(body=u"已重新提交，请等待审批人审批！", message_type='notification')
    return True #line:196:return True
setattr (Model ,'restart_commit_approval',_O0O0OO0OOOOO00OOO )#line:199:setattr(Model, 'restart_commit_approval', _restart_commit_approval)
