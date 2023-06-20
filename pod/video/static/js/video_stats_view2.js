$(function () {
  var myChart;
  var startDate;
  var endDate;
  let d = [];
  let dailyviews = [];
  let dailyfavo = [];
  let today = new Date();
  let data_url = window.location.href;

  let startDateDefault = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];
  $("#start-date").val(startDateDefault); // set date input value to today - 7 days
  document.querySelector("#start-date").max = today.toISOString().split("T")[0];
  $("#end-date").val(today.toISOString().split("T")[0]); // set date input value to today
  document.querySelector("#end-date").max = today.toISOString().split("T")[0];


  if (startDate === undefined && endDate === undefined) {
    startDate = startDateDefault;
    endDate = today.toISOString().split("T")[0];
    updateChart();
  }

  $("#start-date").change(function () {
    startDate = $(this).val();
    document.querySelector("#end-date").min = new Date(startDate).toISOString().split("T")[0];
    updateChart();
  });

  $("#end-date").change(function () {
    endDate = $(this).val();
    document.querySelector("#start-date").max = new Date(endDate).toISOString().split("T")[0];
    updateChart();
  });

  function fetchData(data) {
    return new Promise(function (resolve, reject) {
      $.ajax({
        url: data_url,
        method: "POST",
        dataType: "json",
        data: {
          csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
          periode: data,
        },
        success: function (data) {
          var date = data.map((row) => row.date);
          var day = data.map((row) => row.day);
          var fav_day = data.map((row) => row.fav_day);
            d.push(date[0]);
            dailyviews.push(day[0]);
            dailyfavo.push(fav_day[0]);
          resolve();
        },
        error: function (error) {
          reject(error);
        },
      });
    });
  }

  function updateChart() {
      d = [];
      dailyviews = [];
      dailyfavo = [];
      let currentDate = new Date(startDate);
      let targetDate = new Date(endDate);

      let requests = [];
      while (currentDate <= targetDate) {
        let data = currentDate.toISOString().split("T")[0];
        requests.push(fetchData(data));
        currentDate.setDate(currentDate.getDate() + 1);
      }

      Promise.all(requests)
        .then(function () {
          let sortedData = d
            .map((item, index) => {
              return {
                date: item,
                views: dailyviews[index],
                favo: dailyfavo[index],
              };
            })
            .sort((a, b) => new Date(a.date) - new Date(b.date));
          daily = sortedData.map((item) => item.date);
          dailyviews = sortedData.map((item) => item.views);
          dailyfavo = sortedData.map((item) => item.favo);

          var ctx = document.getElementById("myChart").getContext("2d");
          if (myChart) {
            myChart.destroy();
          }
          myChart = new Chart(ctx, {
            type: "line",
            data: {
              labels: daily,
              datasets: [
                {
                  label: gettext("View"),
                  animations: {
                    y: {
                      duration: 2000,
                      delay: 500,
                    },
                  },
                  backgroundColor: "#DC143C",
                  borderColor: "#DC143C",
                  borderWidth: 2,
                  data: dailyviews,
                  tension: 0.5,
                },
                {
                  label: gettext("Favorite"),
                  backgroundColor: "#1F7C85",
                  borderColor: "#1F7C85",
                  borderWidth: 2,
                  data: dailyfavo,
                  tension: 0.5,
                },
              ],
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

});
