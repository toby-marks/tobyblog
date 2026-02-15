(function () {
  "use strict";

  /**
   * CSS Grid Masonry helper.
   * Requires a grid container with:
   *   display: grid;
   *   grid-auto-rows: <px>;
   *   gap: <px>;
   */

  var grids = new Set();
  var scheduled = false;

  function pxInt(v) {
    var n = parseInt(v, 10);
    return Number.isFinite(n) ? n : 0;
  }

  function getGridRowMetrics(grid) {
    var styles = window.getComputedStyle(grid);
    var rowHeight = pxInt(styles.getPropertyValue("grid-auto-rows"));
    // gap can be set via gap / row-gap
    var rowGap = pxInt(styles.getPropertyValue("grid-row-gap")) || pxInt(styles.getPropertyValue("gap"));
    return { rowHeight: rowHeight, rowGap: rowGap };
  }

  function resizeGridItem(item, metrics) {
    if (!item) return;
    var content = item.querySelector(".tb-masonry__content") || item;
    var height = content.getBoundingClientRect().height;
    var span = Math.ceil((height + metrics.rowGap) / (metrics.rowHeight + metrics.rowGap));
    item.style.gridRowEnd = "span " + span;
  }

  function resizeAll(grid) {
    if (!grid) return;
    var metrics = getGridRowMetrics(grid);
    if (!metrics.rowHeight) return;

    var items = grid.querySelectorAll(".tb-masonry__item");
    for (var i = 0; i < items.length; i++) {
      resizeGridItem(items[i], metrics);
    }
  }

  function scheduleRelayout() {
    if (scheduled) return;
    scheduled = true;

    window.requestAnimationFrame(function () {
      scheduled = false;
      grids.forEach(function (grid) {
        resizeAll(grid);
      });
    });
  }

  function init(grid) {
    if (!grid) return;
    if (grid.dataset && grid.dataset.tbMasonryInit) return;
    if (grid.dataset) grid.dataset.tbMasonryInit = "1";

    grids.add(grid);

    // Re-layout as images load.
    var imgs = grid.querySelectorAll("img");
    for (var i = 0; i < imgs.length; i++) {
      var img = imgs[i];
      if (!img.complete) {
        img.addEventListener("load", scheduleRelayout, { passive: true });
      }
    }

    // ResizeObserver gives the most stable result (tile height changes, viewport changes, etc.)
    if ("ResizeObserver" in window) {
      var ro = new ResizeObserver(scheduleRelayout);
      ro.observe(grid);

      var items = grid.querySelectorAll(".tb-masonry__item");
      for (var j = 0; j < items.length; j++) {
        ro.observe(items[j]);
      }
    } else {
      window.addEventListener("resize", scheduleRelayout, { passive: true });
    }

    scheduleRelayout();
  }

  // Public API
  window.TB_Masonry = {
    init: init,
    resizeAll: resizeAll,
  };
})();
