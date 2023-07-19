const defaultParams = {
  startDateDefault: new Date(new Date().getTime() - 7 * 24 * 60 * 60 * 1000)
    .toISOString()
    .split("T")[0],
  endDateDefault: new Date().toISOString().split("T")[0],
  tension: 0.5,
  borderWidth: 2,
  animationDuration: 2000,
  animationDelay: 500,
};

let startDateDefault = defaultParams.startDateDefault;
let endDateDefault = defaultParams.endDateDefault;

var dateChart;
var startDate;
var endDate;
let days = [];
let dailyViews = [];
let dailyFavorites = [];
let dailyPlaylistAdditions = [];

const startDateInput = document.getElementById("start-date-" + graph_id);
const endDateInput = document.getElementById("end-date-" + graph_id);
const dataUrl = window.location.href;

startDateInput.value = defaultParams.startDateDefault;
startDateInput.max = defaultParams.endDateDefault;
endDateInput.value = defaultParams.endDateDefault;
endDateInput.max = defaultParams.endDateDefault;

if (startDate === undefined && endDate === undefined) {
  startDate = defaultParams.startDateDefault;
  endDate = defaultParams.endDateDefault;
  updateChart();
}

startDateInput.addEventListener("change", function () {
  startDate = parseInt(this.value);
  endDateInput.min = startDate;
  updateChart();
});

endDateInput.addEventListener("change", function () {
  endDate = parseInt(this.value);
  startDateInput.max = endDate;
  updateChart();
});

function updateChart() {
  days = [];
  dailyViews = [];
  dailyFavorites = [];
  dailyPlaylistAdditions = [];
  const requests = [];

  for (
    let currentDate = new Date(startDate);
    currentDate <= new Date(endDate);
    currentDate.setDate(currentDate.getDate() + 1)
  ) {
    let formattedDate = currentDate.toISOString().split("T")[0];
    days.push(formattedDate);
    requests.push(
      fetchData(dataUrl, "POST", {
        csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
        periode: formattedDate,
      }),
    );
  }

  Promise.all(requests)
    .then(function (responses) {
      responses.forEach(function (response) {
        const JSONResponse = JSON.parse(response);
        const data = JSONResponse.datas;
        dailyViews.push(data.views_day);
        dailyFavorites.push(data.favorites_day);
        dailyPlaylistAdditions.push(data.playlist_addition_day);
      });

      renderChart();
    })
    .catch((error) => console.error(error));
}

function renderChart() {
  const ctx = document.getElementById(graph_id).getContext("2d");

  if (dateChart) {
    dateChart.destroy();
  }

  dateChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: days,
      datasets: [
        {
          label: gettext("Views"),
          backgroundColor: "#ed184e",
          borderColor: "#ed184e",
          borderWidth: defaultParams.borderWidth,
          data: dailyViews,
          tension: defaultParams.tension,
        },
        {
          label: gettext("Favorites"),
          backgroundColor: "#3871c1",
          borderColor: "#3871c1",
          borderWidth: defaultParams.borderWidth,
          data: dailyFavorites,
          tension: defaultParams.tension,
        },
        {
          label: gettext("Playlist additions"),
          backgroundColor: "#1F7C85",
          borderColor: "#1F7C85",
          borderWidth: defaultParams.borderWidth,
          data: dailyPlaylistAdditions,
          tension: defaultParams.tension,
        },
      ],
    },
    options: {
      spanGaps: true,
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: graph_title,
          padding: {
            top: 10,
            bottom: 5,
          },
        },
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: gettext("Date"),
          },
        },
        y: {
          display: true,
          title: {
            display: true,
            text: gettext("Value"),
          },
        },
      },
      animation: {
        duration: defaultParams.animationDuration,
        delay: defaultParams.animationDelay,
        easing: "easeInOutElastic",
      },
    },
  });
}
updateChart();

document
  .getElementById("export-btn-" + graph_id)
  .addEventListener("click", function () {
    var dataForCSV = {
      headers: [
        gettext("Date"),
        gettext("Views"),
        gettext("Favorites"),
        gettext("Playlists_addition"),
      ],
      rows: [],
    };
    for (let i = 0; i < daily.length; i++) {
      dataForCSV.rows.push([
        daily[i],
        dailyviews[i],
        dailyfavo[i],
        dailyPlaylists[i],
      ]);
    }
    exportDataToCSV(dataForCSV, "stats-" + graph_title + ".csv"); // INCLURE DATE
  });
