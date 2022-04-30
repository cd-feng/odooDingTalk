# Odoo14系统集成钉钉

## 介绍
本项目是一套基于`Odoo`平台的开源的一个集成阿里钉钉应用，仓库中所有模块均为开源模块，不在仓库中的一些业务模块不再开源。你可联系作者咨询或购买收费版本。

> 博客： https://sxfblog.com/archives/64/
>
> 在使用本模块前，请先将钉钉中你创建的E应用或微应用权限放开和配置出口 **ip**，得到钉钉应用的 **AppKey**和 **AppSecret**， 至于钉钉后台中的配置请参照：>https://open-doc.dingtalk.com/microapp/bgb96b 

本项目是项目成立以来第三次改版了，经过项目实践后，发现目前这个版本是比较合理的。 仓库是按功能模块划分的。 你可以基于dingtalk_base自行拓展其他模块用于你的实际业务。

## 安装

**注：** 若你是基于原来的dingtalk_mc版本升级的话，请先删除掉注册的回调信息，因为新版不在用服务端api进行注册回调，而是利用钉钉提供的应用事件订阅进行回调动作。

在安装模块前，务必先安装额外的三方库`（requirements.txt）`文件中，安装方式示例：

 `pip3 install -r $PATH/requirements.txt`  注意$PATH为你的实际路径!


> **特别强调要在运行odoo的python3中安装依赖项**重要事情说三遍
>
> **特别强调要在运行odoo的python3中安装依赖项**重要事情说三遍
>
> **特别强调要在运行odoo的python3中安装依赖项**重要事情说三遍

## 交流

钉钉群：42198722

## 赞赏

如果你觉得这个项目对你有所帮助，或许你可以资助鼓励一下作者~~ !

**支付宝:**

<p align="center"><img src="https://sxfblog.com/usr/uploads/2020/12/2096443375.jpeg" alt="" style="max-width:50%;" width="200">
</p>

**微信：**

<p align="center">
  <img src="https://sxfblog.com/usr/uploads/2020/12/358378720.jpeg" alt="" style="max-width:50%;" width="200">
</p>

