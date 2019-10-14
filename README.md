# Odoo12系统集成钉钉  12.0


## 介绍
本项目是一套基于`Odoo`平台的开源的一个集成阿里钉钉应用，主要应用功能包括基础数据同步、考勤数据同步、消息、智能人事等

关于模块名可参照下列表格对应的描述

> 博客： https://sxfblog.com/index.php/archives/371.html
>
> 在使用本模块前，请先将钉钉中你创建的E应用或微应用权限放开和配置出口ip，得到钉钉应用的 **AppKey**和 **AppSecret**， 至于钉钉后台中的配置请参照：>https://open-doc.dingtalk.com/microapp/bgb96b 


## 安装

在安装模块前，务必先安装额外的三方库`（requirements.txt）`文件中，安装方式示例：

 `pip3 install -r $PATH/requirements.txt`  注意$PATH为你的实际路径!


> **特别强调要在运行odoo的python3中安装依赖项**重要事情说三遍
>
> **特别强调要在运行odoo的python3中安装依赖项**重要事情说三遍
>
> **特别强调要在运行odoo的python3中安装依赖项**重要事情说三遍

安装方式，在应用列表中(先刷新模块列表)，搜索`dingding_base`应用，安装即可，安装完成后记得给用户设置权限，否则界面上没有图标

## 模块列表

| 模块名            | 模块功能                                                 |
| ----------------- | ------------------------------------------------------ |
| dingding_attendance         | 钉钉考勤（自动安装）                            |
| dingding_attendance_ext     | 钉钉考勤拓展，支持钉钉考勤导入odoo原生出勤         |
| dingding_base               | 钉钉主模块，一般只需安装这个模块就好了             |
| dingding_hrm                | 钉钉智能人事模块（自动安装）                      |
| dingding_message            | 钉钉消息模块（自动安装）                         |
| oa_base                     | 钉钉审批基础模块（无需安装）                      |
| odoo_interface_api          | 开放第三方接口（供小程序、其他应用调用使用）         |
| odoo_performance_manage     | 绩效管理模块（可独立使用或配合钉钉使用、免费版）     |
| odoo_wage_manage            | 薪酬管理模块（可独立使用或配合钉钉使用、免费版）     |
| web_datepicker              | 第三方日期组件，日期格式为（xxxx年、xxxx年xx月）    |
| web_progress                | 第三方进度条模块（自动依赖模块）                   |
| web_sms_manage              | 集成腾讯云、阿里云短信服务，登录、发送短信           |

## 交流

QQ群：1019231617

## 赞赏

如果你觉得这个项目对你有所帮助，或许你可以资助鼓励一下作者~~ !

**支付宝:**
<p align="center"><img src="https://sxfblog.com/usr/uploads/2019/01/1838323992.png" alt="" style="max-width:50%;" width="200">
</p>

**微信：**

<p align="center">
  <img src="https://sxfblog.com/usr/uploads/2019/01/129181912.png" alt="" style="max-width:50%;" width="200">
</p>
