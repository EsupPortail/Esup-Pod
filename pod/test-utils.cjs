/**
 * @file Esup-Pod utilities for JS unit tests
 */

// Simulate the DOMTokenList used by classList.
class FakeClassList {
  constructor(...classes) {
    this.classes = new Set(classes);
  }

  contains(className) {
    return this.classes.has(className);
  }

  add(className) {
    this.classes.add(className);
  }

  remove(...classNames) {
    classNames.forEach((className) => this.classes.delete(className));
  }
}

// Provide the minimal DOM element API used by CommentSince.
class FakeElement {
  constructor() {
    this.attributes = new Map();
    this.children = [];
  }

  getAttribute(name) {
    return this.attributes.get(name) ?? null;
  }

  setAttribute(name, value) {
    this.attributes.set(name, value);
  }

  appendChild(child) {
    this.children.push(child);
  }
}

// Provide the button API used by preventRefreshButton.
class FakeButton {
  constructor({ classes = [], attributes = {}, iconClasses = ["bi"] } = {}) {
    this.classList = new FakeClassList(...classes);
    this.attributes = new Map(Object.entries(attributes));
    this.listeners = new Map();
    this.icon = new FakeClassList(...iconClasses);
    this.style = {};
    this.replacedWith = null;
  }

  addEventListener(eventName, listener) {
    this.listeners.set(eventName, listener);
  }

  getAttribute(name) {
    return this.attributes.get(name) ?? null;
  }

  setAttribute(name, value) {
    this.attributes.set(name, value);
  }

  removeAttribute(name) {
    this.attributes.delete(name);
  }

  querySelector(selector) {
    return selector === ".bi" ? { classList: this.icon } : null;
  }

  replaceWith(element) {
    this.replacedWith = element;
  }
}

module.exports = { FakeButton, FakeClassList, FakeElement };
