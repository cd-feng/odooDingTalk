/**
 *    Copyright (C) 2019 SuXueFeng
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or (at your option) any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 **/


let prot = window.location.protocol;
let host = window.location.host;

$(function () {
    $("#sms_check_info").hide();
    //隐藏验证码输入框和按钮
    $("#verification_code_div").hide();
    $("#sms_login_but").hide();
    $("#login_result").hide();
    $("#regain_code").hide();
    $("#send_verification_code").hide();
    console.log("初始化");

    // 初始化滑动验证
    var slider = new SliderUnlock("#slider", {
        successLabelTip: "验证成功"
    }, function () {
        $("#send_verification_code").show();
        $("#label").html("OK");
        $("#slider").css("background-color", "lightgreen");
    });
    slider.init();
});


//点击发送验证码时的方法函数
$("#send_verification_code").click(function (event) {
    $("#sms_check_info").hide();
    // 获取手机号
    let user_phone = $.trim($("#phone").val());
    if (!checkPhoneInfo(user_phone)) {
        $("#sms_check_info").html("非法的手机号码！");
        $("#sms_check_info").show();
        return false;
    }
    $.ajax({
        async: false,
        url: "/web/odoo/send/sms/by/phone",
        data: {"user_phone": user_phone},
        dataType: "json",
        success: function (data) {
            console.log(data);
            if (data.state) {
                $("#send_verification_code").hide(); //隐藏发送验证码按钮
                $("#phone").attr("disabled", "disabled");  // 手机号码框为不可编辑
                // 允许编辑验证码框和登录按钮
                $("#verification_code_div").show();
                $("#sms_login_but").show();
                //显示 未收到验证码按钮
                $("#regain_code").show();
                $("#login_result").html("验证码已发送，请注意查收短信！").show();
            } else {
                $("#login_result").html(data.msg).show();
            }
        },
        error: function (err) {
            $("#sms_check_info").html("发送验证码失败！请稍后重试!").show();
        }
    });
});

// 点击登录按钮执行函数
$("#sms_login_but").click(function (event) {
    $("#login_result").hide();  //隐藏消息框
    $("#sms_check_info").hide();  //隐藏消息框
    let user_phone = $.trim($("#phone").val()); //获取手机号
    let code = $.trim($("#code").val());  //获取验证码
    if (code == null || code == undefined || code == "") {
        $("#sms_check_info").html("请正确输入验证码！").show();
        return false;
    }
    $.ajax({
        async: false,
        url: "/web/check/sms/verification/code",
        data: {"code": code, "phone": user_phone},
        dataType: "json",
        success: function (data) {
            console.log(data);
            if (data.state) {
                window.location.replace(prot + "//" + host + "/web");
            } else {
                $("#sms_check_info").html(data.msg).show();
            }
        },
        error: function (err) {
            $("#sms_check_info").html("服务器内部异常!").show();
        }
    });

});

// 重发验证码
$("#regain_code").click(function (event) {
    $("#login_result").hide();
    $("#sms_check_info").hide();
    let user_phone = $.trim($("#phone").val());
    if (!checkPhoneInfo(user_phone)) {
        $("#sms_check_info").html("非法的手机号码！");
        $("#sms_check_info").show();
        return false;
    }
    $.ajax({
        async: false,
        url: "/web/odoo/send/sms/by/phone",
        data: {"user_phone": user_phone},
        dataType: "json",
        success: function (result) {
            if (result.state) {
                $("#login_result").html("已重新发送验证码，请注意查收短信！").show();
            } else {
                $("#login_result").html(result.msg).show();
            }
        },
        error: function (err) {
            return {"state": false, "msg": "发送验证码失败！请稍后重试!"}
        }
    });
});


// 检查手机号码
function checkPhoneInfo(user_phone) {
    let flag = false;
    let myreg = /^(((13[0-9]{1})|(14[0-9]{1})|(17[0]{1})|(15[0-3]{1})|(15[5-9]{1})|(18[0-9]{1}))+\d{8})$/;
    if (user_phone == null || user_phone == undefined || user_phone == "" || user_phone.length != 11 || !myreg.test(user_phone)) {
        return false;
    } else {
        flag = true;
    }
    return flag;
}

