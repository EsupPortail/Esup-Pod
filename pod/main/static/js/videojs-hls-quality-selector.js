/**
 * videojs-hls-quality-selector
 * @version 0.0.4
 * @copyright 2018 Chris Boustead (chris@forgemotion.com)
 * @license MIT
 */
(function (global, factory) {
	typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory(require('video.js')) :
	typeof define === 'function' && define.amd ? define(['video.js'], factory) :
	(global.videojsHlsQualitySelector = factory(global.videojs));
}(this, (function (videojs) { 'use strict';

videojs = videojs && videojs.hasOwnProperty('default') ? videojs['default'] : videojs;

var version = "0.0.4";

var asyncGenerator = function () {
  function AwaitValue(value) {
    this.value = value;
  }

  function AsyncGenerator(gen) {
    var front, back;

    function send(key, arg) {
      return new Promise(function (resolve, reject) {
        var request = {
          key: key,
          arg: arg,
          resolve: resolve,
          reject: reject,
          next: null
        };

        if (back) {
          back = back.next = request;
        } else {
          front = back = request;
          resume(key, arg);
        }
      });
    }

    function resume(key, arg) {
      try {
        var result = gen[key](arg);
        var value = result.value;

        if (value instanceof AwaitValue) {
          Promise.resolve(value.value).then(function (arg) {
            resume("next", arg);
          }, function (arg) {
            resume("throw", arg);
          });
        } else {
          settle(result.done ? "return" : "normal", result.value);
        }
      } catch (err) {
        settle("throw", err);
      }
    }

    function settle(type, value) {
      switch (type) {
        case "return":
          front.resolve({
            value: value,
            done: true
          });
          break;

        case "throw":
          front.reject(value);
          break;

        default:
          front.resolve({
            value: value,
            done: false
          });
          break;
      }

      front = front.next;

      if (front) {
        resume(front.key, front.arg);
      } else {
        back = null;
      }
    }

    this._invoke = send;

    if (typeof gen.return !== "function") {
      this.return = undefined;
    }
  }

  if (typeof Symbol === "function" && Symbol.asyncIterator) {
    AsyncGenerator.prototype[Symbol.asyncIterator] = function () {
      return this;
    };
  }

  AsyncGenerator.prototype.next = function (arg) {
    return this._invoke("next", arg);
  };

  AsyncGenerator.prototype.throw = function (arg) {
    return this._invoke("throw", arg);
  };

  AsyncGenerator.prototype.return = function (arg) {
    return this._invoke("return", arg);
  };

  return {
    wrap: function (fn) {
      return function () {
        return new AsyncGenerator(fn.apply(this, arguments));
      };
    },
    await: function (value) {
      return new AwaitValue(value);
    }
  };
}();





var classCallCheck = function (instance, Constructor) {
  if (!(instance instanceof Constructor)) {
    throw new TypeError("Cannot call a class as a function");
  }
};











var inherits = function (subClass, superClass) {
  if (typeof superClass !== "function" && superClass !== null) {
    throw new TypeError("Super expression must either be null or a function, not " + typeof superClass);
  }

  subClass.prototype = Object.create(superClass && superClass.prototype, {
    constructor: {
      value: subClass,
      enumerable: false,
      writable: true,
      configurable: true
    }
  });
  if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass;
};











var possibleConstructorReturn = function (self, call) {
  if (!self) {
    throw new ReferenceError("this hasn't been initialised - super() hasn't been called");
  }

  return call && (typeof call === "object" || typeof call === "function") ? call : self;
};

// Default options for the plugin.
var defaults = {};

// Cross-compatibility for Video.js 5 and 6.
var registerPlugin = videojs.registerPlugin || videojs.plugin;
// const dom = videojs.dom || videojs;

/**
 * VideoJS HLS Quality Selector Plugin class.
 */

var HlsQualitySelectorPlugin = function () {

  /**
   * Plugin Constructor.
   *
   * @param {Player} player - The videojs player instance.
   * @param {Object} options - The plugin options.
   */
  function HlsQualitySelectorPlugin(player, options) {
    classCallCheck(this, HlsQualitySelectorPlugin);

    this.player = player;

    // If there is quality levels plugin and the HLS tech exists
    // then continue.
    if (this.player.qualityLevels && this.getHls()) {
      // Create the quality button.
      this.createQualityButton();
      this.bindPlayerEvents();
    }
  }

  /**
   * Returns HLS Plugin
   *
   * @return {*} - videojs-hls-contrib plugin.
   */


  HlsQualitySelectorPlugin.prototype.getHls = function getHls() {
    return this.player.tech({ IWillNotUseThisInPlugins: true }).hls;
  };

  /**
   * Binds listener for quality level changes.
   */


  HlsQualitySelectorPlugin.prototype.bindPlayerEvents = function bindPlayerEvents() {
    this.player.qualityLevels().on('addqualitylevel', this.onAddQualityLevel.bind(this));
  };

  /**
   * Adds the quality menu button to the player control bar.
   */


  HlsQualitySelectorPlugin.prototype.createQualityButton = function createQualityButton() {

    var player = this.player;
    var videoJsButtonClass = videojs.getComponent('MenuButton');

    /**
     * Extend vjs button class for quality button.
     */

    var ConcreteButtonClass = function (_videoJsButtonClass) {
      inherits(ConcreteButtonClass, _videoJsButtonClass);

      /**
       * Button constructor.
       */
      function ConcreteButtonClass() {
        classCallCheck(this, ConcreteButtonClass);
        return possibleConstructorReturn(this, _videoJsButtonClass.call(this, player, { title: player.localize('Quality') }));
      }

      /**
       * Creates button items.
       *
       * @return {Array} - Button items
       */


      ConcreteButtonClass.prototype.createItems = function createItems() {
        return [];
      };

      return ConcreteButtonClass;
    }(videoJsButtonClass);

    this._qualityButton = new ConcreteButtonClass();

    var placementIndex = player.controlBar.children().length - 2;
    var concreteButtonInstance = player.controlBar.addChild(this._qualityButton, { componentClass: 'qualitySelector' }, placementIndex);

    concreteButtonInstance.addClass('vjs-quality-selector');
    concreteButtonInstance.menuButton_.$('.vjs-icon-placeholder').className += ' vjs-icon-hd';
    concreteButtonInstance.removeClass('vjs-hidden');
  };

  /**
   * Builds individual quality menu items.
   *
   * @param {Object} item - Individual quality menu item.
   * @return {ConcreteMenuItemClass} - Menu item
   */


  HlsQualitySelectorPlugin.prototype.getQualityMenuItem = function getQualityMenuItem(item) {
    var player = this.player;
    var videoJsMenuItemClass = videojs.getComponent('MenuItem');

    /**
     * Extend vjs menu item class.
     */

    var ConcreteMenuItemClass = function (_videoJsMenuItemClass) {
      inherits(ConcreteMenuItemClass, _videoJsMenuItemClass);

      /**
       * Menu item constructor.
       *
       * @param {Player} _player - vjs player
       * @param {Object} _item - Item object
       * @param {ConcreteButtonClass} qualityButton - The containing button.
       * @param {HlsQualitySelectorPlugin} _plugin - This plugin instance.
       */
      function ConcreteMenuItemClass(_player, _item, qualityButton, _plugin) {
        classCallCheck(this, ConcreteMenuItemClass);

        var _this2 = possibleConstructorReturn(this, _videoJsMenuItemClass.call(this, _player, {
          label: item.label,
          selectable: true,
          selected: item.selected || false
        }));

        _this2.item = _item;
        _this2.qualityButton = qualityButton;
        _this2.plugin = _plugin;
        return _this2;
      }

      /**
       * Click event for menu item.
       */


      ConcreteMenuItemClass.prototype.handleClick = function handleClick() {

        // Reset other menu items selected status.
        for (var i = 0; i < this.qualityButton.items.length; ++i) {
          this.qualityButton.items[i].selected(false);
        }

        // Set this menu item to selected, and set quality.
        this.plugin.setQuality(this.item.value);
        this.selected(true);
      };

      return ConcreteMenuItemClass;
    }(videoJsMenuItemClass);

    return new ConcreteMenuItemClass(player, item, this._qualityButton, this);
  };

  /**
   * Executed when a quality level is added from HLS playlist.
   */


  HlsQualitySelectorPlugin.prototype.onAddQualityLevel = function onAddQualityLevel() {

    var player = this.player;
    var qualityList = player.qualityLevels();
    var levels = qualityList.levels_ || [];
    var levelItems = [];

    for (var i = 0; i < levels.length; ++i) {
      var levelItem = this.getQualityMenuItem.call(this, {
        label: levels[i].height + 'p',
        value: levels[i].height
      });

      levelItems.push(levelItem);
    }

    levelItems.push(this.getQualityMenuItem.call(this, {
      label: 'Auto',
      value: 'auto',
      selected: true
    }));

    if (this._qualityButton) {
      this._qualityButton.createItems = function () {
        return levelItems;
      };
      this._qualityButton.update();
    }
  };

  /**
   * Sets quality (based on media height)
   *
   * @param {number} height - A number representing HLS playlist.
   */


  HlsQualitySelectorPlugin.prototype.setQuality = function setQuality(height) {
    var qualityList = this.player.qualityLevels();

    for (var i = 0; i < qualityList.length; ++i) {
      var quality = qualityList[i];

      quality.enabled = quality.height === height || height === 'auto';
    }
    this._qualityButton.unpressButton();
  };

  return HlsQualitySelectorPlugin;
}();

/**
 * Function to invoke when the player is ready.
 *
 * This is a great place for your plugin to initialize itself. When this
 * function is called, the player will have its DOM and child components
 * in place.
 *
 * @function onPlayerReady
 * @param    {Player} player
 *           A Video.js player object.
 *
 * @param    {Object} [options={}]
 *           A plain object containing options for the plugin.
 */


var onPlayerReady = function onPlayerReady(player, options) {
  player.addClass('vjs-hls-quality-selector');
  player.hlsQualitySelector = new HlsQualitySelectorPlugin(player, options);
};

/**
 * A video.js plugin.
 *
 * In the plugin function, the value of `this` is a video.js `Player`
 * instance. You cannot rely on the player being in a "ready" state here,
 * depending on how the plugin is invoked. This may or may not be important
 * to you; if not, remove the wait for "ready"!
 *
 * @function hlsQualitySelector
 * @param    {Object} [options={}]
 *           An object of options left to the plugin author to define.
 */
var hlsQualitySelector = function hlsQualitySelector(options) {
  var _this3 = this;

  this.ready(function () {
    onPlayerReady(_this3, videojs.mergeOptions(defaults, options));
  });
};

// Register the plugin with video.js.
registerPlugin('hlsQualitySelector', hlsQualitySelector);

// Include the version number.
hlsQualitySelector.VERSION = version;

return hlsQualitySelector;

})));
