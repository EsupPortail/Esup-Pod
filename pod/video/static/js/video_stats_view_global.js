$(function () {
  var yearChart;
  var startYear;
  var endYear;
  let y = [];
  let yearlyviews = [];
  let today = new Date();
  let data_url = window.location.href;

  let startYearDefault = today.getFullYear() - 5;
  $("#start-year").val(startYearDefault); // set year input value to current year - 5
  document.querySelector("#start-year").max = today.getFullYear();
  $("#end-year").val(today.getFullYear()); // set year input value to current year
  document.querySelector("#end-year").max = today.getFullYear();

  if (startYear === undefined && endYear === undefined) {
      startYear = startYearDefault;
      endYear = today.getFullYear();
      updateChart();
  }

  $("#start-year").change(function () {
      startYear = parseInt($(this).val());
      document.querySelector("#end-year").min = startYear;
      updateChart();
  });

  $("#end-year").change(function () {
      endYear = parseInt($(this).val());
      document.querySelector("#start-year").max = endYear;
      updateChart();
  });

  function fetchData(year) {
      return new Promise(function (resolve, reject) {
          $.ajax({
              url: data_url,
              method: "POST",
              dataType: "json",
              data: {
                  csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
                  periode: year,
              },
              success: function (data) {
                  var year = data.map((row) => row.all_year);
                  var all_view = data.map((row) => row.all_view_year);
                  var year_favo = data.map((row) => row.all_fav_year);
                  y.push(year[0]);
                  yearlyviews.push(all_view[0]);
                  yearlyfav.push(year_favo[0]);
                  resolve();
              },
              error: function (error) {
                  reject(error);
              },
          });
      });
  }

  function updateChart() {
      y = [];
      yearlyviews = [];
      yearlyfav = [];
      let startYearInt = parseInt(startYear);
      let endYearInt = parseInt(endYear);
      let requests = [];
      while (startYearInt <= endYearInt ) {
          requests.push(fetchData(startYearInt));
          startYearInt++;
      }

      Promise.all(requests)
          .then(function () {
              let sortedData = y
                  .map((item, index) => {
                      return {
                          year: item,
                          views: yearlyviews[index],
                          favorite : yearlyfav[index],
                      };
                  })
                  .sort((a, b) => a.year - b.year);
              year = sortedData.map((item) => item.year);
              yearlyviews = sortedData.map((item) => item.views);
              yearlyfavo = sortedData.map((item) => item.favorite);

              var ctx = document.getElementById("yearChart").getContext("2d");
              if (yearChart) {
                  yearChart.destroy();
              }
              yearChart = new Chart(ctx, {
                  type: "line",
                  data: {
                      labels: year,
                      datasets: [
                          {
                            label: gettext("Views"),
                            animations: {
                                y: {
                                    duration: 2000,
                                    delay: 500,
                                },
                            },
                            backgroundColor: "#DC143C",
                            borderColor: "#DC143C",
                            borderWidth: 2,
                            data: yearlyviews,
                            tension: 0.5,
                          },
                          {
                            label: gettext("Favorites"),
                            backgroundColor: "#1F7C85",
                            borderColor: "#1F7C85",
                            borderWidth: 2,
                            data: yearlyfavo,
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

  // Function to export data in CSV format
  function exportToCSV() {
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += gettext("Date,Views,Favorites");
    csvContent += "\n";
    for (let i = 0; i < year.length; i++) {
      let row = year[i] + "," + yearlyviews[i] + "," + yearlyfav[i] + "\n";
      csvContent += row;
    }
    var encodedUri = encodeURI(csvContent);
    var link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "data.csv");
    document.body.appendChild(link);
    link.click();
  }

  $("#export-btn").click(function () {
    exportToCSV();
  });
});
