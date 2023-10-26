let result,
  verb,
  context,
  object = {};
let timestamp = "";

function create_UUID() {
  var dt = new Date().getTime();
  var uuid = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
    /[xy]/g,
    function (c) {
      var r = (dt + Math.random() * 16) % 16 | 0;
      dt = Math.floor(dt / 16);
      return (c == "x" ? r : (r & 0x3) | 0x8).toString(16);
    },
  );
  return uuid;
}

const createStatement = function () {
  var statement = {
    verb: verb,
    timestamp: timestamp,
    object: object,
  };
  statement["context"] = context;
  if (Object.keys(result).length > 0) {
    statement["result"] = result;
  }
  return statement;
};

async function sendStatement(stmt) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken,
    },
    mode: "same-origin",
    body: JSON.stringify(stmt),
  });
  response.json().then((data) => {
    console.log(data);
  });
}
