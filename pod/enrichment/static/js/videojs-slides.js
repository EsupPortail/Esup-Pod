'use-strict';
var videojs = window.videojs;

const defaults = {};
const registerPlugin = videojs.registerPlugin || videojs.plugin;

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
				const currentSlide = document.getElementById('slide_'+i);
				currentSlide.style.display = 'block';
				videoplayer.setAttribute('style', 'width: 50%');
				active = true;
			} else {
				const oldSlide = document.getElementById('slide_'+i);
				oldSlide.style.display = 'none';
				if (!active) {
					videoplayer.setAttribute('style', 'width: 100%');
				}
			}
		}
		return false;
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