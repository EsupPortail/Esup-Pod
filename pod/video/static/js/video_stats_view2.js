$(function () {
  let data_url = window.location.href;

  // Khởi tạo mảng dữ liệu cho biểu đồ
  let chartData = [];

  // Lấy dữ liệu từ URL
  $.ajax({
    url: data_url,
    method: "POST",
    dataType: "json",
    data: {
      csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
    },
    success: function (data) {
      // Tạo dữ liệu cho biểu đồ từ dữ liệu trả về
      for (let i = 0; i < data.length; i++) {
        let rowData = data[i];
        chartData.push(rowData);
      }

      // Khởi tạo biểu đồ bằng Chart.js
      var ctx = document.getElementById("myChart").getContext("2d");
      var day = chartData.map((row) => row.day);
      var month = chartData.map((row) => row.month);
      var year = chartData.map((row) => row.year);
      var since_created = chartData.map((row) => row.since_created);
      var fav_day = chartData.map((row) => row.fav_day);
      var fav_month = chartData.map((row) => row.fav_month);
      var fav_year = chartData.map((row) => row.fav_year);
      var fav_since_created = chartData.map((row) => row.fav_since_created);
      var myChart = new Chart(ctx, {
        type: "line",
        data: {
          // labels: chartData.map((row) => row.title),
          labels: [
            gettext("During the day"),
            gettext("During the month"),
            gettext("During the year"),
            gettext("Total from creation"),
          ],
          datasets: [
            {
              label: gettext("View"),
              backgroundColor: "#DC143C",
              borderColor: "#DC143C",
              borderWidth: 1,
              data: [day[0], month[0], year[0], since_created[0]],
              tension: 0.5,
            },
            {
              label: gettext("Favorite"),
              backgroundColor: "#1F7C85",
              borderColor: "#1F7C85",
              borderWidth: 1,
              data: [fav_day[0], fav_month[0], fav_year[0], fav_since_created[0]],
              tension: 0.5,
            },
            // Thêm các dataset khác tương tự
          ],
        },
        options: {
          scales: {
            y: {
              beginAtZero: true,
            },
          },
        },
      });
    },
    error: function (error) {
      console.log(error);
    },
  });
});
