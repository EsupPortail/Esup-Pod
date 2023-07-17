(function () {
  var dateChart;
  var startDate;
  var endDate;
  let d = [];
  let dailyviews = [];
  let dailyfavo = [];
  let dailyPlaylists = [];
  let today = new Date();
  let dataUrl = window.location.href;

  var defaultParams = {
    startDateDefault: new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
    endDateDefault: today.toISOString().split("T")[0],
    tension: 0.5,
    borderWidth: 2,
    animationDuration: 2000,
    animationDelay: 500,
  };
  var params = Object.assign({}, defaultParams);

  const startDateInput = document.getElementById("start-date");
  const endDateInput = document.getElementById("end-date");

  startDateInput.value = params.startDateDefault;
  startDateInput.max = params.endDateDefault;
  endDateInput.value = params.endDateDefault;
  endDateInput.max = params.endDateDefault;

  if (startDate === undefined && endDate === undefined) {
    startDate = params.startDateDefault;
    endDate = params.endDateDefault;
    updateChart();
  }

  startDateInput.addEventListener("change", function () {
    startDate = $(this).val(); // TODO
    document.getElementById("end-date").min = new Date(startDate).toISOString().split("T")[0];
    updateChart();
  })

  endDateInput.addEventListener("change", function () {
    endDate = $(this).val();
    document.getElementById("start-date").max = new Date(endDate).toISOString().split("T")[0];
    updateChart();
  })

  function updateChart() {
    d = [];
    dailyviews = [];
    dailyfavo = [];
    dailyPlaylists = [];
    let currentDate = new Date(startDate);
    let targetDate = new Date(endDate);


    let requests = [];
    while (currentDate <= targetDate) {
      let data = currentDate.toISOString().split("T")[0];
      requests.push(fetchData(dataUrl, "POST", { csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(), periode: data }));
      currentDate.setDate(currentDate.getDate() + 1);
    }


    Promise.all(requests)
      .then(function (responses) {
        responses.forEach(function (response) {
          var date = response.map((row) => row.date);
          var day = response.map((row) => row.day);
          var fav_day = response.map((row) => row.fav_day);
          var playlist_day = response.map((row) => row.playlist_day);
          d.push(date[0]);
          dailyviews.push(day[0]);
          dailyfavo.push(fav_day[0]);
          dailyPlaylists.push(playlist_day[0]);
        });


        let sortedData = d
          .map((item, index) => {
            return {
              date: item,
              views: dailyviews[index],
              favo: dailyfavo[index],
              playlists: dailyPlaylists[index],
            };
          })
          .sort((a, b) => new Date(a.date) - new Date(b.date));

        daily = sortedData.map((item) => item.date);
        dailyviews = sortedData.map((item) => item.views);
        dailyfavo = sortedData.map((item) => item.favo);
        dailyPlaylists = sortedData.map((item) => item.playlists);

        console.log(daily);
        var ctx = document.getElementById("dateChart").getContext("2d");
        if (dateChart) {
          dateChart.destroy();
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
            data: dailyviews,
            tension: params.tension,
          },
          {
            label: gettext("Favorites"),
            backgroundColor: "#3871c1",
            borderColor: "#3871c1",
            borderWidth: params.borderWidth,
            data: dailyfavo,
            tension: params.tension,
          },
          {
            label: gettext("Playlists addition"),
            backgroundColor: "#1F7C85",
            borderColor: "#1F7C85",
            borderWidth: params.borderWidth,
            data: dailyPlaylists,
            tension: params.tension,
          },
        ];

        dateChart = new Chart(ctx, {
          type: "line",
          data: {
            labels: daily,
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
      headers: [gettext("Date"), gettext('Views'), gettext('Favorites'), gettext('Playlists_addition')],
      rows: []
    }
    for (let i = 0; i < daily.length; i++) {
      dataForCSV.rows.push([daily[i], dailyviews[i], dailyfavo[i], dailyPlaylists[i]])
    }
    exportDataToCSV(dataForCSV, "stats-video.csv")
  });

})();
