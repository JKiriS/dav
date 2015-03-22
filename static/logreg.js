
$(document).ready(function(){
	$("#gotoreg").on("click", function(){
		window.location.href = "/account/register";
	});

	$("#gotologin").on("click", function(){
		window.location.href = "/account/login";
	});

	function checkUname(uname, msg){
		if(msg==null){
			msg = "用户名除.外任意字符";
		}
		if(uname == ""){
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
			$("#uname .help-block").html("");
			return true;
		}
	}
	function checkUpwd(pwd, msg){
		if(msg==null){
			msg = "密码长度至少六位";
		}
		if(pwd == "" || pwd.length < 6){
			$("#upwd").addClass("has-error");
			$("#upwd .form-control-feedback").addClass("glyphicon-remove");
			$("#upwd .help-block").html(msg);
			return false;
		}
		else {
			$("#upwd").removeClass("has-error");
			$("#upwd").addClass("has-success");
			$("#upwd .form-control-feedback").removeClass("glyphicon-remove");
			$("#upwd .form-control-feedback").addClass("glyphicon-ok");
			$("#upwd .help-block").html("");
			return true;
		}
	}
	function checkEmail(email, msg){
		var emailreg =  /^[\w\-\.]+@[\w\-\.]+(\.\w+)+$/;
		if(msg==null){
			msg = "输入格式正确的邮箱";
		}
		if(!emailreg.test(email) ){
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
			$("#email .help-block").html("");
			return true
		}
	}
	$("#email input").on("focusout", function(){
		var email = $.trim($("#email input").val());
		checkEmail(email);
	});
	$("#uname input").on("focusout", function(){
		var uname = $.trim($("#uname input").val());
		checkUname(uname);
	});
	$("#upwd input").on("focusout", function(){
		var upwd = $.trim($("#upwd input").val());
		checkUpwd(upwd);
	});

	$(".login").submit(function(){
		var email = $.trim($("#email input").val());
		var upwd = $.trim($("#upwd input").val());
		var success = true;
		if(!checkEmaile(email))
			success = false;
		if(!checkUpwd(upwd))
			success = false;
		if(success) {
			$.post("", {"email":email,"pwd":upwd}, function(res){
				if(res.status == "success"){
					if(res.redirecturl != null)
						window.location.href = res.redirecturl
					else
						window.location.href = "/rs/";
				}
				else
					;
			});
		}
		return false;
	});

	$(".register").submit(function(){
		var uname = $.trim($("#uname input").val());
		var upwd = $.trim($("#upwd input").val());
		var email = $.trim($("#email input").val());
		var des = $.trim($("#udes textarea").val());
		var success = true;
		if(!checkUname(uname))
			success = false;
		if(!checkUpwd(upwd))
			success = false;
		if(!checkEmail(email))
			success = false;
		if(success) {
			$.post("", {"uname":uname,"pwd":pwd,"email":email,"des":des}, function(res){
				if(res.status == "success")
					window.location.href = "/account/login";
				else
					;
			});
		}
		return false;
	});

	if($.cookie('absms_crm2_email')!=undefined){  
        $("#rememberme").attr("checked", true);  
    }else{  
        $("#rememberme").attr("checked", false);  
    }  
    if($('#rememberme:checked').length>0){  
        $('#email input').val($.cookie('absms_crm2_email'));  
        $('#upwd input').val($.cookie('absms_crm2_pwd'));  
    }
	$("#rememberme").click(function(){ 
	 	var email = $.trim($("#email input").val());
		var upwd = $.trim($("#upwd input").val()); 
        if($('#rememberme:checked').length>0){ 
            $.cookie('absms_crm2_email', email);  
            $.cookie('absms_crm2_pwd', upwd);  
        }else{
            $.removeCookie('absms_crm2_email');  
            $.removeCookie('absms_crm2_pwd');  
        }  
    });

    var _mousexy = [];  
    $("body").on("mousemove", ".robot-checker", function(event){
    	var offset = $(this).offset();
    	_mousexy.push("("+(event.pageX-offset.left).toString()+","
    		+(event.pageY-offset.top).toString()+")");
    });
    $("body").on("click", ".robot-checker", function(){
    	_mousexy.push("click");
    });
    $("body").on("mouseenter", ".robot-checker", function(){
    	_mousexy = [];
    });
    $("body").on("mouseleave", ".robot-checker", function(){
    	if(_mousexy.indexOf("click") > 0){
    		$.post("/verificate/postmousetrail", {"data":_mousexy});
    	}
    	_mousexy = [];
    });
});