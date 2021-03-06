
$(document).ready(function(){
	$("#gotoreg").on("click", function(){
		window.location.href = "/account/register";
	});

	$("#gotologin").on("click", function(){
		window.location.href = "/account/login";
	});

	function checkInput(target, val, msg){
		var emailreg =  /^[\w\-\.]+@[\w\-\.]+(\.\w+)+$/;
		if(target == 'uname'){
			if(msg==null){
				msg = "用户名除.外任意字符";
			}
			if(val == ""){
				$("#uname").addClass("has-error");
				$("#uname .form-control-feedback").addClass("glyphicon-remove");
				$("#uname .help-block").html(msg);
				return false;
			}
			else {
				$("#uname").removeClass("has-error");
				$("#uname").addClass("has-success");
				$("#uname .form-control-feedback").removeClass("glyphicon-remove");
				$("#uname .form-control-feedback").addClass("glyphicon-ok");
				$("#uname .help-block").html("&nbsp");
				return true;
			}
		}
		if(target == 'pwd'){
			if(msg==null)
				msg = "密码长度至少六位";
			if(val == "" || val.length < 6){
				$("#pwd").addClass("has-error");
				$("#pwd .form-control-feedback").addClass("glyphicon-remove");
				$("#pwd .help-block").html(msg);
				return false;
			}
			else {
				$("#pwd").removeClass("has-error");
				$("#pwd").addClass("has-success");
				$("#pwd .form-control-feedback").removeClass("glyphicon-remove");
				$("#pwd .form-control-feedback").addClass("glyphicon-ok");
				$("#pwd .help-block").html("&nbsp");
				return true;
			}
		}
		if(target == 'email'){
			if(msg==null){
				msg = "输入格式正确的邮箱";
			}
			if(!emailreg.test(val) ){
				$("#email").addClass("has-error");
				$("#email .form-control-feedback").addClass("glyphicon-remove");
				$("#email .help-block").html(msg);
				return false
			}
			else {
				$("#email").removeClass("has-error");
				$("#email").addClass("has-success");
				$("#email .form-control-feedback").removeClass("glyphicon-remove");
				$("#email .form-control-feedback").addClass("glyphicon-ok");
				$("#email .help-block").html("&nbsp");
				return true
			}
		}
		if(target == "des"){
			if(msg==null){
				msg = "用一段话描述自己";
			}
			if(val == ""){
				$("#des").addClass("has-warning");
				$("#des .help-block").html(msg);
				return false
			}
			else {
				$("#des").removeClass("has-warning");
				$("#des").addClass("has-success");
				$("#des .help-block").html("&nbsp");
				return true
			}
		}	
	}

	$("#email input").on("focusout", function(){
		var email = $.trim($("#email input").val());
		checkInput('email', email);
	});
	$("#uname input").on("focusout", function(){
		var uname = $.trim($("#uname input").val());
		checkInput('uname', uname);
	});
	$("#pwd input").on("focusout", function(){
		var pwd = $.trim($("#pwd input").val());
		checkInput('pwd', pwd);
	});
	$("#des textarea").on("focusout", function(){
		var des = $.trim($("#des textarea").val());
		checkInput('des', des);
	});

	$(".login").submit(function(){
		var email = $.trim($("#email input").val());
		var pwd = $.trim($("#pwd input").val());
		var success = true;
		if(!checkInput('email', email))
			success = false;
		if(!checkInput('pwd', pwd))
			success = false;
		if(success) {
			$.post("", {"email":email,"pwd":pwd}, function(res){
				if(res.status == "success"){
					if(res.redirecturl != null)
						window.location.href = res.redirecturl
					else
						window.location.href = "/rs/";
				}
				else{
					for (var i in res.errors){
						checkInput(res.errors[i].target, "", res.errors[i].reason);
					}
				}
			});
		}
		return false;
	});

	$(".register").submit(function(){
		var uname = $.trim($("#uname input").val());
		var pwd = $.trim($("#pwd input").val());
		var email = $.trim($("#email input").val());
		var des = $.trim($("#des textarea").val());
		var success = true;
		if(!checkInput("uname", uname))
			success = false;
		if(!checkInput("pwd", pwd))
			success = false;
		if(!checkInput("email", email))
			success = false;
		checkInput('des', des);
		if(success) {
			$.post("", {"uname":uname,"pwd":pwd,"email":email,"des":des}, function(res){
				if(res.status == "success")
					window.location.href = "/account/login";
				else{
					for (var i in res.errors)
						checkInput(res.errors[i].target, "", res.errors[i].reason);
				}
			});
		}
		return false;
	});

	if($.cookie('absms_crm2_email')!=undefined){  
        $("#rememberme").attr("checked", true);  
    }else{  
        $("#rememberme").attr("checked", false);  
    }  
    if($('#rememberme:checked').length > 0){ 
    	var email = $.cookie('absms_crm2_email');
    	var pwd = $.cookie('absms_crm2_pwd');
        $('#email input').val(email);  
        $('#pwd input').val(pwd);
		checkInput('email', email);
		checkInput('pwd', pwd);  
    }
	$("#rememberme").click(function(){ 
	 	var email = $.trim($("#email input").val());
		var pwd = $.trim($("#pwd input").val()); 
        if($('#rememberme:checked').length > 0){ 
            $.cookie('absms_crm2_email', email);  
            $.cookie('absms_crm2_pwd', pwd);  
        }else{
            $.removeCookie('absms_crm2_email');  
            $.removeCookie('absms_crm2_pwd');  
        }  
    });
});