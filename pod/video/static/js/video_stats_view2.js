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

    function fetchData(da) {
      console.log(" DATA :", da);
      return new Promise(function (resolve, reject) {
        $.ajax({
          url: data_url,
          method: "POST",
          dataType: "json",
          data: {
            csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
            periode: da,
          },
          success: function (data) {
            console.log(" DATA succes :", da);
            var date = data.map((row) => row.date);
            var day = data.map((row) => row.day);
            var fav_day = data.map((row) => row.fav_day);
            daily.push(date[0]);
            // console.log("daily :", daily);
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
      let da = currentDate.toISOString().split("T")[0];
      console.log("date 1 : ",da);
      requests.push(fetchData(da));
      currentDate.setDate(currentDate.getDate() + 1);
    }

    Promise.all(requests)
      .then(function () {
        let sortedData = daily.map((item, index) => {
          return {
            date: item,
            views: dailyviews[index],
            favo: dailyfavo[index]
          };
        }).sort((a, b) => new Date(a.date) - new Date(b.date));
        daily = sortedData.map(item => item.date);
        dailyviews = sortedData.map(item => item.views);
        dailyfavo = sortedData.map(item => item.favo);
        
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
