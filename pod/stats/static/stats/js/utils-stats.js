function fetchData(url, method, data) {
  return new Promise(function (resolve, reject) {
    $.ajax({
      url: url,
      method: method,
      dataType: "json",
      data: data,
      success: function (response) {
        resolve(response);
      },
      error: function (error) {
        reject(error);
      },
    });
  });
}

function exportDataToCSV(data, filename) {
  let csvContent = "data:text/csv;charset=utf-8,";
  csvContent += data.headers.join(",") + "\n";
  for (let i = 0; i < data.rows.length; i++) {
    let row = data.rows[i].join(",") + "\n";
    csvContent += row;
  }
  var encodedUri = encodeURI(csvContent);
  var link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
}
