$(function () {
  $("#validate-btn").click(function () {
    var startDate = document.getElementById("start-date").value;
    var endDate = document.getElementById("end-date").value;
    console.log("date commence:", startDate);
    console.log("date fini:", endDate);

    let data_url = window.location.href;
    let daily = [];
    let dailyviews = [];
    let dailyfavo = [];

    function fetchData(date) {
      return new Promise(function (resolve, reject) {
        $.ajax({
          url: data_url,
          method: "POST",
          dataType: "json",
          data: {
            csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
            periode: date,
          },
          success: function (data) {
            var date = data.map((row) => row.date);
            var day = data.map((row) => row.day);
            var fav_day = data.map((row) => row.fav_day);
            daily.push(date[0]);
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

    var currentDate = new Date(startDate);
    var targetDate = new Date(endDate);

    var requests = [];
    while (currentDate <= targetDate) {
      requests.push(fetchData(currentDate.toISOString().split("T")[0]));
      currentDate.setDate(currentDate.getDate() + 1);
    }

    Promise.all(requests)
      .then(function () {
        console.log("date", daily);
        console.log("views :", dailyviews);
        console.log("favorite : ", dailyfavo);

        var ctx = document.getElementById("myChart").getContext("2d");

        var myChart = new Chart(ctx, {
          type: "line",
          data: {
            labels: daily,
            datasets: [
              {
                label: gettext("View"),
                animations: {
                  y: {
                    duration: 2000,
                    delay: 500
                  }
                },
                backgroundColor: "#DC143C",
                borderColor: "#DC143C",
                borderWidth: 1,
                data: dailyviews,
                tension: 0.5,
              },
              {
                label: gettext("Favorite"),
                backgroundColor: "#1F7C85",
                borderColor: "#1F7C85",
                borderWidth: 1,
                data: dailyfavo,
                tension: 0.5,
                fill: 1,
              },
            ],
          },
          options: {
            animations: {
              y: {
                easing: 'easeInOutElastic',
                from: (ctx) => {
                  if (ctx.type === 'data') {
                    if (ctx.mode === 'default' && !ctx.dropped) {
                      ctx.dropped = true;
                      return 0;
                    }
                  }
                }
              }
            },
          },
        });
      })
      .catch(function (error) {
        console.log(error);
      });
  });
});
