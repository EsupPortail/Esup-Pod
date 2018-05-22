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
			// Create an image and li tag
			const img = document.createElement('img');
			const li = document.createElement('li');

			// Added src and class name
			img.src = this.slidesItems[i].url;
			li.className = 'slide_' + this.slidesItems[i].time;
			// Append image into li
			li.appendChild(img);
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

		var keys = Object.keys(this.slidesItems);
		for (let i = 0; i <= keys.length - 1; i++) {
			if (currentTime == this.slidesItems[i].time && this.oldTime !== currentTime) {
				const firstItem = (i === 0) ? 0 : 1;
				const oldItem = 'slide_' + this.slidesItems[i - firstItem].time;
				const currentItem = 'slide_' + this.slidesItems[i].time;
				const beforeSlide = document.getElementsByClassName(oldItem)[0];
				const currentSlide = document.getElementsByClassName(currentItem)[0];

				beforeSlide.style.display = 'none';
				currentSlide.style.display = 'block';
				this.oldTime = currentTime;
				return false;
			}
		}
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