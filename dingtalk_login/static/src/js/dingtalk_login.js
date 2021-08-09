let prot = window.location.protocol;
let host = window.location.host;

$(function(){
    $.ajax({
        async: true,
        url: "/web/dingtalk/get/companys",
        dataType:'json',
        success: function (data) {
            let company_list = data['company_list']
            if (company_list.length == 0){
                $("#env_company").append("<option value='no'>没有设置登录公司</option>");
            }
            else if (company_list.length == 1){
                let company = company_list[0]
                $("#env_company").append("<option value="+company['id']+ ">"+ company['name'] + "</option>")
                // 加载二维码
                let url_target = get_decode_url(company['id']);
                if(url_target){
                    addDDLogin(url_target);
                }
            }else {
                let first_company = company_list[0]
                for(let x=0; x < company_list.length; x++) {
                    let company = company_list[x]
                    $("#env_company").append("<option value="+company['id']+ ">"+ company['name'] + "</option>")
                }
                // 加载二维码
                let url_target = get_decode_url(first_company['id']);
                if (url_target) {
                    addDDLogin(url_target);
                }
            }
        },
    });

    $('#env_company').change(function(){
        let company_val = $(this).children('option:selected').val();
        if(company_val === 'no'){
            return false;
        }
        // 加载二维码
        let url_target = get_decode_url(company_val);
        if(url_target){
            addDDLogin(url_target);
        }
        return false;
    });
});

function addDDLogin(url_target){
    let obj = DDLogin({
        id: "login_container",
        goto: encodeURIComponent(url_target),
        style: "border:none;background-color:#FFFFFF;",
        href: "",
        width: "300",
        height: "300"
    });
    let hanndleMessage = function (event) {
        let origin = event.origin;
        if (origin == "https://login.dingtalk.com") { //判断是否来自ddLogin扫码事件。
            let loginTmpCode = event.data;            //拿到loginTmpCode后就可以在这里构造跳转链接进行跳转了
            console.log(">>>:loginTmpCode", loginTmpCode);
            window.location.href = url_target + "&loginTmpCode=" + loginTmpCode;
        }
    };
    if (typeof window.addEventListener != 'undefined') {
        window.addEventListener('message', hanndleMessage, false);
    } else if (typeof window.attachEvent != 'undefined') {
        window.attachEvent('onmessage', hanndleMessage);
    }
}

/**
 * 获取服务器拼接的访问url
 * @param company_val
 * @returns {string}
 */
function get_decode_url(company_val) {
    let url_target = '';
    $.ajax({
        async: false,
        url: "/web/dingtalk/get_login_url",
        data: {"local_url": prot + "//" + host, "company_id": company_val},
        success: function (data) {
            if(data.state === false){
                alert(data.error);
                return false;
            }
            url_target = data.encode_url;
        },
        dataType: "json"
    });
    return url_target
}
