import logging #line:3:import logging
from odoo import models ,api #line:4:from odoo import models, api
from odoo .exceptions import UserError #line:5:from odoo.exceptions import UserError
from .import dingtalk_api #line:6:from . import dingtalk_api
_O0O0OO0OO00OOO0OO =logging .getLogger (__name__ )#line:8:_logger = logging.getLogger(__name__)
def approval_result (OO0000O00OO0O000O ):#line:11:def approval_result(self):
    ""#line:16:"""
    O0O0OO0OOOOOOO00O =dingtalk_api .check_dingtalk_authorization ('dingtalk_approval')#line:18:result = dingtalk_api.check_dingtalk_authorization('dingtalk_approval')
    if not O0O0OO0OOOOOOO00O ['state']:#line:19:if not result['state']:
        raise UserError (O0O0OO0OOOOOOO00O ['msg'])#line:20:raise UserError(result['msg'])
    O0O0000O00O0O0O00 =OO0000O00OO0O000O .env ['ir.model'].sudo ().search ([('model','=',OO0000O00OO0O000O ._name )]).id #line:22:model_id = self.env['ir.model'].sudo().search([('model', '=', self._name)]).id
    O0O00000OO00OO0OO =OO0000O00OO0O000O .env ['dingtalk.approval.control'].sudo ().search ([('oa_model_id','=',O0O0000O00O0O0O00 )],limit =1 )#line:23:approval = self.env['dingtalk.approval.control'].sudo().search([('oa_model_id', '=', model_id)], limit=1)
    _O0O0OO0OO00OOO0OO .info ("提交'%s'单据至钉钉进行审批..."%O0O00000OO00OO0OO .name )#line:24:_logger.info("提交'%s'单据至钉钉进行审批..." % approval.name)
    OO0O0OO00O0OOOOO0 =O0O00000OO00OO0OO .template_id .process_code #line:26:process_code = approval.template_id.process_code
    O000O0OOO000OOOOO ,O00000O0O0O00O0O0 =get_originator_user_id (OO0000O00OO0O000O )#line:28:user_id, dept_id = get_originator_user_id(self)
    OOOO00O00OOO000O0 =get_form_values (OO0000O00OO0O000O ,O0O00000OO00OO0OO )#line:30:form_values = get_form_values(self, approval)
    _O0O0OO0OO00OOO0OO .info (OOOO00O00OOO000O0 )#line:31:_logger.info(form_values)
    O000O00OO00O00OOO =dingtalk_api .get_client ()#line:33:client = dingtalk_api.get_client()
    try :#line:34:try:
        O0O0OO000O0OO000O ='topapi/processinstance/create'#line:35:url = 'topapi/processinstance/create'
        O0O0OO0OOOOOOO00O =O000O00OO00O00OOO .post (O0O0OO000O0OO000O ,{'process_code':OO0O0OO00O0OOOOO0 ,'originator_user_id':O000O0OOO000OOOOO ,'dept_id':O00000O0O0O00O0O0 ,'form_component_values':OOOO00O00OOO000O0 })#line:41:})
    except Exception as O000OOOO0O0000O00 :#line:42:except Exception as e:
        raise UserError (O000OOOO0O0000O00 )#line:43:raise UserError(e)
    _O0O0OO0OO00OOO0OO .info (O0O0OO0OOOOOOO00O )#line:44:_logger.info(result)
    return O0O0OO0OOOOOOO00O ,O0O00000OO00OO0OO #line:45:return result, approval
def _OO00OOOOO0O000000 (O0OOOO0OOOO00000O ):#line:48:def _commit_dingtalk_approval(self):
    ""#line:53:"""
    O0OOOO0OOOO00000O .ensure_one ()#line:54:self.ensure_one()
    OO00OOO00OO0OOO0O ,O0O0O000O00O0O00O =approval_result (O0OOOO0OOOO00000O )#line:55:result, approval = approval_result(self)
    if OO00OOO00OO0OOO0O .get ('errcode')!=0 :#line:56:if result.get('errcode') != 0:
        raise UserError ('提交审批实例失败，失败原因:{}'.format (OO00OOO00OO0OOO0O .get ('errmsg')))#line:57:raise UserError('提交审批实例失败，失败原因:{}'.format(result.get('errmsg')))
    O0OOOO0OO0OO0O0OO =O0OOOO0OOOO00000O ._name .replace ('.','_')#line:58:model_name = self._name.replace('.', '_')
    OO00OO000000000OO ="""UPDATE {} 
                SET 
                    dd_approval_state='{}', 
                    dd_doc_state='{}', 
                    dd_process_instance='{}' 
                WHERE 
                    id={}""".format (O0OOOO0OO0OO0O0OO ,'approval','等待审批',OO00OOO00OO0OOO0O .get ('process_instance_id'),O0OOOO0OOOO00000O .id )#line:65:id={}""".format(model_name, 'approval', '等待审批', result.get('process_instance_id'), self.id)
    O0OOOO0OOOO00000O ._cr .execute (OO00OO000000000OO )#line:66:self._cr.execute(sql)
    if O0O0O000O00O0O00O .approval_start_function :#line:68:if approval.approval_start_function:
        for O0OO000O0O0OO00O0 in O0O0O000O00O0O00O .approval_start_function .split (','):#line:69:for method in approval.approval_start_function.split(','):
            try :#line:70:try:
                getattr (O0OOOO0OOOO00000O ,O0OO000O0O0OO00O0 )()#line:71:getattr(self, method)()
            except Exception as OOOO0O0O0OO00OO0O :#line:72:except Exception as e:
                _O0O0OO0OO00OOO0OO .info (OOOO0O0O0OO00OO0O )#line:73:_logger.info(e)
    O0OOOO0OOOO00000O .message_post (body =u"提交钉钉成功，请等待审批人进行审批！",message_type ='notification')#line:74:self.message_post(body=u"提交钉钉成功，请等待审批人进行审批！", message_type='notification')
    return True #line:75:return True
Model =models .Model #line:78:Model = models.Model
setattr (Model ,'commit_dingtalk_approval',_OO00OOOOO0O000000 )#line:79:setattr(Model, 'commit_dingtalk_approval', _commit_dingtalk_approval)
def get_form_values (O0O00O0OO0OOOO0OO ,OOOO00000O0OOOOOO ):#line:82:def get_form_values(self, approval):
    ""#line:88:"""
    OOOO00OO000OO0O0O =list ()#line:89:fcv_list = list()
    for OOOOO0O0OOOOO0O0O in OOOO00000O0OOOOOO .line_ids :#line:90:for line in approval.line_ids:
        if OOOOO0O0OOOOO0O0O .ttype =='many2one':#line:92:if line.ttype == 'many2one':
            O0OOO0O0OO0OO000O =O0O00O0OO0OOOO0OO [OOOOO0O0OOOOO0O0O .field_id .name ]#line:93:ding_field = self[line.field_id.name]
            if OOOOO0O0OOOOO0O0O .is_dd_id :#line:94:if line.is_dd_id:
                OOOO00OO000OO0O0O .append ({'name':OOOOO0O0OOOOO0O0O .dd_field ,'value':[O0OOO0O0OO0OO000O .ding_id ]})#line:95:fcv_list.append({'name': line.dd_field, 'value': [ding_field.ding_id]})
            else :#line:96:else:
                OOOO00OO000OO0O0O .append ({'name':OOOOO0O0OOOOO0O0O .dd_field ,'value':O0OOO0O0OO0OO000O .name })#line:97:fcv_list.append({'name': line.dd_field, 'value': ding_field.name})
        elif OOOOO0O0OOOOO0O0O .ttype =='many2many':#line:99:elif line.ttype == 'many2many':
            O0O0OOOO0OO0000OO =O0O00O0OO0OOOO0OO [OOOOO0O0OOOOO0O0O .field_id .name ]#line:100:many_models = self[line.field_id.name]
            O0000OOO0OO0O00O0 =list ()#line:101:line_list = list()
            for O00O000OOOO000O00 in O0O0OOOO0OO0000OO :#line:102:for many_model in many_models:
                if OOOOO0O0OOOOO0O0O .is_dd_id :#line:104:if line.is_dd_id:
                    O0000OOO0OO0O00O0 .append (O00O000OOOO000O00 .ding_id )#line:105:line_list.append(many_model.ding_id)
                else :#line:106:else:
                    O0000OOO0OO0O00O0 .append (O00O000OOOO000O00 .name )#line:107:line_list.append(many_model.name)
            OOOO00OO000OO0O0O .append ({'name':OOOOO0O0OOOOO0O0O .dd_field ,'value':O0000OOO0OO0O00O0 })#line:108:fcv_list.append({'name': line.dd_field, 'value': line_list})
        elif OOOOO0O0OOOOO0O0O .ttype =='date':#line:110:elif line.ttype == 'date':
            OOOO00OO000OO0O0O .append ({'name':OOOOO0O0OOOOO0O0O .dd_field ,'value':O0O00O0OO0OOOO0OO [OOOOO0O0OOOOO0O0O .field_id .name ].strftime ('%Y-%m-%d')})#line:111:fcv_list.append({'name': line.dd_field, 'value': self[line.field_id.name].strftime('%Y-%m-%d')})
        elif OOOOO0O0OOOOO0O0O .ttype =='datetime':#line:113:elif line.ttype == 'datetime':
            OOOO00OO000OO0O0O .append ({'name':OOOOO0O0OOOOO0O0O .dd_field ,'value':O0O00O0OO0OOOO0OO [OOOOO0O0OOOOO0O0O .field_id .name ].strftime ('%Y-%m-%d %H:%M')})#line:114:fcv_list.append({'name': line.dd_field, 'value': self[line.field_id.name].strftime('%Y-%m-%d %H:%M')})
        elif OOOOO0O0OOOOO0O0O .ttype in ['char','text','integer','float','monetary','selection']:#line:116:elif line.ttype in ['char', 'text', 'integer', 'float', 'monetary', 'selection']:
            OOOO00OO000OO0O0O .append ({'name':OOOOO0O0OOOOO0O0O .dd_field ,'value':O0O00O0OO0OOOO0OO [OOOOO0O0OOOOO0O0O .field_id .name ]})#line:117:fcv_list.append({'name': line.dd_field, 'value': self[line.field_id.name]})
        elif OOOOO0O0OOOOO0O0O .ttype =='one2many':#line:119:elif line.ttype == 'one2many':
            OOO0000O0OO0O0OO0 =O0O00O0OO0OOOO0OO [OOOOO0O0OOOOO0O0O .field_id .name ]#line:120:model_lines = self[line.field_id.name]
            OOO00OO0OO0000O0O =list ()#line:121:fcv_line = list()   # 子表容器列表
            for OO00O00O0O000OOOO in OOO0000O0OO0O0OO0 :#line:122:for model_line in model_lines:      # 遍历对象示例列表
                O00O0O0O0O0OOOO0O =list ()#line:123:fcv_line_list = list()
                for O0O00OO000OO00OO0 in OOOOO0O0OOOOO0O0O .list_ids :#line:124:for list_id in line.list_ids:   # 遍历配置项中的字段列表字段
                    if O0O00OO000OO00OO0 .field_id .ttype =='many2one':#line:126:if list_id.field_id.ttype == 'many2one':
                        OO00OOO00000O00O0 =OO00O00O0O000OOOO [O0O00OO000OO00OO0 .field_id .name ]#line:127:list_ding_field = model_line[list_id.field_id.name]
                        if O0O00OO000OO00OO0 .is_dd_id :#line:128:if list_id.is_dd_id:
                            O00O0O0O0O0OOOO0O .append ({'name':O0O00OO000OO00OO0 .dd_field ,'value':[OO00OOO00000O00O0 .ding_id ]})#line:129:fcv_line_list.append({'name': list_id.dd_field, 'value': [list_ding_field.ding_id]})
                        else :#line:130:else:
                            O00O0O0O0O0OOOO0O .append ({'name':O0O00OO000OO00OO0 .dd_field ,'value':OO00OOO00000O00O0 .name })#line:131:fcv_line_list.append({'name': list_id.dd_field, 'value': list_ding_field.name})
                    elif O0O00OO000OO00OO0 .field_id .ttype =='many2many':#line:133:elif list_id.field_id.ttype == 'many2many':
                        OO00O0O00O00OO0OO =OO00O00O0O000OOOO [O0O00OO000OO00OO0 .field_id .name ]#line:134:list_id_models = model_line[list_id.field_id.name]
                        O00OO0OO0OOO00000 =list ()#line:135:field_list = list()
                        for OO0000OO0OO0000O0 in OO00O0O00O00OO0OO :#line:136:for list_id_model in list_id_models:
                            if O0O00OO000OO00OO0 .is_dd_id :#line:138:if list_id.is_dd_id:
                                O00OO0OO0OOO00000 .append (OO0000OO0OO0000O0 .ding_id )#line:139:field_list.append(list_id_model.ding_id)
                            else :#line:140:else:
                                O00OO0OO0OOO00000 .append (OO0000OO0OO0000O0 .name )#line:141:field_list.append(list_id_model.name)
                        O00O0O0O0O0OOOO0O .append ({'name':O0O00OO000OO00OO0 .dd_field ,'value':O00OO0OO0OOO00000 })#line:142:fcv_line_list.append({'name': list_id.dd_field, 'value': field_list})
                    elif O0O00OO000OO00OO0 .field_id .ttype =='date':#line:144:elif list_id.field_id.ttype == 'date':
                        O00O0O0O0O0OOOO0O .append ({'name':O0O00OO000OO00OO0 .dd_field ,'value':OO00O00O0O000OOOO [O0O00OO000OO00OO0 .field_id .name ].strftime ('%Y-%m-%d')})#line:145:fcv_line_list.append({'name': list_id.dd_field, 'value': model_line[list_id.field_id.name].strftime('%Y-%m-%d')})
                    elif O0O00OO000OO00OO0 .field_id .ttype =='datetime':#line:147:elif list_id.field_id.ttype == 'datetime':
                        O00O0O0O0O0OOOO0O .append ({'name':O0O00OO000OO00OO0 .dd_field ,'value':OO00O00O0O000OOOO [O0O00OO000OO00OO0 .field_id .name ].strftime ('%Y-%m-%d %H:%M')})#line:148:fcv_line_list.append({'name': list_id.dd_field, 'value': model_line[list_id.field_id.name].strftime('%Y-%m-%d %H:%M')})
                    elif O0O00OO000OO00OO0 .field_id .ttype in ['char','text','integer','float','monetary','selection']:#line:150:elif list_id.field_id.ttype in ['char', 'text', 'integer', 'float', 'monetary', 'selection']:
                        O00O0O0O0O0OOOO0O .append ({'name':O0O00OO000OO00OO0 .dd_field ,'value':OO00O00O0O000OOOO [O0O00OO000OO00OO0 .field_id .name ]})#line:151:fcv_line_list.append({'name': list_id.dd_field, 'value': model_line[list_id.field_id.name]})
                OOO00OO0OO0000O0O .append (O00O0O0O0O0OOOO0O )#line:152:fcv_line.append(fcv_line_list)
            OOOO00OO000OO0O0O .append ({'name':OOOOO0O0OOOOO0O0O .dd_field ,'value':OOO00OO0OO0000O0O })#line:153:fcv_list.append({'name': line.dd_field, 'value': fcv_line})
    return OOOO00OO000OO0O0O #line:154:return fcv_list
def get_originator_user_id (OOO00O0O00OOO0OO0 ):#line:157:def get_originator_user_id(self):
    ""#line:162:"""
    O0OOOO000O00O00OO =OOO00O0O00OOO0OO0 .env ['hr.employee'].search ([('user_id','=',OOO00O0O00OOO0OO0 .env .user .id )],limit =1 )#line:163:emp = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
    if not O0OOOO000O00O00OO :#line:164:if not emp:
        raise UserError ("当前登录用户无对应员工，请使用员工账号登录系统再发起审批。  *_*!!")#line:165:raise UserError("当前登录用户无对应员工，请使用员工账号登录系统再发起审批。  *_*!!")
    if not O0OOOO000O00O00OO .ding_id :#line:166:if not emp.ding_id:
        raise UserError ("当前员工{}不存在钉钉ID，请使用钉钉下的员工进行提交,或则先将员工上传至钉钉后在操作。  *_*!!".format (O0OOOO000O00O00OO .name ))#line:167:raise UserError("当前员工{}不存在钉钉ID，请使用钉钉下的员工进行提交,或则先将员工上传至钉钉后在操作。  *_*!!".format(emp.name))
    if not O0OOOO000O00O00OO .department_id :#line:168:if not emp.department_id:
        raise UserError ("当前员工{}不存在钉钉部门，请维护后再发起审批。  *_*!!".format (O0OOOO000O00O00OO .name ))#line:169:raise UserError("当前员工{}不存在钉钉部门，请维护后再发起审批。  *_*!!".format(emp.name))
    if not O0OOOO000O00O00OO .department_id .ding_id :#line:170:if not emp.department_id.ding_id:
        raise UserError ("当前员工{}的部门{}不存在钉钉ID，请注意更正。  *_*!!".format (O0OOOO000O00O00OO .name ,O0OOOO000O00O00OO .department_id .name ))#line:171:raise UserError("当前员工{}的部门{}不存在钉钉ID，请注意更正。  *_*!!".format(emp.name, emp.department_id.name))
    return O0OOOO000O00O00OO .ding_id ,O0OOOO000O00O00OO .department_id .ding_id #line:172:return emp.ding_id, emp.department_id.ding_id
def _OO0OOOO00000OOOOO (OO0OOOOO0O000O00O ):#line:175:def _restart_commit_approval(self):
    ""#line:180:"""
    OO0OOOOO0O000O00O .ensure_one ()#line:181:self.ensure_one()
    O0000O00O00OO00O0 ,O00O00O0O00O0O0O0 =approval_result (OO0OOOOO0O000O00O )#line:182:result, approval = approval_result(self)
    if O0000O00O00OO00O0 .get ('errcode')!=0 :#line:183:if result.get('errcode') != 0:
        raise UserError ('重新提交失败，失败原因:{}'.format (O0000O00O00OO00O0 .get ('errmsg')))#line:184:raise UserError('重新提交失败，失败原因:{}'.format(result.get('errmsg')))
    OO0O00O0OO0O0000O =OO0OOOOO0O000O00O ._name .replace ('.','_')#line:185:model_name = self._name.replace('.', '_')
    OOO0O00000O000OO0 ="""UPDATE {} 
             SET 
                 dd_approval_state='{}', 
                 dd_doc_state='{}', 
                 dd_approval_result='load', 
                 dd_process_instance='{}' 
             WHERE 
                 id={}""".format (OO0O00O0OO0O0000O ,'approval','重新提交审批',O0000O00O00OO00O0 .get ('process_instance_id'),OO0OOOOO0O000O00O .id )#line:193:id={}""".format(model_name, 'approval', '重新提交审批', result.get('process_instance_id'), self.id)
    OO0OOOOO0O000O00O ._cr .execute (OOO0O00000O000OO0 )#line:194:self._cr.execute(sql)
    OO0OOOOO0O000O00O .message_post (body =u"已重新提交，请等待审批人审批！",message_type ='notification')#line:195:self.message_post(body=u"已重新提交，请等待审批人审批！", message_type='notification')
    return True #line:196:return True
setattr (Model ,'restart_commit_approval',_OO0OOOO00000OOOOO )#line:199:setattr(Model, 'restart_commit_approval', _restart_commit_approval)
