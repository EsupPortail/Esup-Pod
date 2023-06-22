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
  
  function createTable() {
    $("#grid").jqGrid({
      url: data_url,
      datatype: "json",
      mtype: "POST",
      styleUI: "Bootstrap5",
      iconSet: "Bootstrap5",
      width: 1700,
      colNames: [
        "<div class='col-name'>" + gettext("Title") + "</div>",
        "<div class='col-name'>" + gettext("View during the day") + "</div>",
        "<div class='col-name'>" + gettext("View during the month") + "</div>",
        "<div class='col-name'>" + gettext("View during the year") + "</div>",
        "<div class='col-name'>" + gettext("Total view from creation") + "</div>",
        "<div class='col-name'>" + gettext("Favorite additions during the day")+ "</div>",
        "<div class='col-name'>" + gettext("Favorite additions during the month")+ "</div>",
        "<div class='col-name'>" + gettext("Favorite additions during the year") + "</div>",
        "<div class='col-name'>" + gettext("Total favorite additions from creation")+ "</div>",
        "<div class='col-name'>" + gettext("Slug") + "</div>",
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
        let min_date = data.filter((obj) => obj.min_date !== undefined);
        // remove date_min in data
        data.pop();
        document.querySelector("#jsperiode").min = min_date[0].min_date;
      },
      postData: {
        csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
      },
    });
  }

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

  $("#filtered").change(function () {
    const selectedValue = $(this).val();
    createTable();

    if (selectedValue === "all") {
      $('#grid').jqGrid('showCol',["title",'day','month','year','since_created','fav_day','fav_month','fav_year','fav_since_created'])
      
    } else if (selectedValue === "views") {
      $('#grid').jqGrid('showCol',["title",'day','month','year','since_created']);
      $("#grid").jqGrid('hideCol',['fav_day','fav_month','fav_year','fav_since_created']);
      

    } else {
      $('#grid').jqGrid('showCol',["title",'fav_day','fav_month','fav_year','fav_since_created']);
      $("#grid").jqGrid('hideCol',['day','month','year','since_created']);

    }

  });

  $("#filtered").val("all").change();
});
