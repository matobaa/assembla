$(document).ready(function() {
	$("#extsearch").submit(function() {
		$('#proj-search').val('ticket:' + $(this).text().match(/\d+/g).join())
		$('#search').submit();
		return false; // avoid original submit
	})
});
