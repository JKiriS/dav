
$(document).ready(function(){

	// init markdown editor
	// editor.codemirror.getValue();
	var editor = new Editor();
	editor.render();

	$(".main-container").on("click", ".material-list a.material", function(){
		$(".material-container iframe").attr("src", $(this).attr("href"));
		$(this).addClass("active");
		return false;
	});

	$(".dialogue").on("click", "a", function(){
		$(".material-container iframe").attr("src", $(this).attr("href"));
		return false;
	});

	$('.editor-wrapper').draggable({cancel:".panel-body"});

	$("#showeditor, #closeeditor").on("click", function(){
		$(".editor-wrapper").toggle();
	});

	$("#submiteditor").on("click", function(){
		var title = $(".editor-wrapper .panel-body .title").val();
		var content = editor.codemirror.getValue();
		$(".dialogue").append(marked(content));
		$(".editor-wrapper").toggle();
	});

	$(".msg-input").submit(function(){
		var msg = $(".msg-input textarea").val()
		$(".dialogue").append(msg);
		$(".msg-input textarea").val("")
		return false;
	});

	$(".material-container").resizable({
		maxWidth: 300,
	});

});