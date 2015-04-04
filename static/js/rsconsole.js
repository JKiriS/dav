$(document).ready(function(){

	function load(type){
		$.post("/console/get"+type,{dtoffset:-(new Date().getTimezoneOffset())},
			function(res){
			if(res.data){
				$("#"+type+" .console-group-content").html(res.data);
			}
		})
	}
	load("rssites");
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
		$.post("/console/set"+type,{target:target,cmd:cmd,
			dtoffset:-(new Date().getTimezoneOffset())},function(res){
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
		var category = $.trim($("#newsite-category .categories").val());
		var parser = $.trim($("#newsite-parser .parsers").val());
		$.post("/console/addrssite",{url:url,source:source,category:category,
			parser:parser,dtoffset:-(new Date().getTimezoneOffset())},
			function(res){
			$("#newsite .form-group").removeClass("has-error");
			if(res.error){
				alert(res.error);
			}
			else{
				$("#addrssite").modal('hide');
				$("#rssites table tr:last").after(res.data);
			}
		});
		return false
	});
	$("#newjob").submit(function(){
		var name = $.trim($(".jobtypes").val());
		var stime = $.trim($("#newjob-stime input").val());
		if(stime == "")
			stime = "minutes=1";
		stime = "timedelta(" + stime + ")"
		$.post("/console/addjob",{name:name,stime:stime,
			dtoffset:-(new Date().getTimezoneOffset())},
			function(res){
			$("#newjob .form-group").removeClass("has-error");
			if(res.error){
				alert(res.error);
			}
			else{
				$("#addjob").modal('hide');
				$("#jobs tr.info").after(res.data);
			}
		});
		return false;
	});
});
