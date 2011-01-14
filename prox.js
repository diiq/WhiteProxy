
$(document).ready(function(){
    $("#time").hide();
    function seed(o){
	var out = o.html;
	$('#terms').html(out);
    }

    $("#for").submit(function(event){
	event.preventDefault();
	alert("yes");
	$.post("prox.cgi", ("words="+ $("#balls").val()));
	$("#for").hide();
	$("#time").show("slide", {direction:"left", easing:"linear"}, 600000,
	    function(){
		$("#time").hide();
		$("#for").show();
	});
	window.open("http://www.google.com/search?sourceid=chrome&ie=UTF-8&q="+ $("#balls").val());
	return false;
    });
});

