var _params = {"start":0};

$(document).ready(function(){
	function addColor(){
		_color = ["red","green","blue","gold","brown","purple","pink",];
		$(".item").css("border-bottom",function(){
			if($(this).css("border-bottom-style") == "none"){
				return "1px solid " + _color[Math.floor(Math.random()*_color.length)] ;
			}
		});
	}

	// get initial content
	$.post("",_params,function(res){
		if (res.status=="success"){
			$("div.itemlist").empty();
			$("div.itemlist").append(res.data);
			_params = res.params;
			addColor();
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
	$(".itemlist").on("click", "a.tagadd", function(){
		$(".activeitem").removeClass("activeitem");
		$(this).parents(".item").addClass("activeitem");
		$(".activeitem .tagadd,.activeitem .newtag").toggle('fast');
	});
	$(".itemlist").on("click", "button[name='cancel']", function(){
		$(".activeitem .tagadd,.activeitem .newtag").toggle('fast');
	});
	$(".itemlist").on("submit", ".newtag", function(){
		var name = $.trim($(".activeitem .newtag").children("input").val());
		var itemid = $(".activeitem").attr("id");
		$(".activeitem .tagadd, .activeitem .newtag").toggle('fast');
		if( name!="" ){
			$.post("/rs/additemtag", {"name":name,"itemid":itemid}, function(res){
				if (res.status=="success")
					$(".activeitem .itemtag:last").after(res.data);
			});
		}
		return false;
	});

	//click item, tag or source
	$(".itemlist").on("click", "a.itemtitle", function(){
		var target = $(this).parents(".item").attr("id");
		var behaviordata = {"target":target, "fromurl":window.location.href};
		if( "searchid" in _params ){
			behaviordata.searchid = _params.searchid;
		}
		$.post("/rs/behaviorrecorder", behaviordata);
	});

	//get more items
	$(".itemlist").on("click", "a.viewmore", function(){
		$("a.viewmore, a.load-sm").toggle();
		$.post("", _params, function (res){
			$("a.load-sm").remove();
			$("a.viewmore").replaceWith(res.data);
			_params = res.params;
			addColor();
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
				$("#nav-search input").val(decodeURI(aTmp[1]));
				break ;
			}
		} 
	} 
	//search
	$("#nav-search").submit(function(){
		var wd = $.trim($("#nav-search input").val());
		if(wd != ""){
			window.location.href = "/rs/search?wd=" + wd.replace("%", "%25");
		}
		return false;
	});

	//favorite
	$(".itemlist").on("click", "a.favo", function(){
		var target = $(this).parents(".item").attr("id");
		if($(this).attr("title") == "添加收藏"){
			$.post("/rs/addfavorite", {"target":target}, function(res){
				$(this).attr("title", "取消收藏");
				$(this).children(".glyphicon").removeClass("glyphicon-star-empty");
				$(this).children(".glyphicon").addClass("glyphicon-star");
				$(this).next().html(parseInt($(this).next().html()) + 1);
			});
		}
		else{
			$.post("/rs/removefavorite", {"target":target}, function(res){
				alert($(this).attr());
				$(this).attr("title", "添加收藏");
				$(this).children(".glyphicon").removeClass("glyphicon-star");
				$(this).children(".glyphicon").addClass("glyphicon-star-empty");
				$(this).next().html(parseInt($(this).next().html()) - 1);
			});
		}
	});

});
