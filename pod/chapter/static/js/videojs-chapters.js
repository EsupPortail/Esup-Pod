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
				options.label = gettext('Chapters');
				MenuButton.call(this, player, options);
				this.el().setAttribute('aria-label', gettext('Chapters'));
				videojs.dom.addClass(this.el(), 'vjs-chapters-button');
				this.controlText(gettext('Chapters'));

				var span = document.createElement('span');
				videojs.dom.addClass(span, 'vjs-chapters-icon');
				this.el().appendChild(span);
			}
		});
		ChapterMenuButton.prototype.handleClick = function(event){
			MenuButton.prototype.handleClick.call(this, event);
			if($('.chapters-list.inactive li').length > 0) {
				$('.chapters-list.inactive').attr('class', 'chapters-list active');
				$('.vjs-chapters-button button').css('text-shadow', '0 0 1em #fff');
			} else {
				$('.chapters-list.active').attr('class', 'chapters-list inactive');
				$('.vjs-chapters-button button').css('text-shadow', '');
			}
		};
		MenuButton.registerComponent('ChapterMenuButton', ChapterMenuButton);


		/**
		 * Initialize the plugin.
		 */
		var Plugin = videojs.getPlugin('plugin');
		videoJsChapters = videojs.extend(Plugin, {
			constructor: function(player, options) {
				Plugin.call(this, player, options);
				var settings = videojs.mergeOptions(defaults, options),
					chapters = {},
					currentChapter = document.createElement('li');

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
						var chapTime = this.chapters.start[i];
						var newLi = document.createElement('li');
						var newA = document.createElement('a');
						newA.setAttribute('id', "chapter"+chapId);
						newA.setAttribute('start', chapTime);
						
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
						start: []
					};
					for (var i = 0; i < data.length; i++) {
						chapters.id.push(parseInt(data[i].attributes[1].value));
						chapters.title.push(data[i].attributes[2].value);
						chapters.start.push(parseInt(data[i].attributes[0].value));
					}
					return chapters;
				}

				player.getGroupedChapters = function(){
					return this.chapters;
				};

				player.getCurrentChapter = function(time, chapters){
					const currentTime = Math.floor(time);

					var keys = Object.keys(chapters.start);
					for (let i = 0; i <= keys.length - 1; i++) {
						var next = chapters.start[i+1] || player.duration();
						currentChapter = document.getElementById("chapter"+chapters.id[i]);
						if (currentTime >= chapters.start[i] && currentTime < next) {
							currentChapter.classList.add('current');
						} else {
							currentChapter.classList.remove('current');
						}
					}
				};

				player.main = function(){
					var data = $('#chapters li');
					if (settings.ui && data.length >= 1 && typeof(player.controlBar.chapters) == 'undefined') {
						var menuButton = new ChapterMenuButton(player, settings);
						player.controlBar.chapters = player.controlBar.el_.insertBefore(
							menuButton.el_, player.controlBar.getChild('fullscreenToggle').el_);
						player.controlBar.chapters.dispose = function(){
							this.parentNode.removeChild(this);
							player.controlBar.chapters = undefined;
						};
					}
					if (data.length >= 1) {
						player.createChapters(data);
					}
				};

				player.ready(player.main);

				this.on(player, 'timeupdate', function() {
					player.getCurrentChapter(player.currentTime(), player.getGroupedChapters());
				});
			}
		});

		videoJsChapters.prototype.dispose = function() {
			Plugin.prototype.dispose.call(this);
		};
			
		// Register the plugin
		videojs.registerPlugin('videoJsChapters', videoJsChapters);
	})(window, videojs);
})();