var _params = {"start":0};

$(document).ready(function(){
	// clear scroll
	//window.scrollTo(0,document.body.scrollHeight);

	// get initial content
	var col = $(".currentcol").attr("id");
	$.post("",_params,function(res){
		if (res.status=="success"){
			$("div.content").empty();
			$("div.content").append(res.data);
			_params = res.params;
		}
	});

	//backtotop
	if ($(window).scrollTop() > 600)  
		$("a.backtotop").fadeIn(100);    
	else  
		$("a.backtotop").fadeOut(100);
	$(window).scroll(function(){  
		if ($(window).scrollTop() > 600)  
			$("a.backtotop").fadeIn(100);    
		else  
			$("a.backtotop").fadeOut(100);   
     }); 
	$("a.backtotop").on('click', function(){  
		$('body,html').animate({scrollTop:0}, 500);  
		return false;  
	});  

	// add tag
	$(".content").on("click", ".tagadd a", function(){
		$(".activeitem").removeClass("activeitem");
		$(this).parents(".item").addClass("activeitem");
		$(".activeitem .tagadd,.activeitem .newtag").toggle('fast');
	});
	$(".content").on("click", "button[name='cancel']", function(){
		$(".activeitem .tagadd,.activeitem .newtag").toggle('fast');
	});
	$(".content").on("click", "button[name='add']", function(){
		var name = $.trim($(".activeitem .newtag").children("input").val());
		var itemid = $(".activeitem").attr("id");
		$(".activeitem .tagadd").toggle('fast');
		$(".activeitem .newtag").toggle('fast');
		if( name!="" ){
			$.post("/rs/additemtag", {"name":name,"itemid":itemid}, function(res){
				if (res.status=="success")
					$(".activeitem .tagadd:first").before(res.data);
			});
		}
	});

	//click item, tag or source
	$(".content").on("click", "a.itemtitle", function(){
		var target = $(this).parents(".item").attr("id");
		$.post("/rs/behaviorrecorder", {"target":target});
	});

	//get more items
	$(".content").on("click", "a.viewmore", function(){
		$("a.viewmore").toggle();
		$("a.loadingmore").toggle();
		$.post("", _params, function (res){
			$("a.loadingmore").remove();
			$("a.viewmore").replaceWith(res.data);
			_params = res.params;
		});
	});

	//initial search
	var aQuery = window.location.href.split("?");//取得Get参数 
	var wd = ""; 
	if(aQuery.length > 1){ 
		var aBuf = aQuery[1].split("&"); 
		for(var i=0, iLoop = aBuf.length; i<iLoop; i++) { 
			var aTmp = aBuf[i].split("=");//分离key与Value 
			if(aTmp[0] == "wd"){
				$(".simsearch input[name='wd']").val(decodeURI(aTmp[1]));
				break ;
			}
		} 
	} 
	//search
	$(".simsearch a").on("click", function(){
		$(".simsearch").submit();
	});
	$(".simsearch").submit(function(){
		var wd = $.trim($(".simsearch input[name='wd']").val());
		if(wd != ""){
			window.location.href = "/rs/search?wd=" + wd.replace("%", "%25");
		}
		return false;
	});

	//user
    $(".navi").on("mouseenter", ".user", function(){
    	$(".user .hide").toggle();
    	$(".user").css("background-color", "rgba(115, 252, 199, 1)");
    });
    $(".navi").on("mouseleave", ".user", function(){
    	$(".user .hide").toggle();
    	$(".user").css("background-color", "");
    });

    //advsearch
    $(".advsearch .advscontent").empty();
	var type = $(".advsearch .advstop a.active").attr("title");
	var _searchdata = {};
	$.post("/rs/getsource", function(res){
    	_searchdata["source"] = res.data;
    	for(i=0;i<_searchdata["source"].length;i++){
	    	$(".advsearch .advscontent").append("<a href='/rs/lookclassified?"+type+"="+_searchdata[type][i]+"'>"+_searchdata[type][i]+"</a>");
	    }
    });
    $.post("/rs/getcategory", function(res){
    	_searchdata["category"] = res.data;
    });
    $(".search").on("mouseenter", function(){
    	$(".advsearch").toggle();
    	$(".column.search span").css("color", "white");
    });
    $(".search").on("mouseleave", function(){
    	$(".advsearch").toggle();
    	$(".column.search span").css("color", "");
    });
	$(".advsearch .advstop a").on("mouseenter", function(){
		if( $(this).hasClass("active") )
			return ;
		$(".advsearch .advstop a.active").removeClass("active");
		$(this).addClass("active");
		$(".advsearch .advscontent").empty();
		type = $(".advsearch .advstop a.active").attr("title");
		if(type == "source"){
			for(i=0;i<_searchdata["source"].length;i++){
	    		$(".advsearch .advscontent").append("<a href='/rs/lookclassified?"+type+"="+_searchdata[type][i]+"'>"+_searchdata[type][i]+"</a>");
	    	}
	    }
	    else if(type == "category"){
	    	for(i=0;i<_searchdata["category"].length;i++){
	    		$(".advsearch .advscontent").append("<a href='/rs/lookclassified?"+type+"="+_searchdata[type][i]+"'>"+_searchdata[type][i]+"</a>");
	    	}
	    }
	});

	//favorite
	$(".content").on("mouseenter mouseleave", ".favorite[title='添加收藏']",function(){
    	$(this).children("img").toggle();
    });
	$(".content").on("click", "a.favorite", function(){
		var target = $(this).parents(".item").attr("id");
		if($(this).attr("title") == "添加收藏"){
			$(this).attr("title", "取消收藏");
			$(this).children("img").attr("src", "/static/img/shoucan.jpg");
			$.post("/rs/addfavorite", {"target":target});
		}
		else{
			$(this).attr("title", "添加收藏");
			$(this).children("img").attr("src", "/static/img/shoucan1.jpg");
			$.post("/rs/removefavorite", {"target":target});
		}
	});

});
