/* ===========================================================================
   Jacaranda — interaction layer. Vanilla, inline, no dependencies.
   Every effect degrades to a readable page if it fails.
   =========================================================================== */
(function () {
  "use strict";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- 1. scroll progress + sticky nav ---------- */
  var bar = document.querySelector(".progress");
  var nav = document.querySelector("header.nav");
  function onScroll() {
    var h = document.documentElement;
    var p = h.scrollTop / (h.scrollHeight - h.clientHeight || 1);
    if (bar) bar.style.width = (p * 100).toFixed(2) + "%";
    if (nav) nav.classList.toggle("stuck", h.scrollTop > 24);
  }
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- 2. cursor light ---------- */
  var glow = document.querySelector(".cursor-glow");
  if (glow && !reduce && matchMedia("(pointer:fine)").matches) {
    addEventListener("pointermove", function (e) {
      glow.style.setProperty("--mx", e.clientX + "px");
      glow.style.setProperty("--my", e.clientY + "px");
    }, { passive: true });
  }

  /* ---------- 3. reveal on scroll ---------- */
  var revealables = document.querySelectorAll(".rv");
  if ("IntersectionObserver" in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    revealables.forEach(function (el) { io.observe(el); });
  } else {
    revealables.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---------- 4. counters ---------- */
  function countUp(el) {
    var to = parseFloat(el.dataset.count || "0");
    var suffix = el.dataset.suffix || "";
    if (reduce) { el.textContent = to + suffix; return; }
    var t0 = performance.now(), dur = 1100;
    function step(t) {
      var k = Math.min(1, (t - t0) / dur);
      var e = 1 - Math.pow(1 - k, 3);
      el.textContent = Math.round(to * e) + suffix;
      if (k < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  var counters = document.querySelectorAll("[data-count]");
  if ("IntersectionObserver" in window) {
    var cio = new IntersectionObserver(function (es) {
      es.forEach(function (en) { if (en.isIntersecting) { countUp(en.target); cio.unobserve(en.target); } });
    }, { threshold: 0.4 });
    counters.forEach(function (el) { cio.observe(el); });
  } else {
    counters.forEach(countUp);
  }

  /* ---------- 5. card tilt ---------- */
  if (!reduce && matchMedia("(pointer:fine)").matches) {
    document.querySelectorAll("[data-tilt]").forEach(function (card) {
      card.addEventListener("pointermove", function (e) {
        var r = card.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width - 0.5;
        var py = (e.clientY - r.top) / r.height - 0.5;
        card.style.transform = "perspective(900px) rotateX(" + (-py * 6).toFixed(2) +
          "deg) rotateY(" + (px * 8).toFixed(2) + "deg) translateY(-3px)";
      });
      card.addEventListener("pointerleave", function () { card.style.transform = ""; });
    });
  }

  /* ---------- 6. venture dialog ---------- */
  var modal = document.getElementById("venture-modal");
  if (modal && typeof modal.showModal === "function") {
    document.querySelectorAll("[data-venture]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var v = JSON.parse(btn.getAttribute("data-venture"));
        modal.querySelector("[data-v-kicker]").textContent = v.kicker;
        modal.querySelector("[data-v-name]").textContent = v.name;
        modal.querySelector("[data-v-line]").textContent = v.line || "";
        var dl = modal.querySelector("[data-v-facts]");
        dl.innerHTML = "";
        (v.facts || []).forEach(function (pair) {
          var dt = document.createElement("dt"); dt.textContent = pair[0];
          var dd = document.createElement("dd"); dd.textContent = pair[1];
          dl.appendChild(dt); dl.appendChild(dd);
        });
        var link = modal.querySelector("[data-v-link]");
        link.href = v.url; link.textContent = v.cta;
        var buyBtn = modal.querySelector("[data-v-buy]");      // the storefront lives here too
        if (buyBtn) {
          if (v.buy) { buyBtn.href = v.buy; buyBtn.textContent = v.buy_label || ("Buy · " + v.from); buyBtn.hidden = false; }
          else { buyBtn.hidden = true; }
        }
        modal.showModal();
      });
    });
    modal.addEventListener("click", function (e) {
      if (e.target === modal || e.target.matches(".close")) modal.close();
    });
  }

  /* ---------- 7. publication filter + search ---------- */
  var chips = document.querySelectorAll("[data-filter]");
  var cards = Array.prototype.slice.call(document.querySelectorAll("[data-work]"));
  var search = document.getElementById("wsearch");
  var empty = document.getElementById("wempty");
  var state = { group: "all", q: "" };

  function apply() {
    var shown = 0;
    cards.forEach(function (c) {
      var okGroup = state.group === "all" || c.dataset.group === state.group;
      var okQuery = !state.q || c.dataset.haystack.indexOf(state.q) !== -1;
      var ok = okGroup && okQuery;
      c.hidden = !ok;
      if (ok) shown++;
    });
    if (empty) empty.hidden = shown !== 0;
    var count = document.getElementById("wcount");
    if (count) count.textContent = shown;
  }
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      chips.forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });
      state.group = chip.dataset.filter;
      apply();
    });
  });
  if (search) {
    search.addEventListener("input", function () {
      state.q = search.value.trim().toLowerCase();
      if (state.q && state.group !== "all") {          // a search is never silently scoped to a chip
        state.group = "all";
        chips.forEach(function (c) { c.setAttribute("aria-pressed", String(c.dataset.filter === "all")); });
      }
      apply();
    });
  }
  if (cards.length) apply();

  /* ---------- 8. command palette ---------- */
  var pal = document.getElementById("palette");
  if (pal && typeof pal.showModal === "function") {
    var pinput = pal.querySelector("input");
    var plist = pal.querySelector("ul");
    var items = [];
    (window.__index || []).forEach(function (it) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = it.url;
      a.innerHTML = '<span class="ptitle"></span><span class="pkind"></span>';
      a.querySelector(".ptitle").textContent = it.title;
      a.querySelector(".pkind").textContent = it.kind;
      li.appendChild(a); plist.appendChild(li);
      items.push({ li: li, hay: (it.title + " " + it.kind + " " + (it.sub || "")).toLowerCase() });
    });
    var sel = 0;
    function render() {
      var q = pinput.value.trim().toLowerCase();
      var n = 0;
      items.forEach(function (it) {
        var on = !q || it.hay.indexOf(q) !== -1;
        it.li.hidden = !on;
        if (on && n === 0) { it.li.setAttribute("aria-selected", "true"); sel = items.indexOf(it); }
        else it.li.removeAttribute("aria-selected");
        if (on) n++;
      });
      var empty = plist.querySelector(".pempty");
      if (!empty) {
        empty = document.createElement("li");
        empty.className = "pempty";
        empty.textContent = "No match. Try a title, a venture or a kind.";
        plist.appendChild(empty);
      }
      empty.hidden = n !== 0;
    }
    function openPal() { pal.showModal(); pinput.value = ""; render(); pinput.focus(); }
    document.querySelectorAll("[data-open-palette]").forEach(function (b) {
      b.addEventListener("click", openPal);
    });
    addEventListener("keydown", function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openPal(); }
      if (e.key === "/" && document.activeElement.tagName !== "INPUT") { e.preventDefault(); openPal(); }
      if (!pal.open) return;
      var vis = items.filter(function (i) { return !i.li.hidden; });
      if (!vis.length) { if (e.key === "Escape") pal.close(); return; }
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        var idx = vis.findIndex(function (i) { return i.li.getAttribute("aria-selected") === "true"; });
        idx = (idx + (e.key === "ArrowDown" ? 1 : -1) + vis.length) % vis.length;
        vis.forEach(function (i) { i.li.removeAttribute("aria-selected"); });
        vis[idx].li.setAttribute("aria-selected", "true");
        vis[idx].li.querySelector("a").focus();
      }
      if (e.key === "Escape") pal.close();
    });
    pinput.addEventListener("input", render);
    pal.addEventListener("click", function (e) { if (e.target === pal) pal.close(); });
  }

  /* ---------- 9. pause offscreen video (battery, not politeness) ---------- */
  var vids = document.querySelectorAll("video[data-lazy]");
  if ("IntersectionObserver" in window) {
    var vio = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        var v = en.target;
        if (en.isIntersecting) { v.play().catch(function () {}); } else { v.pause(); }
      });
    }, { threshold: 0.15 });
    vids.forEach(function (v) { vio.observe(v); });
  }

  /* ---------- 10. copy email ---------- */
  document.querySelectorAll("[data-copy]").forEach(function (b) {
    b.addEventListener("click", function () {
      var text = b.getAttribute("data-copy");
      var done = function () {
        var old = b.textContent;
        b.textContent = "Copied";
        setTimeout(function () { b.textContent = old; }, 1400);
      };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, done);
      else done();
    });
  });

  /* ---------- 11. back to top ---------- */
  document.querySelectorAll("[data-top]").forEach(function (b) {
    b.addEventListener("click", function () { scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" }); });
  });
})();
