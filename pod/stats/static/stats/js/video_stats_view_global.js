const defaultParams = {
  startYear: new Date().getFullYear() - 5,
  endYear: new Date().getFullYear(),
  tension: 0.5,
  borderWidth: 2,
  animationDuration: 2000,
  animationDelay: 500,
};

var yearChart;
let startYear = defaultParams.startYear;
let endYear = defaultParams.endYear;
let years = [];
let yearlyViews = [];
let yearlyFavorites = [];
let yearlyPlaylistAdditions = [];

const startYearInput = document.getElementById("start-year-" + graph_id);
const endYearInput = document.getElementById("end-year-" + graph_id);
const dataUrl = window.location.href;

startYearInput.max = defaultParams.endYear;
startYearInput.value = defaultParams.startYear;
endYearInput.max = defaultParams.endYear;
endYearInput.value = defaultParams.endYear;

if (startYear === undefined && endYear === undefined) {
  startYear = defaultParams.startYear;
  endYear = defaultParams.endYear;
  updateChart();
}

startYearInput.addEventListener("change", function () {
  startYear = parseInt(this.value);
  endYearInput.min = startYear;
  updateChart();
});

endYearInput.addEventListener("change", function () {
  endYear = parseInt(this.value);
  startYearInput.max = endYear;
  updateChart();
});

function updateChart() {
  years = [];
  yearlyViews = [];
  yearlyFavorites = [];
  yearlyPlaylistAdditions = [];
  const requests = [];

  for (let year = startYear; year <= endYear; year++) {
    requests.push(
      fetchData(dataUrl, "POST", {
        csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
        periode: year,
      }),
    );
  }

  Promise.all(requests)
    .then(function (responses) {
      responses.forEach(function (response) {
        const JSONResponse = JSON.parse(response);
        const year = JSONResponse.year;
        const data = JSONResponse.datas;

        years.push(year);
        yearlyViews.push(data.views_year);
        yearlyFavorites.push(data.favorites_year);
        yearlyPlaylistAdditions.push(data.playlist_addition_year);
      });

      renderChart();
    })
    .catch((error) => console.error(error));
}

function renderChart() {
  const ctx = document.getElementById(graph_id).getContext("2d");

  if (yearChart) {
    yearChart.destroy();
  }

  yearChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: years,
      datasets: [
        {
          label: gettext("Views"),
          backgroundColor: "#ed184e",
          borderColor: "#ed184e",
          borderWidth: defaultParams.borderWidth,
          data: yearlyViews,
          tension: defaultParams.tension,
        },
        {
          label: gettext("Favorites"),
          backgroundColor: "#3871c1",
          borderColor: "#3871c1",
          borderWidth: defaultParams.borderWidth,
          data: yearlyFavorites,
          tension: defaultParams.tension,
        },
        {
          label: gettext("Playlist additions"),
          backgroundColor: "#1F7C85",
          borderColor: "#1F7C85",
          borderWidth: defaultParams.borderWidth,
          data: yearlyPlaylistAdditions,
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
        gettext("Years"),
        gettext("Views"),
        gettext("Favorites"),
        gettext("Playlists_addition"),
      ],
      rows: [],
    };
    for (let i = 0; i < years.length; i++) {
      dataForCSV.rows.push([
        years[i],
        yearlyViews[i],
        yearlyFavorites[i],
        yearlyFavorites[i],
      ]);
    }
    exportDataToCSV(dataForCSV, "stats-" + graph_title + ".csv"); // INCLURE DATE
  });
