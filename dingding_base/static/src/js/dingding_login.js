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

function get_decode_url() {
    let url_target = '';
    $.ajax({
        async: false,
        url: "/dingding/login/get_url",
        data: {"local_url": prot + "//" + host},
        success: function (data) {
            url_target = data.encode_url;
        },
        dataType: "json"
    });
    return url_target
}

let url = get_decode_url();
let obj = DDLogin({
    id: "login_container",
    goto: encodeURIComponent(url),
    style: "border:none;background-color:#FFFFFF;",
    href: "",
    width: "260",
    height: "300"
});

let hanndleMessage = function (event) {
    let origin = event.origin;
    if (origin == "https://login.dingtalk.com") { //判断是否来自ddLogin扫码事件。
        let loginTmpCode = event.data;            //拿到loginTmpCode后就可以在这里构造跳转链接进行跳转了
        console.log(">>>:loginTmpCode", loginTmpCode);
        window.location.href = url + "&loginTmpCode=" + loginTmpCode;
    }
};

if (typeof window.addEventListener != 'undefined') {
    window.addEventListener('message', hanndleMessage, false);
} else if (typeof window.attachEvent != 'undefined') {
    window.attachEvent('onmessage', hanndleMessage);
}