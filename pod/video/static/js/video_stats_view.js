function linkedCell(cellValue, options, rowObject) {
  return (
    "<a href='" +
    window.location.origin +
    "/video/" +
    rowObject.slug +
    "' target='_blank' rel='noopener'>" +
    cellValue +
    "</a>"
  );
}
$(() => {
  let data_url = window.location.href;
  $("#grid").jqGrid({
    url: data_url,
    datatype: "json",
    mtype: "POST",
    styleUI: "Bootstrap5",
    iconSet: "Bootstrap5",
    colNames: [
      gettext("Title"),
      gettext("View during the day"),
      gettext("View during the month"),
      gettext("View during the year"),
      gettext("Total view from creation"),
      gettext("Playlist additions during the day"),
      gettext("Playlist additions during the month"),
      gettext("Playlist additions during the year"),
      gettext("Total Playlist additions from creation"),
      gettext("Favorite additions during the day"),
      gettext("Favorite additions during the month"),
      gettext("Favorite additions during the year"),
      gettext("Total favorite additions from creation"),
      gettext("Slug"),
    ],
    colModel: [
      {
        name: "title",
        align: "center",
        sortable: true,
        sorttype: "text",
        formatter: linkedCell,
      },
      { name: "day", align: "center", sortable: true, sorttype: "int" },
      { name: "month", align: "center", sortable: true, sorttype: "int" },
      { name: "year", align: "center", sortable: true, sorttype: "int" },
      {
        name: "since_created",
        align: "center",
        sortable: true,
        sorttype: "int",
      },
      {
        name: "playlist_day",
        align: "center",
        sortable: true,
        sorttype: "int",
      },
      {
        name: "playlist_month",
        align: "center",
        sortable: true,
        sorttype: "int",
      },
      {
        name: "playlist_year",
        align: "center",
        sortable: true,
        sorttype: "int",
      },
      {
        name: "playlist_since_created",
        align: "center",
        sortable: true,
        sorttype: "int",
      },
      { name: "fav_day", align: "center", sortable: true, sorttype: "int" },
      { name: "fav_month", align: "center", sortable: true, sorttype: "int" },
      { name: "fav_year", align: "center", sortable: true, sorttype: "int" },
      {
        name: "fav_since_created",
        align: "center",
        sortable: true,
        sorttype: "int",
      },
      {
        name: "slug",
        align: "center",
        sortable: true,
        sorttype: "text",
        hidden: true,
      },
    ],
    loadonce: true,
    rowNum: 10,
    rowList: [10, 15, 20, 25, 30, 50, 100],
    gridview: true,
    autoencode: true,
    pager: "#pager",
    sortorder: "asc",
    beforeProcessing: function (data) {
      // Set min date
      let min_date = data.filter((obj) => {
        return obj.min_date != undefined;
      });
      // remove date_min in data
      data.pop();
      document.querySelector("#jsperiode").min = min_date[0].min_date;
    },
    postData: {
      csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
    },
  });
  let today = new Date().toISOString().split("T")[0];
  $("#jsperiode").val(today); // set date input value to today
  document.querySelector("#jsperiode").max = today;

  $("#jsperiode").on("change paste keyup", function (e) {
    if ($(this).val() != undefined && $(this).val().trim() !== "") {
      try {
        let data = { periode: $(this).val() };
        $("#grid")
          .jqGrid("setGridParam", { datatype: "json", postData: data })
          .trigger("reloadGrid");
      } catch (e) {
        console.log(e);
      }
    }
  });
});
