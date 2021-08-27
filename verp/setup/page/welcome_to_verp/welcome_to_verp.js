frappe.pages['welcome-to-verp'].on_page_load = function(wrapper) {
	var parent = $('<div class="welcome-to-verp"></div>').appendTo(wrapper);

	parent.html(frappe.render_template("welcome_to_verp", {}));

	parent.find(".video-placeholder").on("click", function() {
		window.verp_welcome_video_started = true;
		parent.find(".video-placeholder").addClass("hidden");
		parent.find(".embed-responsive").append('<iframe class="embed-responsive-item video-playlist" src="https://www.verp.com/embed/videoseries?list=PL3lFfCEoMxvxDHtYyQFJeUYkWzQpXwFM9&color=white&autoplay=1&enablejsapi=1" allowfullscreen></iframe>')
	});

	// pause video on page change
	$(document).on("page-change", function() {
		if (window.verp_welcome_video_started && parent) {
			parent.find(".video-playlist").each(function() {
				this.contentWindow.postMessage('{"event":"command","func":"' + 'pauseVideo' + '","args":""}', '*');
			});
		}
	});
}
