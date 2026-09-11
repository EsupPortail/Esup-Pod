/**
 * @file Esup-Pod Tests for comment scripts
 * Prevent regressions in comment-script.js
 */

const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const vm = require("node:vm");
const { FakeElement } = require("../../../test-utils.cjs");

const source = fs.readFileSync(
  new URL("./comment-script.js", `file://${__dirname}/`),
  "utf8",
);
const classSource = source.match(
  /class CommentSince extends HTMLElement \{[\s\S]*?^\}/m,
)?.[0];

if (!classSource) throw new Error("CommentSince class not found");

// Create a CommentSince instance in a minimal browser context.
function createCommentSince() {
  const context = {
    HTMLElement: FakeElement,
    dayjs: () => ({ fromNow: () => "à l’instant" }),
    window: { setInterval() {} },
    document: {
      // Create a minimal fake DOM element.
      createElement() {
        return new FakeElement();
      },
    },
  };
  vm.runInNewContext(`${classSource}; this.CommentSince = CommentSince;`, context);
  return new context.CommentSince();
}

// Ensure construction without the since attribute does not throw.
test("CommentSince does not fail before its since attribute is set", () => {
  assert.doesNotThrow(() => createCommentSince());
});

// Ensure the component initializes when the since attribute is available.
test("CommentSince initializes after its since attribute is set", () => {
  const commentSince = createCommentSince();
  commentSince.setAttribute("since", "2026-09-11T10:00:00Z");

  assert.doesNotThrow(() => commentSince.connectedCallback());
  assert.equal(commentSince.children.length, 1);
  assert.equal(commentSince.children[0].innerText, "à l’instant");
});
