'use-strict';
var videojs = window.videojs;

const defaults = {};
const registerPlugin = videojs.registerPlugin || videojs.plugin;
const slide_color = {
	'document': 'yellow',
	'image': 'purple',
	'richtext': 'blue',
	'weblink': 'red',
	'embed': 'green'
};
const slide_mode_list = {
	'off': '100/0',
	'default': '50/50',
	'pip media': '100/20',
	'pip video': '20/100'
};
var slide_mode = 'default';
var currentSlide = null;

/**
 * VideoSlides component
 *
 * @class VideoSlides
 * @extends {videojs.Component}
 */
class VideoSlides {

	constructor(items) {
		this.slides = document.createElement('ul');
		this.slidesItems = items;
		this.oldTime = 0;
		this.appendSlider();
		this.slideButton();
		this.slideMode();
		currentSlide = document.getElementById('slide_0');
		player.trigger('changemode', slide_mode);
	}

	/**
	 * AppendSlider function to append Slide list into VideoJS.
	 *
	 * @return {void} doesn't return anything
	 * @function appendSlider
	 */
	appendSlider() {
		// Get control bar element
		const controlBar = document.getElementsByClassName('vjs-control-bar')[0];

		// Add slide list className
		this.slides.className = 'video-slides';
		controlBar.parentNode.insertBefore(this.slides, controlBar);
		this.appendSliderItem();
		this.slideBar();
	}

	/**
	 * AppendSliderItem function to append SlideItem into Slide List.
	 *
	 * @return {void} doesn't return anything
	 * @function appendSliderItem
	 */
	appendSliderItem() {
		var keys = Object.keys(this.slidesItems);
		for (let i = 0; i <= keys.length - 1; i++) {
			// Create the slide depend on their type
			var type = this.slidesItems[i].type;
			var slide = null;
			if (type == 'image') {
				slide = document.createElement('img');
				slide.src = this.slidesItems[i].url;
				slide.alt = this.slidesItems[i].title;
				slide.width = player.currentDimensions().width / 2;
				slide.height = player.currentDimensions().height / 2;
			} else if (type == 'document') {
				slide = document.createElement('embed');
				slide.src = this.slidesItems[i].url;
				slide.alt = this.slidesItems[i].title;
				slides.type = 'application/pdf';
				slide.width = player.currentDimensions().width / 2;
				slide.height = player.currentDimensions().height / 2;
			} else if (type == 'richtext') {
				slide = document.createElement('div');
				slide.innerHTML = this.slidesItems[i].url;
			} else if (type == 'weblink') {
				slide = document.createElement('embed');
				slide.src = this.slidesItems[i].url;
				slide.alt = this.slidesItems[i].title;
				slides.type = 'text/html';
				slide.width = player.currentDimensions().width / 2;
				slide.height = player.currentDimensions().height / 2;
			} else if (type == 'embed') {
				slide = document.createElement('div');
				slide.innerHTML = this.slidesItems[i].url;
			}
			const li = document.createElement('li');
			// Added src and class name
			li.setAttribute('data-start', this.slidesItems[i].start);
			li.setAttribute('data-end', this.slidesItems[i].end);
			li.setAttribute('data-type', this.slidesItems[i].type);
			li.setAttribute('id', 'slide_'+i);
			// Append image into li
			li.appendChild(slide);
			// Append li into ul list
			this.slides.appendChild(li);
		}
	}

	/**
	 * slideShow function to show the current slide according to the time.
	 *
	 * @param {number} time the current video time
	 * @return {void} doesn't return anything
	 * @function slideShow
	 */
	slideShow(time) {
		const currentTime = Math.floor(time);
		var videoplayer = document.getElementsByClassName('vjs-tech')[0];

		var keys = Object.keys(this.slidesItems);
		var active = false;
		for (let i = 0; i <= keys.length - 1; i++) {
			if (currentTime >= this.slidesItems[i].start && currentTime < this.slidesItems[i].end) {
				currentSlide = document.getElementById('slide_'+i);
				currentSlide.style.display = 'block';
				active = true;
				player.trigger('changemode', slide_mode);
			} else {
				const oldSlide = document.getElementById('slide_'+i);
				oldSlide.style.display = 'none';
			}
		}
		if (!active) {
			player.trigger('changemode', 'off');
		}
		return false;
	}

	/**
	 * slideBar function to show position of the slides above the reading bar
	 *
	 * @return {void} doesn't return anything
	 * @function slideBar
	 */
	slideBar() {
		const progressbar = document.getElementsByClassName('vjs-progress-holder')[0];
		// Create the slidebar
		var slidebar = document.createElement('div');
		slidebar.className = 'vjs-chapbar';
		var slidebar_holder = document.createElement('div');
		slidebar_holder.className = 'vjs-chapbar-holder';
		slidebar.appendChild(slidebar_holder);
		progressbar.appendChild(slidebar);
		// Create slide(s) into the slidebar
		var duration = player.duration();
		var keys = Object.keys(this.slidesItems);
		for (let i = 0; i <= keys.length - 1; i++) {
			var slidebar_left = (parseInt(this.slidesItems[i].start) / duration) * 100;
			var slidebar_width = (parseInt(this.slidesItems[i].end) / duration) * 100 - slidebar_left;
			var id = this.slidesItems[i].id;
			var type = this.slidesItems[i].type;
			var newslide = document.createElement('div');
			newslide.className = 'vjs-chapbar-chap';
			newslide.style = 'left: ' + slidebar_left + '%; width: ' + slidebar_width + '%; background-color: ' + slide_color[type];
			newslide.id = 'slidebar_' + i;
			slidebar_holder.appendChild(newslide); 
		}
	}

	/**
	 * slideMode function to change display mode for the slides.
	 *
	 * @return {void} does'nt return anything
	 * @function slideMode
	 */
	slideMode() {
		player.on('changemode', function (e, mode) {
			var videoplayer = document.getElementsByClassName('vjs-tech')[0];
			if (mode in slide_mode_list) {
				var video = slide_mode_list[mode].split('/')[0];
				var slide = slide_mode_list[mode].split('/')[1];
				videoplayer.style.width = video + '%';
				videoplayer.style.zIndex = 1;
				currentSlide.classList.remove('pip-slide');
				currentSlide.classList.remove('full-slide');
				currentSlide.style.zIndex = 'auto';
				currentSlide.style.width = slide + '%';
				if (mode == 'pip media') {
					currentSlide.className = 'pip-slide';
					currentSlide.style.zIndex = 2;
				}
				if (mode == 'pip video') {
					currentSlide.className = 'full-slide';
					videoplayer.style.zIndex = 1;
				}
			}
			document.getElementsByClassName('vjs-slide-manager')[0].firstChild.firstChild.innerHTML = slide_mode;
		});
	}

	/**
	 * slideButton function create a button on the player to manage slides.
	 *
	 * @return {void} doesn't return anything
	 * @function slideButton
	 */
	slideButton() {
		// Create the slide view mode
		var vjs_menu_item = videojs.getComponent('MenuItem');
		var SlideMode = videojs.extend(vjs_menu_item, {
			constructor: function(player, options={}) {
				options.label = options.mode;
				vjs_menu_item.call(this, player, options);
				this.on('click', this.onClick);
				this.addClass('vjs-slide-mode');
				this.controlText('Turn to ' + options.mode);
			},
			onClick: function() {
				this.setAttribute('aria-checked', true);
				this.addClass('vjs-selected');
				player.trigger('changemode', this.el().firstChild.innerHTML);
				slide_mode = this.el().firstChild.innerHTML;

				var available = document.getElementsByClassName('vjs-slide-mode');
				for (let e of available) {
					if (e.firstChild.innerHTML != this.el().firstChild.innerHTML) {
						e.setAttribute('aria-checked', false);
						e.classList.remove('vjs-selected');
					}
				}
			}
		});

		// Create the slide manager menu title
		var SlideTitle = videojs.extend(vjs_menu_item, {
			constructor: function(player, options = {}) {
				vjs_menu_item.call(this, player, options);
				this.off('click');
			}
		});

		// Create the slide menu manager
		var vjs_menu_button = videojs.getComponent('MenuButton');
		var SlideButton = videojs.extend(vjs_menu_button, {
			constructor: function(player, options = {}) {
				vjs_menu_button.call(this, player, options);
				this.addClass('vjs-slide-manager');
				this.controlText('Open slide manager');
				this.el().firstChild.firstChild.innerHTML = slide_mode;
			},
			createItems: function() {
				var items = [];

				items.push(new SlideTitle(player, {
					el: videojs.dom.createEl('li', {
						className: 'vjs-menu-title vjs-slide-manager-title',
						innerHTML: 'Slide'
					})
				}));

				for (let e in slide_mode_list) {
					items.push(new SlideMode(player, {
						mode: e
					}));
				}

				return items;
			}
		});
		var newbutton = new SlideButton(player);

		player.controlBar.el().insertBefore(newbutton.el(), document.getElementsByClassName('vjs-fullscreen-control')[0]);
	}
}

const onPlayerReady = (player, options) => {
	player.addClass('vjs-slides');
	const slides = new VideoSlides(options);

	player.on('timeupdate', function() {
		slides.slideShow(this.currentTime());
	});
};

/**
 * A video.js plugin.
 *
 * @function slides
 * @param {object} [options={}]
 * 		  An object of options left to the plugin author to define.
 */
const slides = function(options) {
	this.ready(() => {
		onPlayerReady(this, videojs.mergeOptions(defaults, options));
	});
};

// Register the plugin with video.js.
registerPlugin('slides', slides);