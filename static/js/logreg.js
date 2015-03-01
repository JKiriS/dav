
$(document).ready(function(){
	$("#gotoreg").on("click", function(){
		window.location.href = "/account/register";
	});
	$(".login").submit(function(){
		var uname = $.trim($("input[name='uname']").val());
		var pwd = $.trim($("input[name='pwd']").val());
		$(".errorinput").removeClass("errorinput");
		if(uname == "")
			$("input[name='uname']").addClass("errorinput");
		else if(pwd == "" || pwd.length < 6)
			$("input[name='pwd']").addClass("errorinput");
		else {
			$.post("", {"uname":uname,"pwd":pwd}, function(res){
				if(res.status == "success")
					window.location.href = "/rs/";
				else
					$("input[name='pwd']").addClass("errorinput");
			});
		}
		return false;
	});

	$("#gotologin").on("click", function(){
		window.location.href = "/account/login/";
	});

	$(".register").submit(function(){
		var uname = $.trim($(".register input[name='uname']").val());
		var pwd = $.trim($(".register input[name='pwd']").val());
		var email = $.trim($(".register input[name='email']").val());
		var des = $.trim($("textarea").val());
		var emailreg =  /^[\w\-\.]+@[\w\-\.]+(\.\w+)+$/;
		$(".errorinput").removeClass("errorinput");
		if(uname == "")
			$(".register input[name='uname']").addClass("errorinput");
		else if(pwd == "" || pwd.length < 6)
			$(".register input[name='pwd']").addClass("errorinput");
		else if(email == "" || !emailreg.test(email) )
			$(".register input[name='email']").addClass("errorinput");
		else {
			$.post("", {"uname":uname,"pwd":pwd,"email":email,"des":des}, function(res){
				if(res.status == "success")
					window.location.href = "/account/login";
				else
					$("input[name='email']").addClass("errorinput");
			});
		}
		return false;
	});
});
