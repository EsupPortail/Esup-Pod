$(() => {
  let data_url = window.location.href;
  
  // Tạo biểu đồ
  let ctx = document.getElementById("myChart").getContext("2d");
  let myChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [
        gettext("During the day"),
        gettext("During the month"),
        gettext("During the year"),
        gettext("Total from creation"),
      ],
      datasets: [
        {
          label: gettext("View"),
          backgroundColor: "rgba(255, 99, 132, 0.2)",
          borderColor: "rgba(255, 99, 132, 1)",
          borderWidth: 1,
          data: [],
        },
        {
          label: gettext("Favorite"),
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          borderColor: "rgba(54, 162, 235, 1)",
          borderWidth: 1,
          data: [],
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: { display: true },
        y: { beginAtZero: true },
      },
    },
  });
  
  // Lấy dữ liệu từ URL và cập nhật biểu đồ
  fetch(data_url)
    .then((response) => response.json())
    .then((data) => {
      data.forEach((item) => {
      alert("day " + item.day);

        myChart.data.datasets[0].data.push(item.day);
        myChart.data.datasets[1].data.push(item.fav_since_created);
      });
      myChart.update();
    })
    .catch((error) => console.error(error));
});
