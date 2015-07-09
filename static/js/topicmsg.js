
$(document).ready(function(){
	function parseGET(){
		var aQuery = window.location.href.split("?");//取得Get参数 
		var res = {}; 
		if(aQuery.length > 1){ 
			var aBuf = aQuery[1].split("&"); 
			for(var i=0, iLoop = aBuf.length; i<iLoop; i++) { 
				var aTmp = aBuf[i].split("=");//分离key与Value 
				if(aTmp[0] != ""){
					res[aTmp[0]] = aTmp[1];
				}
			} 
		} 
		return res;
	}
	var GET = parseGET();

	$.post("/topicmsg/materiallist", {'topic':GET['id']}, function(res){
		if(! res.errors)
			$(".material-list-content").append(res.data);
		else
			alert(res.errors);
	});

	var lastmsgid = ($(".dialogue .msg:last").attr("id"))?$(".dialogue .msg:last").attr("id"):"";
	function pollmsg(){	
		$.ajax({
			type:"POST",
			dataType:"json",
			timeout:80000,
			url:"/topicmsg/getmsglist", 
			data:{topic:GET['id'],lastmsgid:lastmsgid,time:60,dtoffset:-(new Date().getTimezoneOffset())}, 
			success:function(res){
				if(! res.errors){
					$(".dialogue").append(res.data);
					lastmsgid = ($(".dialogue .msg:last").attr("id"))?$(".dialogue .msg:last").attr("id"):"";
					// pollmsg();
				}
				else{
					alert(res.errors);
					// pollmsg();
				}
			},
			error:function(XMLHttpRequest,textStatus,errorThrown){      
	            if(textStatus=="timeout"){ 
	                // setTimeout(pollmsg(), 1000); 
	            }      
	        }
		});
	};
	pollmsg();

	var editor = new Editor({
		  element: document.getElementById('editor')
		});
	editor.render();

	$(".material-list").on("click", "a.material", function(){
		$(".material-container iframe").attr("src", $(this).attr("href"));
		$(this).addClass("active");
		return false;
	});
	$(".addmaterial").on("click", function(){
		$(".new-material").show();
		return false;
	});
	$("#submitmaterial").on("click", function(){
		var title = $("#newmaterial-topic input").val();
		var url = $("#newmaterial-link input").val();
		$.post("/topicmsg/addmaterial",{'topic':GET['id'],'title':title,'url':url}
			,function(res){
			if(! res.errors){
				$(".material-list-content .material:first").before(res.data);
				$("#newmaterial-topic input").val("");
				$("#newmaterial-link input").val("");
			}
			else
				alert(res.errors);
		});
		$(".new-material").hide();
	});
	$(".material-list-header").on("click", function(){
		$(".material-list-content").toggle("fast");
		$(".togglemateriallist .glyphicon").toggleClass("glyphicon-triangle-left");
		$(".togglemateriallist .glyphicon").toggleClass("glyphicon-triangle-bottom");
	});

	$(".dialogue").on("click", ".viewmsgdetail", function(){
		var msgid = $(this).parents(".msg").attr("id");
		if($("#d"+msgid).length > 0)
			$("#d"+msgid).show("fast");
		else{
			$.post("/topicmsg/msgdetail",{'id':msgid},function(res){
				if(! res.errors){
					$("body").append(res.data);
					$("#d"+msgid).draggable({cancel:".panel-body"});
					$("#d"+msgid).css("top", $("#"+msgid).offset().top+10);
					$("#d"+msgid).css("left", $("#"+msgid).offset().left+150);
					$("#d"+msgid).show();
				}
				else
					alert(res.errors);
			});
		}
		return false;
	});

	$("body").on("click", ".msg-detail a", function(){
		$(".material-container iframe").attr("src", $(this).attr("href"));
		return false;
	});

	$('.panel').draggable({cancel:".panel-body"});

	$("#showeditor").on("click", function(){
		$(".editor-wrapper").show();
	});

	$("body").on("click", ".closepanel", function(){
		$(this).parents(".panel").hide();
	});

	$("#submiteditor").on("click", function(){
		var title = $(".editor-wrapper .panel-body .title").val();
		var content = editor.codemirror.getValue();
		$.post("/topicmsg/addmsg",{'topic':GET['id'],'content':content,'title':title}
			,function(res){
			if(! res.errors){
				$(".dialogue").append(res.data);
				editor.codemirror.setValue("");
				$(".editor-wrapper .panel-body .title").val("");
				$(".editor-wrapper").hide();
			}
			else
				alert(res.errors);
		});
	});

	$(".msg-input").submit(function(){
		var title = $(".msg-input textarea").val();
		// alert(now.getTime());
		$.post("/topicmsg/addmsg",{'topic':GET['id'],'content':'','title':title}
			,function(res){
			if(! res.errors){
				$(".dialogue").append(res.data);
				$(".msg-input textarea").val("");
			}
			else
				alert(res.errors);
		});
		return false;
	});
	
});