((function () {
  var yearChart;
  var startYear;
  var endYear;
  let y = [];
  let yearlyviews = [];
  let yearlyfav = [];
  let yearlyPlaylist = [];
  let today = new Date();
  let dataUrl = window.location.href;

  var defaultParams = {
    startYear: today.getFullYear() - 5,
    endYear: today.getFullYear(),
    tension: 0.5,
    borderWidth: 2,
    animationDuration: 2000,
    animationDelay: 500,
  };
  var params = Object.assign({}, defaultParams);

  const startYearInput = document.getElementById("start-year");
  const endYearInput = document.getElementById("end-year");

  startYearInput.max = params.endYear;
  startYearInput.value = params.startYear;
  endYearInput.max = params.endYear;
  endYearInput.value = params.endYear;

  if (startYear === undefined && endYear === undefined) {
    startYear = params.startYear;
    endYear = params.endYear;
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
    y = [];
    yearlyviews = [];
    yearlyfav = [];
    yearlyPlaylist = [];
    let startYearInt = parseInt(startYear);
    let endYearInt = parseInt(endYear);
    let requests = [];
    while (startYearInt <= endYearInt) {
      requests.push(
        fetchData(dataUrl, "POST", {
          csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
          periode: startYearInt,
        })
      );
      startYearInt++;
    }

    Promise.all(requests)
      .then(function (responses) {
        responses.forEach(function (response) {
          var year = response.map((row) => row.all_year);
          var all_view = response.map((row) => row.all_view_year);
          var year_favo = response.map((row) => row.all_fav_year);
          var year_playlists = response.map((row) => row.all_playlists_year);
          y.push(year[0]);
          yearlyviews.push(all_view[0]);
          yearlyfav.push(year_favo[0]);
          yearlyPlaylist.push(year_playlists[0]);
        });


        let sortedData = y.map((item, index) => {
          return {
            year: item,
            views: yearlyviews[index],
            favorite: yearlyfav[index],
            playlists: yearlyPlaylist[index],
          };
        }).sort((a, b) => a.year - b.year);

        year = sortedData.map((item) => item.year);
        yearlyviews = sortedData.map((item) => item.views);
        yearlyfav = sortedData.map((item) => item.favorite);
        yearlyPlaylist = sortedData.map((item) => item.playlists);


        var ctx = document.getElementById("yearChart").getContext("2d");
        if (yearChart) {
          yearChart.destroy();
        }

        var datasets = [
          {
            label: gettext("Views"),
            animations: {
              y: {
                duration: params.animationDuration,
                delay: params.animationDelay,
              },
            },
            backgroundColor: "#ed184e",
            borderColor: "#ed184e",
            borderWidth: params.borderWidth,
            data: yearlyviews,
            tension: params.tension,
          },
          {
            label: gettext("Favorites"),
            backgroundColor: "#3871c1",
            borderColor: "#3871c1",
            borderWidth: params.borderWidth,
            data: yearlyfav,
            tension: params.tension,
          },
          {
            label: gettext("Playlists addition"),
            backgroundColor: "#1F7C85",
            borderColor: "#1F7C85",
            borderWidth: params.borderWidth,
            data: yearlyPlaylist,
            tension: params.tension,
          },
        ];

        yearChart = new Chart(ctx, {
          type: "line",
          data: {
            labels: year,
            datasets: datasets,
          },
          options: {
            animations: {
              y: {
                easing: "easeInOutElastic",
                from: (ctx) => {
                  if (ctx.type === "data") {
                    if (ctx.mode === "default" && !ctx.dropped) {
                      ctx.dropped = true;
                      return 0;
                    }
                  }
                },
              },
            },
          },
        });
      })
      .catch(function (error) {
        console.log(error);
      });
  }

  document.getElementById("export-btn").addEventListener("click", function () {
    var dataForCSV = {
      headers: [gettext("Years"), gettext('Views'), gettext('Favorites'), gettext('Playlists_addition')],
      rows: []
    }
    for (let i = 0; i < year.length; i++) {
      dataForCSV.rows.push([year[i], yearlyviews[i], yearlyfav[i], yearlyPlaylist[i]])
    }
    exportDataToCSV(dataForCSV, "stats-global.csv")
  });

}))();
