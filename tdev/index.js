var _params = {"start":0};

$(document).ready(function(){
	// clear scroll
	window.scrollTo(0,document.body.scrollHeight);

	// get initial content
	var col = $(".currentcol").attr("id");
	if(col != "self")
		$.post("",_params,function(res){
			if (res.status=="success"){
				$("div.content").empty();
				$("div.content").append(res.data);
				_params = res.params;
			}
		});
	else
		$.post("/rs/getupre",_params,function(res){
			if (res.status=="success"){
				$("div.content").empty();
				$("div.content").append(res.data);
				_params = res.params;
			}
		});

	//backtotop
	$(window).scroll(function(){  
		if ($(window).scrollTop() > 300)  
			$("a.backtotop").fadeIn(100);    
		else  
			$("a.backtotop").fadeOut(100);   
     }); 
	$("a.backtotop").on('click', function(){  
		$('body,html').animate({scrollTop:0}, 500);  
		return false;  
	});  

	// add tag
	$(".content").on("click", "div.tagadd", function(){
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
	$(".content").on("click", "a[type]", function(){
		var ttype = this.type;
		var target = $(this).attr("title");
		if(ttype != "item"){
			var _searchparams = {};
			if(ttype == "source")
				_searchparams.source = target;
			if(ttype == "tag")
				_searchparams.tag = target;
			window.location.href = "/rs/search?" + $.param( _searchparams, true )
		}
		else
			$.post("/rs/behaviorrecorder", {"type":"click", "ttype":ttype, "target":target});
	});

	//get more items
	$(".content").on("click", "a.viewmore", function(){
		$("a.viewmore span").replaceWith("<img src='/static/img/loadingsmall.gif' width='25' height='25' />")
		$.post("", _params, function (res){
			$("a.viewmore").replaceWith(res.data);
			_params = res.params;
		});
	});

	//search
	$(".simsearch a").on("click", function(){
		var wd = $.trim($(".simsearch input[name='wd']").val());
		if(wd != ""){
			window.location.href = "/rs/search?wd=" + wd
		}
	});

	//user
    $(".navi").on("mouseenter", ".user", function(){
    	$(".user .hide").toggle();
    	$(".user").css("background-color", "white");
    });
    $(".navi").on("mouseleave", ".user", function(){
    	$(".user .hide").toggle();
    	$(".user").css("background-color", "");
    });

    //advsearch
    $(".advsearch .advscontent").empty();
	var type = $(".advsearch .advstop a.active").attr("title");
	var _searchdata = {};
	$.post("/rs/get"+type, function(res){
    	_searchdata[type] = res.data;
    	for(i=0;i<_searchdata[type].length;i++){
    		$(".advsearch .advscontent").append("<a href='/rs/search?"+type+"="+_searchdata[type][i]+"'>"+_searchdata[type][i]+"</a>");
    	}
    });
    $(".search").on("mouseenter", function(){
    	$(".advsearch").toggle();
    	$(".column.search").css("background-color", "rgba(211, 84, 84, 0.85)");
    });
    $(".search").on("mouseleave", function(){
    	$(".advsearch").toggle();
    	$(".column.search").css("background-color", "");
    });
	$(".advsearch .advstop a").on("click", function(){
		if( $(this).hasClass("active") )
			return ;
		$(".advsearch .advstop a.active").removeClass("active");
		$(this).addClass("active");
		$(".advsearch .advscontent").empty();
		var type = $(".advsearch .advstop a.active").attr("title");
		if( _searchdata[type] == null ){
			$.post("/rs/get"+type, function(res){
    			_searchdata[type] = res.data;
    		});
		}
		for(i=0;i<_searchdata[type].length;i++){
    		$(".advsearch .advscontent").append("<a href='/rs/search?"+type+"="+_searchdata[type][i]+"'>"+_searchdata[type][i]+"</a>");
    	}
	});

	//add favorite
	$(".favorite").on("mouseenter", function(){
    	$(this).children("img").toggle();
    });
    $(".favorite").on("mouseleave", function(){
    	$(this).children("img").toggle();
    });
	$(".favorite").on("click", function(){
		if($(this).attr("title") == "添加收藏"){
			$(this).attr("title", "取消收藏")
			$(this).children("img").attr("src", "./shoucan.jpg");
		}
		else{
			$(this).attr("title", "添加收藏")
			$(this).children("img").attr("src", "./shoucan1.jpg");
		}
		// alert( $s(this).parents(".item").attr("id") );
	});

});
