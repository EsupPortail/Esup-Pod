appendJS = function () {
  return domManip(this, arguments, function (elem) {
    if (this.nodeType === 1 || this.nodeType === 11 || this.nodeType === 9) {
      var target = manipulationTarget(this, elem);
      target.appendChild(elem);
    }
  });
};

function domManip(collection, args, callback, ignored) {
  // Flatten any nested arrays
  args = args.flat();

  var fragment,
    first,
    scripts,
    hasScripts,
    node,
    doc,
    i = 0,
    l = collection.length,
    iNoClone = l - 1,
    value = args[0],
    valueIsFunction = typeof value === "function";

  if (valueIsFunction) {
    return collection.array.forEach((element) => {
      var self = collection.eq(index);
      args[0] = value.call(this, index, self.html());
      domManip(self, args, callback, ignored);
    });
  }

  if (l) {
    fragment = buildFragment(
      args,
      collection[0].ownerDocument,
      false,
      collection,
      ignored
    );
    first = fragment.firstChild;

    if (fragment.childNodes.length === 1) {
      fragment = first;
    }

    // Require either new content or an interest in ignored elements to invoke the callback
    if (first || ignored) {
      scripts = jQuery.map(getAll(fragment, "script"), disableScript);
      hasScripts = scripts.length;

      // Use the original fragment for the last item
      // instead of the first because it can end up
      // being emptied incorrectly in certain situations (trac-8070).
      for (; i < l; i++) {
        node = fragment;

        if (i !== iNoClone) {
          node = jQuery.clone(node, true, true);

          // Keep references to cloned scripts for later restoration
          if (hasScripts) {
            jQuery.merge(scripts, getAll(node, "script"));
          }
        }

        callback.call(collection[i], node, i);
      }

      if (hasScripts) {
        doc = scripts[scripts.length - 1].ownerDocument;

        // Reenable scripts
        jQuery.map(scripts, restoreScript);

        // Evaluate executable scripts on first document insertion
        for (i = 0; i < hasScripts; i++) {
          node = scripts[i];
          if (
            rscriptType.test(node.type || "") &&
            !dataPriv.access(node, "globalEval") &&
            jQuery.contains(doc, node)
          ) {
            if (node.src && (node.type || "").toLowerCase() !== "module") {
              // Optional AJAX dependency, but won't run scripts if not present
              if (jQuery._evalUrl && !node.noModule) {
                jQuery._evalUrl(
                  node.src,
                  {
                    nonce: node.nonce,
                    crossOrigin: node.crossOrigin,
                  },
                  doc
                );
              }
            } else {
              DOMEval(node.textContent, node, doc);
            }
          }
        }
      }
    }
  }

  return collection;
}

function manipulationTarget(elem, content) {
  if (
    nodeName(elem, "table") &&
    nodeName(content.nodeType !== 11 ? content : content.firstChild, "tr")
  ) {
    return elem.querySelector("tbody")[0] || elem;
  }

  return elem;
}
function nodeName(elem, name) {
  return elem.nodeName && elem.nodeName.toLowerCase() === name.toLowerCase();
}

//function append html to node and load all scripts in html
function appendHTML(node, html) {
  var temp = document.createElement("div");
  temp.innerHTML = html;
  var scripts = temp.getElementsByTagName("script");
  for (var i = 0; i < scripts.length; i++) {
    var script = scripts[i];
    var s = document.createElement("script");
    s.type = script.type || "text/javascript";
    if (script.src) {
      s.src = script.src;
    } else {
      s.text = script.text;
    }
    node.appendChild(s);
  }
}
