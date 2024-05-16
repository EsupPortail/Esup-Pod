module.exports = {
  "env": {
    "browser": true,
    "commonjs": false,
    "es2021": true,
    "node": false
  },
  "extends": "eslint:recommended",
  "parserOptions": {
    "ecmaVersion": "latest",
    "sourceType": "script"
  },
  "rules": {
    "indent": [
      "error",
      2,
      {"SwitchCase": 1}
    ],
    "linebreak-style": [
      "error",
      "unix"
    ],
    "semi": [
      "error",
      "always",
    ],
    /*"camelcase": ["warn", {"ignoreGlobals": true}],*/
    /* First capital letter is reserved for "new" Objects. */
    "new-cap": ["warn", { "capIsNew": true }]
  },
  /* functions and Objects that will not trigger a "not defined" error. */
  "globals": {
    "Cookies": "readonly",
    "gettext": "readonly",
    "ngettext": "readonly",
    "interpolate": "readonly",
    "bootstrap": "readonly",
    "videojs": "readonly",
    "CKEDITOR": "readonly",
    "send_form_data": "writable",
    "showalert": "writable",
    "showLoader": "writable",
    "manageDisableBtn": "writable"
  }
};
