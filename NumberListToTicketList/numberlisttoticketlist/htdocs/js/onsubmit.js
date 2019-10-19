


$(document).ready(function() {
	if( !$("#content")[0].classList.contains("search"))
		return;
	$('<form id="extsearch" action="#">' +
		'<textarea rows="5" cols="60" class="trac-resizable"/>' +
		'<input type="submit" value="Show ticket list"/></form>')
	.submit(function() {
		$('#proj-search').val('ticket:' + $("textarea", this)[0].value.match(/\d+/g).join())
		$('#search').submit();
		return false; // avoid original submit
	})
	.insertAfter($("#content"))
});
