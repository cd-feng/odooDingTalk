# Odoo12系统集成钉钉  

 注意: 这是odoo12适配odoo13版本钉钉的一个分支，本版本适用于odoo12 EE CE; 若日后升级为odoo13，那么你只需要下载13版本的模块代码直接覆盖即可，数据不会丢失！！！

 操作方式和odoo13的操作方式大致一样，包括菜单位置。操作说明见群文件。所有模块全部采用sdk的方式实现与钉钉服务端的通信


## 本项目不支持多公司，如需使用多公司版本，请跳转至多公司版本

> OdooERP集成钉钉（多公司）：https://github.com/suxuefeng20/OdooDingtalk-MultiCompany


## 介绍
本项目是一套基于`Odoo`平台的开源的一个集成阿里钉钉应用，主要应用功能包括基础数据同步、考勤数据同步、消息、智能人事等


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

安装方式，在应用列表中(先刷新模块列表)，搜索`dingtalk_base`应用，安装即可，安装完成后记得给用户设置权限，否则界面上没有图标

## 模块列表

| 模块名            | 模块功能                                                 |
| ----------------- | ------------------------------------------------------ |
| dingtalk_base         | 基础模块                            |
| dingtalk_hr           | 基础数据、员工、部门、联系人           |
| dingtalk_login        | 账号、密码、扫码以及免登               |
| dingtalk_callback     | 钉钉回调管理                         |
| dingtalk_approval     | 钉钉审批模块                         |
| dingtalk_attendance     | 钉钉考勤模块                         |

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
