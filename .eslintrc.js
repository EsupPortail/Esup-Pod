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
    "require": true,
    "process": true,
    "Cookies": "readonly",
    "gettext": "readonly",
    "ngettext": "readonly",
    "interpolate": "readonly",
    "bootstrap": "readonly",
    "videojs": "readonly",
    "tinyMCE": "readonly",
    "send_form_data": "writable",
    "showalert": "writable",
    "showLoader": "writable",
    "manageDisableBtn": "writable"
  },
  overrides: [
    {
      // Allow use of import & export functions
      files: [ "pod/main/static/js/utils.js", "pod/video/static/js/regroup_videos_by_theme.js" ],
      parserOptions: { sourceType: "module" },
    }
  ]
};
