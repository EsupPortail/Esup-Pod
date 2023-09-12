let sliderOne = document.getElementById("slider-1");
let sliderTwo = document.getElementById("slider-2");
let displayValOne = document.getElementById("range1");
let displayValTwo = document.getElementById("range2");
let minGap = 0;
let sliderTrack = document.querySelector(".slider-track");
start_time = parseInt(sliderOne.value);
button_reset = document.getElementById("reset");
initialStart = sliderOne.value;
initialEnd = sliderTwo.value;

// Set max value
let sliderMaxValue = sliderOne.max;
// Set min value
let sliderMinValue = sliderOne.min;

function doChangeForRange1() {
  // Do change for the start value with the "time range"
  let value = timeToInt(this.value);
  if (value >= 0 && value <= sliderMaxValue) {
    sliderOne.value = value;
    fillColor();
    changeCurrentTimePlayer(value);
  }
}

function doChangeForRange2() {
  // Do change for the end value with the "time range"
  let value = timeToInt(this.value);
  if (value >= 0 && value <= sliderMaxValue) {
    sliderTwo.value = value;
    fillColor();
    changeCurrentTimePlayer(value);
  }
}

window.onload = function () {
  slideOne();
  slideTwo();
  player.currentTime(0);
};

displayValOne.addEventListener("change", doChangeForRange1);
displayValTwo.addEventListener("change", doChangeForRange2);

function slideOne() {
  // Do change for the start value with the slider
  if (parseInt(sliderTwo.value) - parseInt(sliderOne.value) <= minGap) {
    sliderOne.value = parseInt(sliderTwo.value) - minGap;
  }
  displayValOne.value = intToTime(sliderOne.value);
  fillColor();
  changeCurrentTimePlayer(sliderOne.value);
}

function slideTwo() {
  // Do change for the end value with the slider
  if (parseInt(sliderTwo.value) - parseInt(sliderOne.value) <= minGap) {
    sliderTwo.value = parseInt(sliderOne.value) + minGap;
  }
  displayValTwo.value = intToTime(sliderTwo.value);
  fillColor();
  changeCurrentTimePlayer(sliderTwo.value);
}

function fillColor() {
  // Apply the changes
  percent1 = (sliderOne.value / sliderMaxValue) * 100;
  percent2 = (sliderTwo.value / sliderMaxValue) * 100;
  sliderTrack.style.background = `linear-gradient(to right, #dadae5 ${percent1}% , #1f8389 ${percent1}% , #1f8389 ${percent2}%, #dadae5 ${percent2}%)`;
  calculation_total_time();
}

function intToTime(time) {
  // Convert an integer to a time
  var sec_num = parseInt(time, 10); // don't forget the second param
  var hours = Math.floor(sec_num / 3600);
  var minutes = Math.floor((sec_num - hours * 3600) / 60);
  var seconds = sec_num - hours * 3600 - minutes * 60;

  if (hours < 10) {
    hours = "0" + hours;
  }
  if (minutes < 10) {
    minutes = "0" + minutes;
  }
  if (seconds < 10) {
    seconds = "0" + seconds;
  }
  return hours + ":" + minutes + ":" + seconds;
}

function timeToInt(date) {
  // Convert time to an integer
  var a = date.split(":"); // split it at the colons

  // minutes are worth 60 seconds. Hours are worth 60 minutes.
  var seconds = +a[0] * 60 * 60 + +a[1] * 60 + +a[2];
  return seconds;
}

function calculation_total_time() {
  // Calculate the total duration of the video
  var total_time = sliderTwo.value - sliderOne.value;
  if (total_time >= 0 && total_time <= sliderMaxValue) {
    document.getElementById("total_time").innerText = intToTime(total_time);
  } else {
    document.getElementById("total_time").innerText = "--:--:--";
  }
}

// Prevents validating only with the Enter key without going through confirmation
(function (n) {
  var f = function (e) {
    var c = e.which || e.keyCode;
    if (c == 13) {
      e.preventDefault();
      let ConfirmationModalID = document.getElementById("ConfirmationModal");
      let ConfirmationModal =
        bootstrap.Modal.getOrCreateInstance(ConfirmationModalID);
      ConfirmationModal.show();
      return false;
    }
  };
  window.noPressEnter = function (a, b) {
    b = typeof b === "boolean" ? b : true;
    if (b) {
      a.addEventListener(n, f);
    } else {
      a.removeEventListener(n, f);
    }
    return a;
  };
})("keydown");

noPressEnter(displayValOne);
noPressEnter(displayValTwo);
noPressEnter(sliderOne);
noPressEnter(sliderTwo);

// Buttons to get the time of the video player
let button_start = document.getElementById("button_start");
let button_end = document.getElementById("button_end");

button_start.addEventListener("click", get_video_player_start);
button_start.addEventListener("keydown", function (event) {
  if (event.key === " ") {
    get_video_player_start(event);
  }
});

button_end.addEventListener("click", get_video_player_end);
button_end.addEventListener("keydown", function (event) {
  if (event.key === " ") {
    get_video_player_end(event);
  }
});

/**
 * Retrieves the start time of the video player and updates UI elements accordingly.
 */
function get_video_player_start(event) {
  event.preventDefault();
  time = Math.trunc(player.currentTime()) + start_time;
  displayValOne.value = intToTime(time);
  sliderOne.value = time;
  fillColor();
}

/**
 * Retrieves the end time of the video player and updates UI elements accordingly.
 */
function get_video_player_end(event) {
  event.preventDefault();
  time = Math.trunc(player.currentTime()) + start_time;
  displayValTwo.value = intToTime(time);
  sliderTwo.value = Math.trunc(time);
  fillColor();
}

// Button reset
button_reset.addEventListener("click", resetVideoCut);
button_reset.addEventListener("keydown", function (event) {
  if (event.key === " ") {
    resetVideoCut(event);
  }
});

/**
 * Resets the video cut to its initial state, updating UI elements and video player.
 */
function resetVideoCut(event) {
  event.preventDefault();
  displayValOne.value = intToTime(initialStart);
  sliderOne.value = initialStart;
  displayValTwo.value = intToTime(initialEnd);
  sliderTwo.value = initialEnd;
  fillColor();
  player.currentTime(0);
}

/**
 * Changes the current time of the video player based on the provided value.
 *
 * @param {number} value - The new time value to set for the video player.
 */
function changeCurrentTimePlayer(value) {
  // Move the player along with the cursor
  if (value - initialStart >= 0) {
    player.currentTime(value - initialStart);
  }
}
