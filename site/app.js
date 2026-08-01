(function () {
  "use strict";

  var state = { query: "", section: "all", data: null };

  var els = {
    search: document.getElementById("search"),
    chips: document.getElementById("chips"),
    results: document.getElementById("results"),
    count: document.getElementById("count"),
    empty: document.getElementById("empty"),
  };

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // Converts a trusted markdown-lite string (only `[text](url)` links) to
  // safe HTML, escaping everything else.
  function renderInlineMarkdown(str) {
    if (!str) return "";
    var linkPattern = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
    var out = "";
    var lastIndex = 0;
    var match;
    while ((match = linkPattern.exec(str)) !== null) {
      out += escapeHtml(str.slice(lastIndex, match.index));
      var text = escapeHtml(match[1]);
      var href = escapeHtml(match[2]);
      out += '<a href="' + href + '" target="_blank" rel="noopener">' + text + "</a>";
      lastIndex = linkPattern.lastIndex;
    }
    out += escapeHtml(str.slice(lastIndex));
    return out;
  }

  function buildChips(sections) {
    var frag = document.createDocumentFragment();
    var all = makeChip("all", "All");
    all.setAttribute("aria-pressed", "true");
    frag.appendChild(all);
    sections.forEach(function (s) {
      frag.appendChild(makeChip(s.id, s.title));
    });
    els.chips.appendChild(frag);
  }

  function makeChip(id, label) {
    var btn = document.createElement("button");
    btn.className = "chip";
    btn.type = "button";
    btn.dataset.section = id;
    btn.setAttribute("aria-pressed", "false");
    btn.textContent = label;
    btn.addEventListener("click", function () {
      state.section = id;
      Array.prototype.forEach.call(els.chips.children, function (c) {
        c.setAttribute("aria-pressed", String(c.dataset.section === id));
      });
      render();
    });
    return btn;
  }

  function matches(entry, query) {
    if (!query) return true;
    var haystack = (entry.name + " " + entry.desc + " " + entry.category).toLowerCase();
    return haystack.indexOf(query) !== -1;
  }

  function render() {
    var query = state.query.trim().toLowerCase();
    var filtered = state.data.entries.filter(function (e) {
      var sectionOk = state.section === "all" || e.sectionId === state.section;
      return sectionOk && matches(e, query);
    });

    els.count.textContent = filtered.length + " result" + (filtered.length === 1 ? "" : "s");
    els.results.innerHTML = "";
    els.empty.hidden = filtered.length !== 0;

    var frag = document.createDocumentFragment();
    filtered.forEach(function (entry) {
      var li = document.createElement("li");
      li.className = "result";

      var cat = document.createElement("span");
      cat.className = "category";
      cat.textContent = entry.category;
      li.appendChild(cat);

      var a = document.createElement("a");
      a.className = "name";
      a.href = entry.url;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = entry.name;
      li.appendChild(a);

      if (entry.desc) {
        var p = document.createElement("p");
        p.className = "desc";
        p.innerHTML = renderInlineMarkdown(entry.desc);
        li.appendChild(p);
      }

      frag.appendChild(li);
    });
    els.results.appendChild(frag);
  }

  function debounce(fn, wait) {
    var t;
    return function () {
      clearTimeout(t);
      var args = arguments;
      t = setTimeout(function () {
        fn.apply(null, args);
      }, wait);
    };
  }

  els.search.addEventListener(
    "input",
    debounce(function (e) {
      state.query = e.target.value;
      render();
    }, 120)
  );

  fetch("data.json")
    .then(function (r) {
      return r.json();
    })
    .then(function (data) {
      state.data = data;
      buildChips(data.sections);
      render();
    })
    .catch(function (err) {
      els.count.textContent = "";
      els.empty.hidden = false;
      els.empty.textContent = "Failed to load data.json: " + err.message;
    });
})();
