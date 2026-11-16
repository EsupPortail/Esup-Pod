/**
 * Esup-Pod Xapi scripts
 */
let result,
  verb,
  context,
  object = {};
let timestamp = "";

/**
 * Create an RFC4122 v4 UUID using cryptographically secure randomness.
 * @returns {string}
 */
function create_UUID() {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  if (
    globalThis.crypto &&
    typeof globalThis.crypto.getRandomValues === "function"
  ) {
    const bytes = new Uint8Array(16);
    globalThis.crypto.getRandomValues(bytes);
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  }
  throw new Error("Secure random generator is unavailable.");
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
