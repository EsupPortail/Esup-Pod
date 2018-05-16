(function() {
	'use strict';
	var videojs = null;
	if(typeof window.videojs === 'undefined' && typeof require === 'function') {
		videojs = require('video.js');
	} else {
		videojs = window.videojs;
	}

	(function(window, videojs) {
		var videoJsChapters,
			defaults = {
				ui: true
			};

		/*
		 * Chapter menu button
		 */
		var MenuButton = videojs.getComponent('MenuButton');
		var ChapterMenuButton = videojs.extend(MenuButton, {
			constructor: function(player, options){
				options.label = 'Chapters';
				MenuButton.call(this, player, options);
				this.el().setAttribute('aria-label', 'Chapters');
				videojs.dom.addClass(this.el(), 'vjs-chapters-button');
				this.controlText('Chapters');

				var span = document.createElement('span');
				videojs.dom.addClass(span, 'vjs-chapters-icon');
				this.el().appendChild(span);
			}
		});
		ChapterMenuButton.prototype.handleClick = function(event){
			MenuButton.prototype.handleClick.call(this, event);
			if($('.chapters-list.inactive li').length > 0) {
				if($('.vjs-slide').children().length > 0) {
					$('.vjs-slide').animate({
						width: '20%',
						height: '20%',
						left: '5%'
					},500);
					$('.vjs-slide img').animate({
						top: '0px'
					},500);
				}
				$('.video-js .vjs-tech').animate({
					width: '80%'
				},500, function(){
					$('.chapters-list.inactive').attr('class', 'chapters-list active');
				});
				$('.vjs-chapters-button button').css('text-shadow', '0 0 1em #fff');
			} else {
				$('.chapters-list.active').attr('class', 'chapters-list inactive');
				if($('.vjs-slide').children().length > 0) {
					$('.vjs-slide').animate({
						width: '50%',
						height: '90%',
						left: '50%'
					},500);
					$('.vjs-slide img').animate({
						top: '69px'
					},500);
					$('.video-js .vjs-tech').animate({
						width: '50%'
					},500);
				} else {
					$('.video-js .vjs-tech').animate({
						width: '100%'
					},500);
				}
				$('.vjs-chapters-button button').css('text-shadow', '');
			}
		};
		MenuButton.registerComponent('ChapterMenuButton', ChapterMenuButton);


		/**
		 * Initialize the plugin.
		 */
		videoJsChapters = function(options) {
			var settings = videojs.mergeOptions(defaults, options),
				player = this,
				chapters = {},
				currentChapter = {};

			/**
			 * Create the list of chapters
			 */
			player.createChapters = function(data){
				if(!data){ return false; }
				this.chapters = groupedChapters(data);

				var ol = document.getElementById('chapters-list');
				for (var i = 0; i < this.chapters.id.length; ++i) {
					var chapId = this.chapters.id[i];
					var chapTitle = this.chapters.title[i];
					var chapStart = this.chapters.start[i];
					var chapEnd = this.chapters.end[i];
					var newLi = document.createElement('li');
					var newA = document.createElement('a');
					newA.setAttribute('id', chapId);
					newA.setAttribute('start', chapStart);
					newA.setAttribute('end', chapEnd);
					
					var newTitle = document.createTextNode(chapTitle);
					newA.appendChild(newTitle);
					newLi.appendChild(newA);
					ol.appendChild(newLi);

					newA.addEventListener('click', function() {
						player.currentTime(this.attributes.start.value);
					}, false);
				}
				var oldList  = document.getElementById('chapters');
				var newList = document.getElementsByClassName('chapters-list inactive');
				oldList.parentNode.removeChild(oldList);
				$(newList).appendTo('#'+player.id());
				
			};

			/**
			 * Return a list of chapters useable by other functions
			 */
			function groupedChapters(data){
				var chapters = {
					id: [],
					title: [],
					start: [],
					end: []
				};

				for (var i = 0; i < data.length; i++) {
					chapters.id.push(parseInt(data[i].attributes[3].value));
					chapters.title.push(data[i].attributes[2].value);
					chapters.start.push(parseInt(data[i].attributes[0].value));
					chapters.end.push(parseInt(data[i].attributes[1].value));
				}

				return chapters;
			}

			player.getGroupedChapters = function(){
				return this.chapters;
			};

			player.ready(function(){
				var data = $('#chapters li');
				if( settings.ui && data.length >= 1) {
					var menuButton = new ChapterMenuButton(player, settings);
					player.controlBar.chapters = player.controlBar.el_.insertBefore(
						menuButton.el_, player.controlBar.getChild('fullscreenToggle').el_);
					player.controlBar.chapters.dispose = function(){
						this.parentNode.removeChild(this);
					};
				}
				if (data.length >= 1) {
					player.createChapters(data);
				}
			});
		};

		// Register the plugin
		videojs.registerPlugin('videoJsChapters', videoJsChapters);
	})(window, videojs);
})();