
$(document).ready(function(){

	Date.prototype.Format = function(fmt)   
	{ //author: meizz   
	  var o = {   
	    "M+" : this.getMonth()+1,                 //月份   
	    "d+" : this.getDate(),                    //日   
	    "h+" : this.getHours(),                   //小时   
	    "m+" : this.getMinutes(),                 //分   
	    "s+" : this.getSeconds(),                 //秒   
	    "q+" : Math.floor((this.getMonth()+3)/3), //季度   
	    "S"  : this.getMilliseconds()             //毫秒   
	  };   
	  if(/(y+)/.test(fmt))   
	    fmt=fmt.replace(RegExp.$1, (this.getFullYear()+"").substr(4 - RegExp.$1.length));   
	  for(var k in o)   
	    if(new RegExp("("+ k +")").test(fmt))   
	  fmt = fmt.replace(RegExp.$1, (RegExp.$1.length==1) ? (o[k]) : (("00"+ o[k]).substr((""+ o[k]).length)));   
	  return fmt;   
	} 

	// init markdown editor
	// editor.codemirror.getValue();
	var editor = new Editor();
	editor.render();

	$(".material-list").on("click", "a.material", function(){
		$(".material-container iframe").attr("src", $(this).attr("href"));
		$(this).addClass("active");
		return false;
	});

	$(".dialogue").on("click", "a", function(){
		$(".material-container iframe").attr("src", $(this).attr("href"));
		return false;
	});

	$('.panel').draggable({cancel:".panel-body"});

	$("#showeditor").on("click", function(){
		$(".editor-wrapper").show();
	});

	$(".closepanel").on("click", function(){
		$(this).parents(".panel").hide();
	});

	$("#submiteditor").on("click", function(){
		var title = $(".editor-wrapper .panel-body .title").val();
		// var content = editor.codemirror.getValue();
		// $(".dialogue").append(marked(content));
		var now = new Date()
		// alert(now.getTime());
		var nowstr = now.Format("yyyy-MM-dd hh:mm:ss");
		var nm = '<div class="msg self">'+
                    '<div class="msg-header">'+
                        '<a href="javascript:void(0)" class="user"><img class="img-rounded" src="./img/icon.png" height="25"/>'+
                        '<span>Anony.</span></a><span>'+nowstr+'</span>'+
                    '</div><div class="msg-content">'+title+
                    '<a href="javascript:void(0) class="details"><span>查看详细</span></a></div></div>';
		$(".dialogue").append(nm);
		$(".editor-wrapper").hide();
	});

	$()

	$(".msg-input").submit(function(){
		var msg = $(".msg-input textarea").val();
		var now = new Date()
		// alert(now.getTime());
		var nowstr = now.Format("yyyy-MM-dd hh:mm:ss");
		var nm = '<div class="msg self">'+
                    '<div class="msg-header">'+
                        '<a href="javascript:void(0)" class="user"><img class="img-rounded" src="./img/icon.png" height="25"/>'+
                        '<span>Anony.</span></a><span>'+nowstr+'</span>'+
                    '</div><div class="msg-content">'+msg+'</div></div>';
		$(".dialogue").append(nm);
		$(".msg-input textarea").val("");
		return false;
	});

	$(".addmaterial").on("click", function(){
		$(".new-material").show();
		return false;
	});

	$("#submitmaterial").on("click", function(){
		var topic = $("#newmaterial-topic input").val();
		var link = $("#newmaterial-link input").val();
		var na = '<a href="'+link+'" class="material">'+topic+'</a>';
		$(".material-list-content .material:first").before(na);
		$(".new-material").hide();
		$("#newmaterial-topic input").val("");
		$("#newmaterial-link input").val("");
	});

	// $( ".main-container" ).resizable({
	// 	alsoResize: '.material-container',
	// 	iframeFix: true
	// });

	$(".material-list-header").on("click", function(){
		$(".material-list-content").toggle("fast");
		$(".togglemateriallist .glyphicon").toggleClass("glyphicon-triangle-left");
		$(".togglemateriallist .glyphicon").toggleClass("glyphicon-triangle-bottom");
	});
	
});