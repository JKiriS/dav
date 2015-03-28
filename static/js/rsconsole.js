$(document).ready(function(){

	function load(type){
		$.post("/console/get"+type,function(res){
			if(res.data){
				$("#"+type+" .console-group-content").html(res.data);
			}
		})
	}
	load("sites");
	load("jobs");
	load("services");
	$(".console-group-header a.refresh").on("click",function(){
		var type = $(this).parents(".console-group").attr("id");
		load(type);
	});

	$(".content").on("mouseover",".console-group-content .status",function(){
		$(this).children(".status-label").hide();
		$(this).children("button").show();
	});

	$(".content").on("mouseleave",".console-group-content .status",function(){
		$(this).children(".status-label").show();
		$(this).children("button").hide();
	});

	$(".content").on("click",".console-group-content table button",function(){
		var type = $(this).parents(".console-group").attr("id");
		var target = $(this).parents("tr").attr("id");
		var cmd = $(this).html();
		$.post("/console/set"+type,{'target':target,'cmd':cmd},function(res){
			if(res.data){
				$("tr#"+target).html(res.data);
			}
			else{
				alert(res.error);
			}
		})
	});

	$("#newsite").submit(function(){
		var url = $.trim($("#newsite-url input").val());
		var source = $.trim($("#newsite-source input").val());
		var category = $.trim($("#newsite-category input").val());
		var parser = $.trim($("#newsite-parser textarea").val());
		$.post("/console/rs/addsite",{"url":url,"source":source,
			"category":category,"parser":parser},function(res){
			$("#newsite .form-group").removeClass("has-error");
			if(res.errors){
				for (var i in res.errors){
					var t = "#newsite-" + res.errors[i].target;
					$(t).addClass("has-error");
				}
			}
			else{
				$("#sites table").append(res.data);
			}
		});
	});
	$("#newjob").submit(function(){
		var name = $.trim($("#newjob-name input").val());
		var starttime = $.trim($("#newjob-starttime input").val());
		$.post("/console/rs/addjob",{"name":name,
			"starttime":starttime},function(res){
			$("#newjob .form-group").removeClass("has-error");
			if(res.errors){
				for (var i in res.errors){
					var t = "#newjob-" + res.errors[i].target;
					$(t).addClass("has-error");
				}
			}
			else{
				$("#jobs table").append(res.data);
			}
		});
	});
});
