// === Temu 价差筛选插件 v9 ===
// 修复：fixed 面板 + 自动给内容区加 padding，不盖住导航

(function () {
  "use strict";

  var STORAGE_KEY_MIN = "temu_filter_min";
  var STORAGE_KEY_MAX = "temu_filter_max";
  var STORAGE_KEY_STORE = "temu_filter_store";
  var STORAGE_KEY_PAGE_REPLAY = "temu_filter_page_replay";
  var DEFAULT_MIN = 0;
  var DEFAULT_MAX = 100;
  var DEFAULT_STORE = "DXXmall";
  var ROW_SELECTORS = [
    "tr[data-testid=\"beast-core-table-body-tr\"]",
    "tbody tr",
  ];
  var AUTO_SCROLL_DELAY = 325;
  var AUTO_SCROLL_MAX_LOOPS = 260;
  var AUTO_SCROLL_STALE_LIMIT = 8;
  var GLOBAL_SCAN_MAX_PAGES = 200;
  var SKU_REFERENCE_PRICE_MAP = {
    "L042-01": 36,
    "L042-02": 36,
    "L043-01": 20,
    "L043-02": 30,
    "L043-03": 40,
    "L043-04": 10,
    "L043-05": 60,
    "L043-06": 10,
    "L043-07": 20,
    "L043-08": 30,
    "L043-09": 40,
    "L043-10": 60,
    "L043-11": 10,
    "L043-12": 20,
    "L043-13": 30,
    "L043-14": 40,
    "L043-15": 60,
    "L043-16": 10,
    "L043-17": 20,
    "L043-18": 30,
    "L043-19": 40,
    "L043-20": 60,
    "L047-00": 53,
    "L048-00": 40,
    "L051-00": 31,
    "L058-00": 66,
    "L063-00": 110,
    "L063-01": 110,
    "L063-02": 110,
    "L068-00": 110,
    "L068-01": 110,
    "L071-01": 62,
    "L071-02": 62,
    "L072-01": 43,
    "L072-02": 43,
    "L074-00": 52,
    "L075-00": 52,
    "L076-00": 34,
    "L077-00": 40,
    "L078-00": 68,
    "L079-00": 55,
    "L079-01": 55,
    "L081-00": 57,
    "L081-01": 57,
    "L082-00": 57,
    "L082-01": 57,
    "L083-00": 40,
    "L083-01": 40,
    "L084-00": 75,
    "L084-01": 90,
    "L085-00": 60,
    "L086-00": 70,
    "L086-01": 70,
    "L087-00": 52,
    "L087-01": 52,
    "L088-00": 42,
    "L088-01": 42,
    "L089-00": 38,
    "L090-00": 110,
    "L090-01": 110,
    "L091-00": 47,
    "L092-00": 40,
    "L093-00": 53,
    "L094-00": 42,
    "L094-01": 64,
    "L095-00": 68,
    "L095-01": 93,
    "L096-00": 38,
  };

  console.log("[TemuFilter v9] loaded on", location.href);

  // ── 收集元素内所有独立的 % 文本节点 ──────────────
  function collectPercentTexts(el) {
    var results = [];
    if (!el) return results;
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    var node;
    while (node = walker.nextNode()) {
      var text = node.textContent.trim();
      var match = text.match(/^(\d+\.?\d*)%$/);
      if (match) {
        results.push(parseFloat(match[1]));
      }
    }
    return results;
  }

  // ── 解析某一行的价差百分比 ────────────────────────
  function getRowPriceDiffPercent(row) {
    // 方法1：class 匹配
    var container = row.querySelector("[class*=\"use-columns_priceDistance\"]");
    if (container) {
      var valueEl = container.querySelector("[class*=\"use-columns_impPrice\"]");
      if (valueEl) {
        var num = parseFloat(valueEl.textContent.trim());
        if (!isNaN(num) && num >= 0 && num <= 100) {
          console.log("[TemuFilter v9] parse method1:", num + "%");
          return num;
        }
      }
    }

    // 方法2：TreeWalker
    var allPct = collectPercentTexts(row);
    var validPct = allPct.filter(function (p) { return p >= 0 && p <= 100; });
    if (validPct.length > 0) {
      var result = validPct[validPct.length - 1];
      console.log("[TemuFilter v9] parse method2:", validPct, "=>", result + "%");
      return result;
    }

    // 方法3：兜底正则
    var text = row.innerText || row.textContent || "";
    var matches = text.match(/(\d+\.?\d*)%/g);
    if (matches) {
      for (var i = matches.length - 1; i >= 0; i--) {
        var v = parseFloat(matches[i]);
        if (v >= 0 && v <= 100) {
          console.log("[TemuFilter v9] parse method3:", v + "%");
          return v;
        }
      }
    }

    console.log("[TemuFilter v9] parse FAILED");
    return null;
  }

  function getRowPriceDiffPercentsFromElement(el) {
    var values = [];
    function add(value) {
      var num = parseFloat(value);
      if (!isNaN(num) && num >= 0 && num <= 100 && values.indexOf(num) < 0) values.push(num);
    }

    if (!el) return values;
    Array.from(el.querySelectorAll("[class*=\"use-columns_impPrice\"]")).forEach(function (node) {
      add((node.innerText || node.textContent || "").trim());
    });

    collectPercentTexts(el).forEach(add);

    var text = el.innerText || el.textContent || "";
    var matches = text.match(/(\d+\.?\d*)%/g) || [];
    matches.forEach(function (item) { add(item); });

    console.log("[TemuFilter v9] parse declare pct:", values);
    return values;
  }

  function getRowDeclarePriceDiffPercents(row, headerIndexes) {
    headerIndexes = headerIndexes || getHeaderIndexes();
    var declareCell = getCellByIndex(row, headerIndexes.declare);
    return getRowPriceDiffPercentsFromElement(declareCell);
  }

  // ── 获取当前渲染出来的数据行 ──────────────────────
  function getVisibleRows() {
    var rows = [];
    for (var s = 0; s < ROW_SELECTORS.length; s++) {
      var found = document.querySelectorAll(ROW_SELECTORS[s]);
      if (found.length > 0) {
        rows = Array.from(found);
        console.log("[TemuFilter v9] Rows:", ROW_SELECTORS[s], "count=", rows.length);
        break;
      }
    }
    return rows;
  }

  function snapshotRowCells(row) {
    return Array.from(row.querySelectorAll("td")).map(function (cell) {
      return cell.innerText.trim();
    });
  }

  function getRowIdentity(row, pct, index) {
    var text = row.innerText || row.textContent || "";
    var ids = [];
    var patterns = [
      /SPU[:：]\s*([0-9A-Za-z_-]+)/i,
      /货号[:：]\s*([0-9A-Za-z_-]+)/i,
      /SKU[:：]\s*([0-9A-Za-z_-]+)/i,
      /L\d{6,}[-\w]*/i,
    ];
    patterns.forEach(function (pattern) {
      var match = text.match(pattern);
      if (match && match[1]) ids.push(match[1]);
      else if (match && match[0]) ids.push(match[0]);
    });
    if (ids.length > 0) return ids.join("|");
    return "row|" + pct + "|" + text.replace(/\s+/g, " ").slice(0, 500);
  }

  function getDeclareReferenceMatchesFromRow(row, headerIndexes) {
    var declareCell = getCellByIndex(row, headerIndexes.declare);
    var skuCell = getCellByIndex(row, headerIndexes.sku);
    if (!declareCell || !skuCell) return [];
    var skuCodes = extractCargoCodes(skuCell.innerText || skuCell.textContent || "");
    var groups = parseDeclarePriceGroups(declareCell.innerText || declareCell.textContent || "");
    var matches = [];
    for (var i = 0; i < Math.max(skuCodes.length, groups.length); i++) {
      var skuCode = skuCodes[i] || "";
      var floorPrice = getConfiguredComparePrice(skuCode);
      var group = groups.length === 1 ? groups[0] : (groups[i] || groups[groups.length - 1]);
      if (!skuCode || floorPrice === null || !group || group.reference === null || group.reference < floorPrice) continue;
      matches.push({
        declared: group.declared,
        reference: group.reference,
        floorPrice: floorPrice,
        skuCode: skuCode,
        diff: Math.round((group.reference - floorPrice) * 100) / 100,
        text: group.text || "",
      });
    }
    return matches;
  }

  function collectMatchingRowsFromVisible(minPct, maxPct, seen) {
    var rows = getVisibleRows();
    var headerIndexes = getHeaderIndexes();
    var result = [];
    rows.forEach(function (row, index) {
      var priceMatches = getDeclareReferenceMatchesFromRow(row, headerIndexes);
      if (priceMatches.length > 0) {
        var key = getRowIdentity(row, "ref-" + priceMatches.map(function (item) {
          return item.skuCode + ":" + item.reference + ">=" + item.floorPrice;
        }).join("/"), index);
        if (!seen || !seen[key]) {
          if (seen) seen[key] = true;
          result.push({ row: row, pct: null, allPcts: [], priceMatches: priceMatches, key: key, cells: snapshotRowCells(row) });
        }
      }
    });
    return result;
  }

  async function collectMatchingRowsStable(minPct, maxPct, seen, rounds) {
    var result = [];
    rounds = rounds || 3;
    for (var round = 0; round < rounds; round++) {
      var batch = collectMatchingRowsFromVisible(minPct, maxPct, seen);
      if (batch.length > 0) result = result.concat(batch);
      await wait(Math.max(60, Math.floor(AUTO_SCROLL_DELAY / 3)));
    }
    return result;
  }

  async function collectGlobalRecordsStable(seen, minPct, maxPct, rounds) {
    var result = [];
    rounds = rounds || 3;
    for (var round = 0; round < rounds; round++) {
      var batch = collectGlobalScanRecordsFromVisible(seen, minPct, maxPct);
      if (batch.length > 0) result = result.concat(batch);
      await wait(Math.max(60, Math.floor(AUTO_SCROLL_DELAY / 3)));
    }
    return result;
  }

  // ── 获取匹配行 ────────────────────────────────────
  function getMatchingRows(minPct, maxPct) {
    var result = collectMatchingRowsFromVisible(minPct, maxPct);

    console.log("[TemuFilter v9] Reference-price matches:", result.length);
    return result;
  }

  function getHeaderIndexes() {
    var headers = [];
    var ths = document.querySelectorAll("thead th");
    ths.forEach(function (th) {
      headers.push((th.innerText || th.textContent || "").replace(/\s+/g, ""));
    });

    function find(names, fallback) {
      for (var n = 0; n < names.length; n++) {
        for (var i = 0; i < headers.length; i++) {
          if (headers[i].indexOf(names[n]) >= 0) return i;
        }
      }
      return fallback;
    }

    return {
      product: find(["商品信息"], 1),
      skc: find(["SKC属性", "SKC"], 4),
      sku: find(["SKU属性集", "SKU"], 5),
      declare: find(["申报价格"], 6),
    };
  }

  function getCellByIndex(row, index) {
    var cells = row.querySelectorAll("td");
    return cells[index] || null;
  }

  function findProductInfoCell(row, headerIndexes) {
    var candidate = getCellByIndex(row, headerIndexes.product);
    if (candidate && (candidate.querySelector("img") || /SPU[:：]/i.test(candidate.innerText || candidate.textContent || ""))) {
      return candidate;
    }

    var cells = Array.from(row.querySelectorAll("td"));
    for (var i = 0; i < cells.length; i++) {
      var text = cells[i].innerText || cells[i].textContent || "";
      if (cells[i].querySelector("img") && (/SPU[:：]/i.test(text) || /¥\s*\d/.test(text))) {
        return cells[i];
      }
    }
    for (var j = 0; j < cells.length; j++) {
      var fallbackText = cells[j].innerText || cells[j].textContent || "";
      if (/SPU[:：]/i.test(fallbackText) && /¥\s*\d/.test(fallbackText)) {
        return cells[j];
      }
    }
    return candidate;
  }

  function parseMoney(text) {
    if (!text) return null;
    var match = String(text).replace(/,/g, "").match(/¥?\s*(\d+(?:\.\d+)?)/);
    if (!match) return null;
    var value = parseFloat(match[1]);
    return isNaN(value) ? null : value;
  }

  function extractMoneyAfterLabel(text, labels) {
    text = text || "";
    for (var i = 0; i < labels.length; i++) {
      var label = labels[i];
      var idx = text.indexOf(label);
      if (idx >= 0) {
        var part = text.slice(idx + label.length, idx + label.length + 40);
        var value = parseMoney(part);
        if (value !== null) return value;
      }
    }
    return null;
  }

  function extractProductTitle(productCell) {
    if (!productCell) return "";
    var rawText = productCell.innerText || productCell.textContent || "";
    var lines = (productCell.innerText || productCell.textContent || "")
      .split(/\n+/)
      .map(function (line) { return line.trim(); })
      .filter(Boolean);

    function cleanTitle(value) {
      return String(value || "")
        .replace(/\s+/g, " ")
        .replace(/^商品标题[:：]\s*/i, "")
        .replace(/^标题[:：]\s*/i, "")
        .trim();
    }

    function isNoiseLine(line) {
      return /^¥\s*\d/.test(line)
        || /^SPU[:：]/i.test(line)
        || /^SKU[:：]/i.test(line)
        || /^货号[:：]/i.test(line)
        || /^申报价格[:：]/i.test(line)
        || /^参考报价[:：]/i.test(line)
        || /^价差百分比[:：]/i.test(line)
        || /^\d+$/.test(line)
        || /^[\d\s.,%-]+$/.test(line);
    }

    var text = lines.join("\n");
    var directMatch = rawText.match(/¥\s*\d+(?:\.\d+)?\s*([\s\S]*?)(?:SPU[:：]|$)/i);
    if (directMatch && directMatch[1]) {
      var directTitle = directMatch[1]
        .split(/\n+/)
        .map(function (line) { return cleanTitle(line); })
        .filter(function (line) { return line && !isNoiseLine(line); })
        .join("");
      if (directTitle) return directTitle.slice(0, 180);
    }

    var priceMatch = text.match(/¥\s*\d+(?:\.\d+)?/);
    var spuMatch = text.match(/SPU[:：]/i);
    if (priceMatch && spuMatch && spuMatch.index > priceMatch.index) {
      var between = text.slice(priceMatch.index + priceMatch[0].length, spuMatch.index)
        .split(/\n+/)
        .map(function (line) { return cleanTitle(line); })
        .filter(function (line) { return line && !isNoiseLine(line); });
      if (between.length > 0) return between.join("").slice(0, 180);
    }

    var titleParts = [];
    var afterPrice = false;
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (/^¥\s*\d/.test(line)) {
        afterPrice = true;
        line = cleanTitle(line.replace(/^¥\s*\d+(?:\.\d+)?/, ""));
        if (line && !isNoiseLine(line)) titleParts.push(line);
        continue;
      }
      if (/^SPU[:：]/i.test(line)) break;
      if (!afterPrice) continue;
      line = cleanTitle(line);
      if (!line || isNoiseLine(line)) continue;
      titleParts.push(line);
    }
    if (titleParts.length > 0) return titleParts.join("");

    var attrCandidates = Array.from(productCell.querySelectorAll("[title],[alt],a,span,div"))
      .map(function (el) {
        return cleanTitle(el.getAttribute("title") || el.getAttribute("alt") || "");
      })
      .filter(function (value) {
        return value && value.length > 4 && !isNoiseLine(value) && !/^https?:\/\//i.test(value);
      });
    if (attrCandidates.length > 0) {
      attrCandidates.sort(function (a, b) { return b.length - a.length; });
      return attrCandidates[0].slice(0, 180);
    }

    return lines.map(cleanTitle).filter(function (line) {
      return line && !isNoiseLine(line);
    }).join("").slice(0, 180);
  }

  function extractProductImage(productCell) {
    if (!productCell) return "";
    var imgs = Array.from(productCell.querySelectorAll("img"));
    if (imgs.length === 0) return "";
    imgs.sort(function (a, b) {
      var aArea = (a.naturalWidth || a.clientWidth || 0) * (a.naturalHeight || a.clientHeight || 0);
      var bArea = (b.naturalWidth || b.clientWidth || 0) * (b.naturalHeight || b.clientHeight || 0);
      return bArea - aArea;
    });
    for (var i = 0; i < imgs.length; i++) {
      var img = imgs[i];
      var candidates = [
        img.currentSrc,
        img.src,
        img.getAttribute("data-src"),
        img.getAttribute("data-original"),
        img.getAttribute("data-lazy-src"),
      ];
      var srcset = img.getAttribute("srcset") || img.getAttribute("data-srcset") || "";
      if (srcset) candidates.push(srcset.split(",")[0].trim().split(/\s+/)[0]);
      for (var c = 0; c < candidates.length; c++) {
        var url = normalizeImageUrl(candidates[c]);
        if (url) return url;
      }
    }
    return "";
  }

  function extractCargoCodes(text) {
    var result = [];
    text = text || "";
    var re = /货号[:：]\s*(L[0-9A-Za-z]+(?:-[0-9A-Za-z]+)?)/g;
    var match;
    while ((match = re.exec(text)) !== null) {
      result.push(match[1]);
    }
    return result;
  }

  function parseDeclarePriceGroups(text) {
    text = text || "";
    var blocks = text.match(/原申报价[:：]?[\s\S]*?(?=原申报价[:：]?|$)/g) || [text];
    return blocks.map(function (block) {
      var declared = extractMoneyAfterLabel(block, ["卖家当前报价", "申报价格", "原申报价"]);
      var reference = extractMoneyAfterLabel(block, ["参考报价", "参考申报价"]);
      return {
        text: block,
        declared: declared,
        reference: reference,
      };
    });
  }

  function normalizeSkuCode(code) {
    return String(code || "").trim().toUpperCase();
  }

  function getConfiguredComparePrice(skuCode) {
    var base = SKU_REFERENCE_PRICE_MAP[normalizeSkuCode(skuCode)];
    if (typeof base !== "number") return null;
    return base;
  }

  function getGlobalScanRecord(row, headerIndexes, minPct, maxPct) {
    var productCell = findProductInfoCell(row, headerIndexes);
    var skcCell = getCellByIndex(row, headerIndexes.skc);
    var skuCell = getCellByIndex(row, headerIndexes.sku);
    var declareCell = getCellByIndex(row, headerIndexes.declare);
    if (!productCell || !skcCell || !skuCell || !declareCell) return null;

    var skcCodes = extractCargoCodes(skcCell.innerText || skcCell.textContent || "");
    var skcCode = skcCodes[0] || "";
    if (!skcCode) return null;

    var skuCodes = extractCargoCodes(skuCell.innerText || skuCell.textContent || "");
    var priceGroups = parseDeclarePriceGroups(declareCell.innerText || declareCell.textContent || "");
    if (priceGroups.length === 0) return null;

    var qualifiedRecords = [];
    for (var i = 0; i < Math.max(skuCodes.length, priceGroups.length); i++) {
      var skuCode = skuCodes[i] || "";
      var comparePrice = getConfiguredComparePrice(skuCode);
      var group = priceGroups.length === 1 ? priceGroups[0] : (priceGroups[i] || priceGroups[priceGroups.length - 1]);
      if (!skuCode || comparePrice === null || !group || group.reference === null || group.reference < comparePrice) continue;

      var record = {
        title: extractProductTitle(productCell),
        image: extractProductImage(productCell),
        skcCode: skcCode,
        declarePrice: group.declared,
        referencePrice: comparePrice,
        declareReferencePrice: group.reference,
        diffPrice: Math.round((group.reference - comparePrice) * 100) / 100,
        diffDeclareReferencePrice: Math.round((group.reference - comparePrice) * 100) / 100,
        skuCode: skuCode,
        pct: "",
        status: "参考申报价高于最低参考价",
        key: skcCode + "|" + skuCode + "|ref:" + group.reference + "|floor:" + comparePrice,
      };
      qualifiedRecords.push(record);
    }
    return qualifiedRecords.length ? qualifiedRecords : null;
  }

  function collectGlobalScanRecordsFromVisible(seen, minPct, maxPct) {
    var rows = getVisibleRows();
    var headerIndexes = getHeaderIndexes();
    var records = [];
    rows.forEach(function (row) {
      var rowRecords = getGlobalScanRecord(row, headerIndexes, minPct, maxPct);
      if (!rowRecords) return;
      rowRecords.forEach(function (record) {
        if (record && !seen[record.key]) {
          seen[record.key] = true;
          records.push(record);
        }
      });
    });
    return records;
  }

  function getVisibleLowPriceRecords(seen) {
    var rows = getVisibleRows();
    var headerIndexes = getHeaderIndexes();
    var records = [];
    rows.forEach(function (row) {
      var rowRecords = getGlobalScanRecord(row, headerIndexes, 0, 100);
      if (!rowRecords) return;
      rowRecords.forEach(function (record) {
        if (record && (!seen || !seen[record.key])) {
          if (seen) seen[record.key] = true;
          records.push(record);
        }
      });
    });
    return records;
  }

  function isScrollableY(el) {
    if (!el) return false;
    var style = getComputedStyle(el);
    var overflowY = style.overflowY || style.overflow;
    return (overflowY === "auto" || overflowY === "scroll")
      && el.scrollHeight > el.clientHeight + 80;
  }

  // 只滚动包含商品表格数据的容器，避免误滚页面/侧边栏/弹窗滚动条。
  function findDataScrollContainer() {
    var rows = getVisibleRows();
    var anchor = rows[0] || document.querySelector("tbody") || document.querySelector("table");
    var el = anchor;
    while (el && el !== document.body && el !== document.documentElement) {
      if (isScrollableY(el)) {
        console.log("[TemuFilter v9] Found data scroll container:", el.tagName, String(el.className || "").substring(0, 80));
        return el;
      }
      el = el.parentElement;
    }
    console.log("[TemuFilter v9] Use document scrollingElement as data scroll fallback");
    return document.scrollingElement || document.documentElement;
  }

  function wait(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
  }

  function setScrollTop(el, top) {
    if (el === document.body || el === document.documentElement || el === document.scrollingElement) {
      window.scrollTo(0, top);
    } else {
      el.scrollTop = top;
    }
  }

  function getScrollTop(el) {
    if (el === document.body || el === document.documentElement || el === document.scrollingElement) {
      return window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
    }
    return el.scrollTop;
  }

  function getScrollMax(el) {
    if (el === document.body || el === document.documentElement || el === document.scrollingElement) {
      var doc = document.documentElement;
      return Math.max(doc.scrollHeight, document.body.scrollHeight) - window.innerHeight;
    }
    return el.scrollHeight - el.clientHeight;
  }

  function describeScrollElement(el) {
    if (!el) return "null";
    if (el === document.scrollingElement || el === document.documentElement || el === document.body) return "document";
    return el.tagName + "." + String(el.className || "").replace(/\s+/g, ".").slice(0, 90);
  }

  function getPaginationScrollCandidates() {
    var candidates = [];
    function add(el) {
      if (!el || candidates.indexOf(el) >= 0) return;
      if (el === document.body || el === document.documentElement) {
        el = document.scrollingElement || document.documentElement;
      }
      if (candidates.indexOf(el) < 0) candidates.push(el);
    }

    add(document.scrollingElement || document.documentElement);
    var anchor = getVisibleRows()[0] || document.querySelector("tbody") || document.querySelector("table");
    var el = anchor;
    while (el && el !== document.body && el !== document.documentElement) {
      if (isScrollableY(el)) add(el);
      el = el.parentElement;
    }

    Array.from(document.querySelectorAll("div, main, section")).forEach(function (node) {
      if (!isScrollableY(node)) return;
      var rect = node.getBoundingClientRect();
      if (rect.width < 500 || rect.height < 180) return;
      if (node.closest("#temu-filter-panel") || node.closest("#temu-filter-modal")) return;
      add(node);
    });
    return candidates;
  }

  async function autoScrollCollectMatchingRows(minPct, maxPct, onProgress) {
    var container = findDataScrollContainer();
    var originalTop = getScrollTop(container);
    var seen = {};
    var matches = [];
    var lastTop = -1;
    var staleLoops = 0;

    setScrollTop(container, 0);
    await wait(AUTO_SCROLL_DELAY);

    for (var loop = 0; loop < AUTO_SCROLL_MAX_LOOPS; loop++) {
      var batch = await collectMatchingRowsStable(minPct, maxPct, seen, 3);
      if (batch.length > 0) matches = matches.concat(batch);

      var currentTop = getScrollTop(container);
      var maxTop = Math.max(0, getScrollMax(container));
      if (typeof onProgress === "function") {
        onProgress({
          matches: matches.length,
          visible: getVisibleRows().length,
          top: currentTop,
          max: maxTop,
          loop: loop + 1,
        });
      }

      if (maxTop <= 0 || currentTop >= maxTop - 5) {
        await wait(AUTO_SCROLL_DELAY);
        var refreshedMaxTop = Math.max(0, getScrollMax(container));
        if (refreshedMaxTop <= maxTop + 5) break;
        maxTop = refreshedMaxTop;
      }

      var step = Math.max(320, Math.floor((container.clientHeight || window.innerHeight) * 0.9));
      setScrollTop(container, Math.min(maxTop, currentTop + step));
      await wait(AUTO_SCROLL_DELAY);

      var nextTop = getScrollTop(container);
      if (Math.abs(nextTop - lastTop) < 3) staleLoops++;
      else staleLoops = 0;
      lastTop = nextTop;
      if (staleLoops >= AUTO_SCROLL_STALE_LIMIT) break;
    }

    setScrollTop(container, originalTop);
    console.log("[TemuFilter v9] Auto-scroll matches:", matches.length);
    return matches;
  }

  async function autoScrollCollectGlobalRecords(seen, minPct, maxPct, onProgress) {
    var container = findDataScrollContainer();
    var records = [];
    var lastTop = -1;
    var staleLoops = 0;

    setScrollTop(container, 0);
    await wait(AUTO_SCROLL_DELAY);

    for (var loop = 0; loop < AUTO_SCROLL_MAX_LOOPS; loop++) {
      var batch = await collectGlobalRecordsStable(seen, minPct, maxPct, 3);
      if (batch.length > 0) records = records.concat(batch);

      var currentTop = getScrollTop(container);
      var maxTop = Math.max(0, getScrollMax(container));
      if (typeof onProgress === "function") {
        onProgress({
          pageRecords: records.length,
          top: currentTop,
          max: maxTop,
          loop: loop + 1,
        });
      }

      if (maxTop <= 0 || currentTop >= maxTop - 5) {
        await wait(AUTO_SCROLL_DELAY);
        var refreshedMaxTop = Math.max(0, getScrollMax(container));
        if (refreshedMaxTop <= maxTop + 5) break;
        maxTop = refreshedMaxTop;
      }

      var step = Math.max(320, Math.floor((container.clientHeight || window.innerHeight) * 0.9));
      setScrollTop(container, Math.min(maxTop, currentTop + step));
      await wait(AUTO_SCROLL_DELAY);

      var nextTop = getScrollTop(container);
      if (Math.abs(nextTop - lastTop) < 3) staleLoops++;
      else staleLoops = 0;
      lastTop = nextTop;
      if (staleLoops >= AUTO_SCROLL_STALE_LIMIT) break;
    }

    console.log("[TemuFilter v9] Global page records:", records.length);
    return records;
  }

  function isVisibleElement(el) {
    if (!el) return false;
    var rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.top < window.innerHeight;
  }

  function isDisabledElement(el) {
    var cls = String(el.className || "").toLowerCase();
    var parent = el.parentElement;
    var parentCls = parent ? String(parent.className || "").toLowerCase() : "";
    return el.disabled
      || el.getAttribute("aria-disabled") === "true"
      || el.getAttribute("disabled") !== null
      || cls.indexOf("disabled") >= 0
      || (parent && parent.getAttribute("aria-disabled") === "true")
      || (parent && parent.getAttribute("disabled") !== null)
      || parentCls.indexOf("disabled") >= 0;
  }

  function getTableSignature() {
    var rows = getVisibleRows();
    return rows.slice(0, 3).map(function (row) {
      return (row.innerText || row.textContent || "").replace(/\s+/g, " ").slice(0, 160);
    }).join("|");
  }

  function getPaginationNumberButtons() {
    var candidates = Array.from(document.querySelectorAll("button,a,[role=\"button\"],li,div,span"));
    var result = [];
    for (var i = 0; i < candidates.length; i++) {
      var el = candidates[i];
      if (!isVisibleElement(el) || isDisabledElement(el)) continue;
      if (el.closest("#temu-filter-panel") || el.closest("#temu-filter-modal")) continue;
      var rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight * 0.65) continue;
      if (rect.width > 90 || rect.height > 60) continue;
      var text = (el.innerText || el.textContent || "").trim();
      if (!/^\d+$/.test(text)) continue;
      if (/每页|条\/页|page\s*size/i.test((el.parentElement && el.parentElement.innerText) || "")) continue;
      var clickable = el.closest("button,a,[role=\"button\"],li") || el;
      result.push({
        el: clickable,
        number: parseInt(text, 10),
        rect: rect,
      });
    }
    result.sort(function (a, b) {
      if (Math.abs(a.rect.top - b.rect.top) > 4) return a.rect.top - b.rect.top;
      return a.rect.left - b.rect.left;
    });
    return result;
  }

  function isCurrentPageButton(el) {
    if (!el) return false;
    var cls = String(el.className || "").toLowerCase();
    var parent = el.parentElement;
    var parentCls = parent ? String(parent.className || "").toLowerCase() : "";
    return el.getAttribute("aria-current") === "page"
      || el.getAttribute("aria-selected") === "true"
      || cls.indexOf("active") >= 0
      || cls.indexOf("current") >= 0
      || cls.indexOf("selected") >= 0
      || parentCls.indexOf("active") >= 0
      || parentCls.indexOf("current") >= 0
      || parentCls.indexOf("selected") >= 0;
  }

  function getCurrentPageNumber() {
    var buttons = getPaginationNumberButtons();
    for (var i = 0; i < buttons.length; i++) {
      if (isCurrentPageButton(buttons[i].el)) return buttons[i].number;
    }
    return null;
  }

  function findPageButtonByNumber(pageNumber) {
    var buttons = getPaginationNumberButtons();
    for (var i = 0; i < buttons.length; i++) {
      if (buttons[i].number === pageNumber) return buttons[i].el;
    }
    console.warn("[TemuFilter v9] page button not found:", pageNumber, "visible pages=", buttons.map(function (item) { return item.number; }));
    return null;
  }

  function findSingleNextPageButton() {
    var numberButtons = getPaginationNumberButtons();
    if (numberButtons.length === 0) return null;

    var rowTop = numberButtons.reduce(function (sum, item) { return sum + item.rect.top; }, 0) / numberButtons.length;
    var maxNumberRight = numberButtons.reduce(function (max, item) { return Math.max(max, item.rect.right); }, 0);
    var candidates = Array.from(document.querySelectorAll("button,a,[role=\"button\"],li,div,span"));
    var scored = [];
    var used = [];

    candidates.forEach(function (el) {
      if (el.closest("#temu-filter-panel") || el.closest("#temu-filter-modal")) return;
      var clickable = el.closest("button,a,[role=\"button\"],li") || el;
      if (used.indexOf(clickable) >= 0) return;
      used.push(clickable);
      if (!isVisibleElement(clickable) || isDisabledElement(clickable)) return;

      var rect = clickable.getBoundingClientRect();
      if (Math.abs(rect.top - rowTop) > 30) return;
      if (rect.left < maxNumberRight - 4) return;
      if (rect.width > 80 || rect.height > 60) return;

      var text = (el.innerText || el.textContent || "").trim();
      var clickableText = (clickable.innerText || clickable.textContent || "").trim();
      var aria = (clickable.getAttribute("aria-label") || clickable.getAttribute("title") || "").trim();
      var cls = String(clickable.className || "");
      var label = text + " " + aria + " " + cls;
      if (/^\d+$/.test(clickableText) || clickableText === "..." || clickableText === "…") return;
      if (/快进|向后\s*5|jump|fast|ellipsis|更多|more/i.test(label)) return;

      scored.push({
        el: clickable,
        leftDistance: Math.max(0, rect.left - maxNumberRight),
        right: rect.right,
      });
    });
    scored.sort(function (a, b) {
      if (Math.abs(a.leftDistance - b.leftDistance) > 4) return a.leftDistance - b.leftDistance;
      return b.right - a.right;
    });
    return scored.length > 0 ? scored[0].el : null;
  }

  function realClick(el) {
    if (!el) return;
    try { el.scrollIntoView({ block: "center", inline: "center" }); } catch (e) {}
    try { if (typeof el.focus === "function") el.focus(); } catch (e0) {}
    var rect = el.getBoundingClientRect();
    var x = Math.max(0, Math.min(window.innerWidth - 1, rect.left + rect.width / 2));
    var y = Math.max(0, Math.min(window.innerHeight - 1, rect.top + rect.height / 2));
    var target = document.elementFromPoint(x, y) || el;
    try { el.click(); } catch (e1) {}
    ["pointerdown", "mousedown", "pointerup", "mouseup", "click"].forEach(function (type) {
      var eventOptions = {
        bubbles: true,
        cancelable: true,
        view: window,
        clientX: x,
        clientY: y,
        button: 0,
        buttons: type.indexOf("down") >= 0 ? 1 : 0,
      };
      var event;
      if (type.indexOf("pointer") === 0 && typeof PointerEvent === "function") {
        event = new PointerEvent(type, Object.assign({ pointerId: 1, pointerType: "mouse", isPrimary: true }, eventOptions));
      } else {
        event = new MouseEvent(type, eventOptions);
      }
      target.dispatchEvent(event);
    });
    if (target !== el) try { el.click(); } catch (e2) {}
  }

  function clickAtPoint(x, y) {
    var target = document.elementFromPoint(x, y);
    if (!target) return false;
    ["pointerdown", "mousedown", "pointerup", "mouseup", "click"].forEach(function (type) {
      var eventOptions = {
        bubbles: true,
        cancelable: true,
        view: window,
        clientX: x,
        clientY: y,
        button: 0,
        buttons: type.indexOf("down") >= 0 ? 1 : 0,
      };
      var event;
      if (type.indexOf("pointer") === 0 && typeof PointerEvent === "function") {
        event = new PointerEvent(type, Object.assign({ pointerId: 1, pointerType: "mouse", isPrimary: true }, eventOptions));
      } else {
        event = new MouseEvent(type, eventOptions);
      }
      target.dispatchEvent(event);
    });
    return true;
  }

  function cssPathForElement(el) {
    if (!el || !el.tagName) return "";
    var parts = [];
    var node = el;
    while (node && node.nodeType === 1 && node !== document.body && parts.length < 6) {
      var part = node.tagName.toLowerCase();
      if (node.id) {
        part += "#" + node.id.replace(/([^\w-])/g, "\\$1");
        parts.unshift(part);
        break;
      }
      var cls = String(node.className || "").trim().split(/\s+/).filter(Boolean).slice(0, 2);
      if (cls.length) part += "." + cls.map(function (c) { return c.replace(/([^\w-])/g, "\\$1"); }).join(".");
      var parent = node.parentElement;
      if (parent) {
        var siblings = Array.from(parent.children).filter(function (child) { return child.tagName === node.tagName; });
        if (siblings.length > 1) part += ":nth-of-type(" + (siblings.indexOf(node) + 1) + ")";
      }
      parts.unshift(part);
      node = parent;
    }
    return parts.join(" > ");
  }

  function loadPageReplayConfig() {
    try {
      var data = JSON.parse(localStorage.getItem(STORAGE_KEY_PAGE_REPLAY) || "{}");
      return data && typeof data === "object" ? data : {};
    } catch (e) {
      return {};
    }
  }

  function savePageReplayConfig(config) {
    localStorage.setItem(STORAGE_KEY_PAGE_REPLAY, JSON.stringify(config || {}));
  }

  function startRecordNextPageReplay() {
    showToast("请点击一次分页栏的「下一页 >」按钮；我会只记录，不会真的翻页");
    var overlay = document.createElement("div");
    overlay.id = "temu-page-replay-recording";
    Object.assign(overlay.style, {
      position: "fixed",
      left: "0",
      top: "0",
      right: "0",
      bottom: "0",
      zIndex: 2147483646,
      background: "rgba(37,99,235,0.08)",
      cursor: "crosshair",
    });
    var tip = document.createElement("div");
    tip.textContent = "录制翻页按钮：请点击页面右下角「>」；按 ESC 取消";
    Object.assign(tip.style, {
      position: "fixed",
      right: "18px",
      bottom: "70px",
      zIndex: 2147483647,
      background: "#2563eb",
      color: "#fff",
      padding: "10px 14px",
      borderRadius: "8px",
      fontWeight: "700",
      boxShadow: "0 6px 20px rgba(0,0,0,.25)",
    });
    document.body.appendChild(overlay);
    document.body.appendChild(tip);
    function cleanup() {
      document.removeEventListener("click", onClick, true);
      document.removeEventListener("keydown", onKey, true);
      overlay.remove();
      tip.remove();
    }
    function onKey(event) {
      if (event.key === "Escape") {
        cleanup();
        showToast("已取消翻页录制");
      }
    }
    function onClick(event) {
      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();
      var target = document.elementFromPoint(event.clientX, event.clientY);
      var clickable = target && (target.closest("button,a,[role=\"button\"],li") || target);
      var rect = clickable && clickable.getBoundingClientRect ? clickable.getBoundingClientRect() : { left: event.clientX, top: event.clientY, width: 1, height: 1 };
      var pgtNext = target && target.closest("li[class*=\"PGT_next\"], button[class*=\"PGT_next\"], a[class*=\"PGT_next\"]");
      var config = {
        selector: pgtNext ? "li[class*=\"PGT_next\"], button[class*=\"PGT_next\"], a[class*=\"PGT_next\"]" : cssPathForElement(clickable),
        rawSelector: cssPathForElement(clickable),
        text: clickable ? ((clickable.innerText || clickable.textContent || "").trim()) : "",
        xRatio: event.clientX / Math.max(1, window.innerWidth),
        yRatio: event.clientY / Math.max(1, window.innerHeight),
        offsetXRatio: (event.clientX - rect.left) / Math.max(1, rect.width),
        offsetYRatio: (event.clientY - rect.top) / Math.max(1, rect.height),
        savedAt: new Date().toISOString(),
      };
      savePageReplayConfig(config);
      cleanup();
      showToast("已记录翻页按钮。全局翻页筛选会在DOM失败时自动回放。");
    }
    document.addEventListener("click", onClick, true);
    document.addEventListener("keydown", onKey, true);
  }

  function clickRecordedNextPageReplay() {
    var config = loadPageReplayConfig();
    if (!config || (!config.selector && !config.xRatio)) return false;
    var el = null;
    if (config.selector) {
      try { el = document.querySelector(config.selector); } catch (e) { el = null; }
    }
    if (el && isVisibleElement(el) && !isDisabledElement(el)) {
      clickElementCenter(el);
      return true;
    }
    var x = Math.max(0, Math.min(window.innerWidth - 1, Math.round((config.xRatio || 0.96) * window.innerWidth)));
    var y = Math.max(0, Math.min(window.innerHeight - 1, Math.round((config.yRatio || 0.92) * window.innerHeight)));
    console.warn("[TemuFilter v9] use recorded next-page replay:", x, y, config);
    return clickAtPoint(x, y);
  }

  // ── 稳定分页识别：基于「共有XX条 每页100条」分页栏 ─────────────
  function scrollToPageBottomForPagination() {
    var candidates = getPaginationScrollCandidates();
    candidates.forEach(function (el) {
      try {
        setScrollTop(el, Math.max(0, getScrollMax(el)));
        console.log("[TemuFilter v9] scroll pagination candidate bottom:", describeScrollElement(el), getScrollTop(el), "/", getScrollMax(el));
      } catch (e) {}
    });
  }

  function findPaginationContainer() {
    scrollToPageBottomForPagination();
    var pgtContainers = Array.from(document.querySelectorAll("ul[class*=\"PGT_outerWrapper\"], ul[class*=\"TB_pgtOuterWrapper\"]"));
    for (var p = 0; p < pgtContainers.length; p++) {
      var pgt = pgtContainers[p];
      var pgtNext = pgt.querySelector("li[class*=\"PGT_next\"], button[class*=\"PGT_next\"], a[class*=\"PGT_next\"]");
      var pageItems = Array.from(pgt.querySelectorAll("li, a, button")).filter(function (el) {
        return isPurePageNumberText(el.innerText || el.textContent || "");
      });
      if (pgtNext || pageItems.length > 0) {
        try { pgt.scrollIntoView({ block: "center", inline: "nearest" }); } catch (e) {}
        console.log("[TemuFilter v9] PGT pagination container found");
        return pgt;
      }
    }

    var spans = Array.from(document.querySelectorAll("span"));
    for (var i = 0; i < spans.length; i++) {
      var span = spans[i];
      var text = (span.innerText || span.textContent || "").trim();
      if (text.indexOf("共有") < 0) continue;
      var parent = span.parentElement;
      while (parent && parent !== document.body && parent !== document.documentElement) {
        var clickables = Array.from(parent.querySelectorAll("a, button, li"));
        var hasNext = clickables.some(function (el) {
          var text = (el.innerText || el.textContent || "").trim();
          var cls = String(el.className || "");
          return text === ">" || cls.indexOf("PGT_next") >= 0;
        });
        if (hasNext) {
          console.log("[TemuFilter v9] pagination container found:", text);
          return parent;
        }
        parent = parent.parentElement;
      }
    }
    console.warn("[TemuFilter v9] pagination container not found");
    return null;
  }

  function getPaginationLinks(container) {
    return container ? Array.from(container.querySelectorAll("a, button, li")).filter(function (el) {
      return isVisibleElement(el);
    }) : [];
  }

  function isPurePageNumberText(text) {
    return /^\d+$/.test(String(text || "").trim());
  }

  function isActivePageLink(a) {
    if (!a) return false;
    var text = (a.innerText || a.textContent || "").trim();
    if (!isPurePageNumberText(text)) return false;
    var cls = String(a.className || "").toLowerCase();
    var styleText = String(a.getAttribute("style") || "").toLowerCase();
    return cls.indexOf("active") >= 0
      || cls.indexOf("current") >= 0
      || cls.indexOf("selected") >= 0
      || cls.indexOf("pgt_itemactive") >= 0
      || cls.indexOf("pgt_active") >= 0
      || styleText.indexOf("background") >= 0
      || a.getAttribute("aria-current") === "page";
  }

  function getStableCurrentPageNumber(container) {
    var links = getPaginationLinks(container);
    for (var i = 0; i < links.length; i++) {
      if (isActivePageLink(links[i])) {
        return parseInt((links[i].innerText || links[i].textContent || "").trim(), 10);
      }
    }
    return null;
  }

  function getStableTotalPageNumber(container) {
    var maxPage = null;
    getPaginationLinks(container).forEach(function (a) {
      var text = (a.innerText || a.textContent || "").trim();
      if (!isPurePageNumberText(text)) return;
      var num = parseInt(text, 10);
      if (maxPage === null || num > maxPage) maxPage = num;
    });
    return maxPage;
  }

  function getStableNextPageButton(container) {
    if (container) {
      var pgtNext = Array.from(container.querySelectorAll("li[class*=\"PGT_next\"], button[class*=\"PGT_next\"], a[class*=\"PGT_next\"]")).find(function (el) {
        return isVisibleElement(el) && !isDisabledElement(el);
      });
      if (pgtNext) return pgtNext;
    }
    var links = getPaginationLinks(container);
    for (var i = 0; i < links.length; i++) {
      var text = (links[i].innerText || links[i].textContent || "").trim();
      var cls = String(links[i].className || "");
      if ((text === ">" || cls.indexOf("PGT_next") >= 0) && !isDisabledElement(links[i])) return links[i];
    }
    return null;
  }

  function getTableSignatureForWait() {
    return getTableSignature() + "|" + getVisibleRows().length;
  }

  async function waitForProductTableChanged(beforeSignature, beforePage, timeoutMs) {
    var start = Date.now();
    var stableSignature = "";
    var stableCount = 0;
    timeoutMs = timeoutMs || 15000;
    while (Date.now() - start < timeoutMs) {
      await wait(500);
      var container = findPaginationContainer();
      var currentPage = getStableCurrentPageNumber(container);
      var signature = getTableSignatureForWait();
      if ((currentPage && currentPage !== beforePage) || (signature && signature !== beforeSignature)) {
        if (signature === stableSignature) stableCount++;
        else {
          stableSignature = signature;
          stableCount = 1;
        }
        if (stableCount >= 2) {
          console.log("[TemuFilter v9] page loaded:", currentPage, signature.slice(0, 80));
          return true;
        }
      }
    }
    console.warn("[TemuFilter v9] wait page load timeout");
    return false;
  }

  function clickElementCenter(el) {
    if (!el) return false;
    var rect = el.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return false;
    var x = Math.max(0, Math.min(window.innerWidth - 1, rect.left + rect.width / 2));
    var y = Math.max(0, Math.min(window.innerHeight - 1, rect.top + rect.height / 2));
    return clickAtPoint(x, y);
  }

  function clickPaginationRightFallback() {
    var numberButtons = getPaginationNumberButtons();
    if (numberButtons.length === 0) return false;
    var rowTop = numberButtons.reduce(function (sum, item) { return sum + item.rect.top; }, 0) / numberButtons.length;
    var x = window.innerWidth - 28;
    var y = rowTop + 16;
    console.warn("[TemuFilter v9] use coordinate next-page fallback:", x, y);
    return clickAtPoint(x, y);
  }

  async function clickPageNumberAndWait(pageNumber) {
    var btn = findPageButtonByNumber(pageNumber);
    if (!btn) return false;
    if (isCurrentPageButton(btn)) return true;
    var before = getTableSignature();
    clickElementCenter(btn);
    for (var i = 0; i < 30; i++) {
      await wait(500);
      var after = getTableSignature();
      var actual = getCurrentPageNumber();
      if (actual === pageNumber) return true;
      if (after && after !== before) return true;
    }
    return false;
  }

  async function clickSequentialNextPageAndWait(currentPage) {
    var expected = currentPage + 1;
    var btn = findPageButtonByNumber(expected);
    if (!btn) btn = findSingleNextPageButton();

    var before = getTableSignature();
    if (btn) clickElementCenter(btn);
    else if (!clickPaginationRightFallback()) return { moved: false, page: currentPage };
    for (var i = 0; i < 30; i++) {
      await wait(500);
      var after = getTableSignature();
      var actual = getCurrentPageNumber();
      if (actual === expected) return { moved: true, page: expected };
      if (actual !== null && actual !== currentPage && actual !== expected) {
        console.warn("[TemuFilter v9] pagination jumped unexpectedly:", currentPage, "=>", actual, "expected", expected);
        return { moved: false, page: actual, jumped: true };
      }
      if (after && after !== before && actual === null) return { moved: true, page: expected };
    }
    return { moved: false, page: currentPage };
  }

  async function goFirstPageAndWait() {
    var current = getCurrentPageNumber();
    if (current === 1) return 1;
    var moved = await clickPageNumberAndWait(1);
    await wait(AUTO_SCROLL_DELAY);
    return moved ? (getCurrentPageNumber() || 1) : (current || 1);
  }

  async function globalScanAllPages(minPct, maxPct, onProgress) {
    var seen = {};
    var records = [];
    scrollToPageBottomForPagination();
    await wait(800);

    for (var loopPage = 1; loopPage <= GLOBAL_SCAN_MAX_PAGES; loopPage++) {
      var pagination = findPaginationContainer();
      var currentPage = getStableCurrentPageNumber(pagination);
      var totalPage = getStableTotalPageNumber(pagination);
      var nextButton = getStableNextPageButton(pagination);
      if (!currentPage) currentPage = getCurrentPageNumber() || loopPage;

      console.log("[TemuFilter v9] global page loop:", currentPage, "/", totalPage || "?");
      var pageRecords = await autoScrollCollectGlobalRecords(seen, minPct, maxPct, function (progress) {
        if (typeof onProgress === "function") {
          onProgress({
            page: currentPage,
            totalPage: totalPage,
            total: records.length + progress.pageRecords,
            top: progress.top,
            max: progress.max,
          });
        }
      });
      records = records.concat(pageRecords);

      if (typeof onProgress === "function") {
        onProgress({ page: currentPage, totalPage: totalPage, total: records.length, turning: true });
      }

      pagination = findPaginationContainer();
      currentPage = getStableCurrentPageNumber(pagination) || currentPage;
      totalPage = getStableTotalPageNumber(pagination) || totalPage;
      nextButton = getStableNextPageButton(pagination);
      var hasReplayNext = !!(loadPageReplayConfig().selector || loadPageReplayConfig().xRatio);
      if ((totalPage && currentPage >= totalPage) || (!nextButton && !hasReplayNext)) {
        console.log("[TemuFilter v9] global scan finished at page:", currentPage, "total:", totalPage, "records:", records.length);
        break;
      }

      var beforeSignature = getTableSignatureForWait();
      console.log("[TemuFilter v9] click next page:", currentPage, "=>", currentPage + 1);
      if (nextButton) realClick(nextButton);
      else if (!clickRecordedNextPageReplay()) {
        console.warn("[TemuFilter v9] no next button and no recorded replay");
        break;
      }
      var moved = await waitForProductTableChanged(beforeSignature, currentPage, 18000);
      if (!moved && nextButton) {
        console.warn("[TemuFilter v9] DOM next click did not move, retry recorded/fallback click");
        if (!clickRecordedNextPageReplay()) clickPaginationRightFallback();
        moved = await waitForProductTableChanged(beforeSignature, currentPage, 12000);
      }
      if (!moved) {
        console.warn("[TemuFilter v9] stop global scan because next page did not load");
        break;
      }
    }
    console.log("[TemuFilter v9] global scan complete, records:", records.length);
    return records;
  }

  function downloadGlobalScanExcel(records) {
    var rowsHTML = records.map(function (record) {
      var imageHTML = record.image
        ? "<img src=\"" + escapeHTML(record.image) + "\" width=\"90\" height=\"90\" style=\"object-fit:contain;\"/>"
        : "";
      return "<tr>" +
        "<td>" + escapeHTML(record.title) + "</td>" +
        "<td>" + imageHTML + "</td>" +
        "<td>" + escapeHTML(record.skcCode) + "</td>" +
        "<td>" + escapeHTML(record.skuCode) + "</td>" +
        "<td>" + escapeHTML(String(record.declarePrice)) + "</td>" +
        "<td>" + escapeHTML(record.declareReferencePrice === null || record.declareReferencePrice === undefined ? "" : String(record.declareReferencePrice)) + "</td>" +
        "<td>" + escapeHTML(record.diffDeclareReferencePrice === null || record.diffDeclareReferencePrice === undefined ? "" : String(record.diffDeclareReferencePrice)) + "</td>" +
        "<td>" + escapeHTML(record.referencePrice === null || record.referencePrice === undefined ? "" : String(record.referencePrice)) + "</td>" +
        "<td>" + escapeHTML(record.diffPrice === null || record.diffPrice === undefined ? "" : String(record.diffPrice)) + "</td>" +
        "<td>" + escapeHTML(record.status || "") + "</td>" +
      "</tr>";
    }).join("");
    var html =
      "<html><head><meta charset=\"UTF-8\"></head><body>" +
      "<table border=\"1\">" +
      "<thead><tr>" +
      "<th>商品信息标题</th><th>首图</th><th>SKC货号</th><th>SKU货号</th><th>申报价</th><th>参考申报价</th><th>高出最低参考价</th><th>最低参考价</th><th>高出最低参考价</th><th>结果</th>" +
      "</tr></thead><tbody>" + rowsHTML + "</tbody></table>" +
      "</body></html>";
    var blob = new Blob(["\ufeff" + html], { type: "application/vnd.ms-excel;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    var ts = new Date().toISOString().replace(/[:T]/g, "-").slice(0, 19);
    a.href = url;
    a.download = "temu-全局扫描-" + ts + ".xls";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  function showImageZoom(url) {
    if (!url) return;
    var old = document.getElementById("temu-image-zoom-modal");
    if (old) old.remove();
    var modal = document.createElement("div");
    modal.id = "temu-image-zoom-modal";
    Object.assign(modal.style, {
      position: "fixed", top: "0", left: "0", width: "100vw", height: "100vh",
      background: "rgba(0,0,0,0.72)", zIndex: 2147483647,
      display: "flex", alignItems: "center", justifyContent: "center", padding: "30px",
    });
    modal.innerHTML =
      "<div style=\"position:relative;max-width:92vw;max-height:92vh;\">" +
        "<img src=\"" + escapeHTML(url) + "\" style=\"max-width:92vw;max-height:88vh;object-fit:contain;background:#fff;border-radius:10px;\"/>" +
        "<button style=\"position:absolute;top:-18px;right:-18px;width:36px;height:36px;border-radius:50%;border:none;background:#fff;color:#111;font-size:20px;cursor:pointer;\">×</button>" +
      "</div>";
    modal.addEventListener("click", function (e) {
      if (e.target === modal || e.target.tagName === "BUTTON") modal.remove();
    });
    document.body.appendChild(modal);
  }

  function showPriceResults(records) {
    var old = document.getElementById("temu-filter-modal");
    if (old) old.remove();

    var modal = document.createElement("div");
    modal.id = "temu-filter-modal";
    Object.assign(modal.style, {
      position: "fixed", top: "0", left: "0", width: "100vw", height: "100vh",
      background: "rgba(0,0,0,0.45)", zIndex: 2147483647,
      display: "flex", alignItems: "center", justifyContent: "center",
    });

    var tableHTML = "<table style=\"width:100%;border-collapse:collapse;font-size:13px;\"><thead><tr style=\"background:#e6fffb;\">" +
      "<th style=\"padding:8px 12px;border:1px solid #87e8de;text-align:left;\">标题</th>" +
      "<th style=\"padding:8px 12px;border:1px solid #87e8de;text-align:left;\">首图</th>" +
      "<th style=\"padding:8px 12px;border:1px solid #87e8de;text-align:left;\">SKC货号</th>" +
      "<th style=\"padding:8px 12px;border:1px solid #87e8de;text-align:left;\">SKU货号</th>" +
      "<th style=\"padding:8px 12px;border:1px solid #87e8de;text-align:left;\">申报价</th>" +
      "<th style=\"padding:8px 12px;border:1px solid #87e8de;text-align:left;\">最低价</th>" +
      "<th style=\"padding:8px 12px;border:1px solid #87e8de;text-align:left;\">高出</th>" +
      "<th style=\"padding:8px 12px;border:1px solid #87e8de;text-align:left;\">结果</th>" +
      "</tr></thead><tbody>";
    records.forEach(function (record, index) {
      var img = record.image
        ? "<img class=\"temu-price-result-img\" data-url=\"" + escapeHTML(record.image) + "\" src=\"" + escapeHTML(record.image) + "\" style=\"width:92px;height:92px;object-fit:contain;border:1px solid #ddd;border-radius:6px;cursor:zoom-in;background:#fff;\"/>"
        : "";
      tableHTML += "<tr>" +
        "<td style=\"padding:8px 12px;border:1px solid #eee;max-width:360px;\">" + escapeHTML(record.title || "") + "</td>" +
        "<td style=\"padding:8px 12px;border:1px solid #eee;text-align:center;\">" + img + "</td>" +
        "<td style=\"padding:8px 12px;border:1px solid #eee;\">" + escapeHTML(record.skcCode || "") + "</td>" +
        "<td style=\"padding:8px 12px;border:1px solid #eee;\">" + escapeHTML(record.skuCode || "") + "</td>" +
        "<td style=\"padding:8px 12px;border:1px solid #eee;\">¥" + escapeHTML(String(record.declarePrice)) + "</td>" +
        "<td style=\"padding:8px 12px;border:1px solid #eee;\">¥" + escapeHTML(String(record.referencePrice)) + "</td>" +
        "<td style=\"padding:8px 12px;border:1px solid #eee;color:#cf1322;font-weight:700;\">¥" + escapeHTML(String(record.diffPrice)) + "</td>" +
        "<td style=\"padding:8px 12px;border:1px solid #eee;\">" + escapeHTML(record.status || "") + "</td>" +
      "</tr>";
    });
    tableHTML += "</tbody></table>";

    modal.innerHTML =
      "<div style=\"background:#fff;border-radius:12px;width:92vw;max-width:1280px;max-height:88vh;display:flex;flex-direction:column;box-shadow:0 8px 40px rgba(0,0,0,0.25);overflow:hidden;\">" +
        "<div style=\"display:flex;align-items:center;justify-content:space-between;padding:16px 24px;background:linear-gradient(135deg,#13a8a8,#08979c);color:#fff;\">" +
          "<div style=\"font-size:16px;font-weight:700;\">高于最低价结果（共 " + records.length + " 条）</div>" +
          "<button id=\"temu-modal-close\" style=\"background:rgba(255,255,255,0.2);border:1px solid rgba(255,255,255,0.4);color:#fff;font-size:18px;cursor:pointer;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;\">X</button>" +
        "</div>" +
        "<div style=\"flex:1;overflow:auto;padding:16px 24px;\">" +
          (records.length === 0
            ? "<div style=\"text-align:center;padding:60px 0;color:#999;font-size:15px;\">暂无高于最低价的产品</div>"
            : tableHTML) +
        "</div>" +
        "<div style=\"padding:12px 24px;border-top:1px solid #f0f0f0;text-align:right;\">" +
          "<button id=\"temu-price-export\" style=\"padding:6px 18px;background:#13a8a8;color:#fff;border:none;border-radius:6px;font-size:14px;cursor:pointer;margin-right:8px;\">导出 Excel</button>" +
          "<button id=\"temu-modal-close2\" style=\"padding:6px 24px;background:#722ed1;color:#fff;border:none;border-radius:6px;font-size:14px;cursor:pointer;\">关闭</button>" +
        "</div>" +
      "</div>";

    document.body.appendChild(modal);
    modal.addEventListener("click", function (e) { if (e.target === modal) modal.remove(); });
    document.getElementById("temu-modal-close").addEventListener("click", function () { modal.remove(); });
    document.getElementById("temu-modal-close2").addEventListener("click", function () { modal.remove(); });
    document.getElementById("temu-price-export").addEventListener("click", function () { downloadGlobalScanExcel(records); });
    Array.from(modal.querySelectorAll(".temu-price-result-img")).forEach(function (img) {
      img.addEventListener("click", function () { showImageZoom(img.getAttribute("data-url")); });
    });
  }

  // ── HTML 转义 ─────────────────────────────────────
  function escapeHTML(str) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // ── Temu 商品详情页轮播图采集 ─────────────────────
  function normalizeImageUrl(raw) {
    if (!raw) return "";
    var url = String(raw).trim();
    if (!url || url.indexOf("data:") === 0 || url.indexOf("blob:") === 0) return "";
    url = url.replace(/&amp;/g, "&");
    if (url.indexOf("//") === 0) url = location.protocol + url;
    try {
      url = new URL(url, location.href).href;
    } catch (e) {
      return "";
    }
    return url;
  }

  function stripImageSizing(url) {
    try {
      var u = new URL(url);
      [
        "imageView2", "imageMogr2", "x-oss-process", "width", "height",
        "w", "h", "format", "quality", "thumbnail", "resize"
      ].forEach(function (key) { u.searchParams.delete(key); });
      return u.href;
    } catch (e) {
      return url;
    }
  }

  function downloadUrlForProductImage(url) {
    try {
      var u = new URL(url);
      if (/img\.kwcdn\.com$/i.test(u.hostname) && /\/product\/(open|fancy)\//i.test(u.pathname)) {
        u.search = "";
        return u.href;
      }
    } catch (e) {}
    return url;
  }

  function canonicalProductImageUrl(url) {
    return downloadUrlForProductImage(url);
  }

  function isLikelyProductImageUrl(url) {
    if (!url) return false;
    var lower = url.toLowerCase();
    if (!/\.(jpg|jpeg|png|webp|avif)(\?|$)/.test(lower)) return false;
    if (/avatar|logo|icon|sprite|badge|flag|payment|favicon|review|comment|rating|star|openemail|upload_commimg|upload_aimg\/openi|\/promotion\//.test(lower)) return false;
    if (!/kwcdn|temu|pddpic|img|image|goods|product|mall/.test(lower)) return false;
    return /img\.kwcdn\.com\/product\/(open|fancy)\/[^?#]+\.(jpg|jpeg|png|webp|avif)/.test(lower);
  }

  function addCandidate(map, rawUrl, source, indexHint, score) {
    var url = normalizeImageUrl(rawUrl);
    if (!isLikelyProductImageUrl(url)) return;
    url = canonicalProductImageUrl(url);
    var key = url.split("#")[0];
    if (!map[key]) {
      map[key] = {
        url: url,
        rawUrl: url,
        source: source || "",
        indexHint: indexHint || 0,
        score: score || 0,
      };
    }
  }

  function collectSrcsetUrls(srcset) {
    if (!srcset) return [];
    return String(srcset).split(",").map(function (part) {
      return part.trim().split(/\s+/)[0];
    }).filter(Boolean);
  }

  function collectKwcdnUrlsFromText(text) {
    var urls = [];
    if (!text) return urls;
    var re = /https?:\\?\/\\?\/img\.kwcdn\.com\/product\/(?:open|fancy)\/[^"'\\\s<>]+?\.(?:jpg|jpeg|png|webp|avif)(?:\?[^"'\\\s<>]*)?/gi;
    var match;
    while ((match = re.exec(text)) !== null) {
      urls.push(match[0].replace(/\\\//g, "/").replace(/\\u002F/g, "/"));
    }
    return urls;
  }

  function getElementScore(el) {
    var score = 0;
    var rect = el.getBoundingClientRect ? el.getBoundingClientRect() : { width: 0, height: 0, top: 9999, left: 9999 };
    var text = "";
    var p = el;
    for (var i = 0; i < 4 && p; i++, p = p.parentElement) {
      text += " " + (p.className || "") + " " + (p.id || "") + " " + Array.from(p.attributes || []).map(function (a) {
        return a.name + "=" + a.value;
      }).join(" ");
    }
    text = String(text).toLowerCase();
    if (/carousel|swiper|slider|gallery|thumb|main|goods|product|sku|image|img|picture|preview/.test(text)) score += 30;
    if (rect.width >= 240 && rect.height >= 240) score += 40;
    if (rect.width >= 80 && rect.height >= 80) score += 15;
    if (rect.top >= -100 && rect.top <= window.innerHeight + 600) score += 10;
    if (rect.left <= window.innerWidth * 0.75) score += 5;
    return score;
  }

  function collectCarouselImages() {
    var candidates = {};

    // 1) Temu PDP carousel images are often present in script/serialized state as full kwcdn product URLs.
    collectKwcdnUrlsFromText(document.documentElement.innerHTML).forEach(function (url, index) {
      addCandidate(candidates, url, "html:kwcdn", index, 80);
    });

    // 2) Prefer visible carousel/thumb containers near the product hero area.
    var carouselRoots = Array.from(document.querySelectorAll(
      "[role='button'], [class*='carousel'], [class*='swiper'], [class*='thumb'], [class*='gallery'], [class*='goods'], [class*='product']"
    )).filter(function (el) {
      var rect = el.getBoundingClientRect();
      return rect.width >= 40 && rect.height >= 40 && rect.top > -200 && rect.top < window.innerHeight + 800;
    });
    var scopedNodes = [];
    carouselRoots.forEach(function (root) {
      scopedNodes = scopedNodes.concat(Array.from(root.querySelectorAll("img, source")));
    });

    var imgNodes = scopedNodes.concat(Array.from(document.querySelectorAll("img, source")));
    imgNodes.forEach(function (el, index) {
      var score = getElementScore(el);
      [
        "src", "currentSrc", "data-src", "data-lazy-src", "data-original",
        "data-image", "data-url", "data-thumb", "data-large", "data-main"
      ].forEach(function (attr) {
        var value = attr === "currentSrc" ? el.currentSrc : el.getAttribute(attr);
        if (value && score >= 20) addCandidate(candidates, value, "img:" + attr, index, score);
      });
      collectSrcsetUrls(el.getAttribute("srcset") || el.getAttribute("data-srcset")).forEach(function (url) {
        if (score >= 20) addCandidate(candidates, url, "srcset", index, score);
      });
    });

    Array.from(document.querySelectorAll("[style*='background']")).forEach(function (el, index) {
      var score = getElementScore(el);
      if (score < 20) return;
      var bg = getComputedStyle(el).backgroundImage || "";
      var matches = bg.match(/url\((['"]?)(.*?)\1\)/g) || [];
      matches.forEach(function (m) {
        var url = m.replace(/^url\((['"]?)/, "").replace(/(['"]?)\)$/, "");
        addCandidate(candidates, url, "background", 10000 + index, score);
      });
    });

    Array.from(document.querySelectorAll("a[href]")).forEach(function (el, index) {
      var score = getElementScore(el);
      if (score >= 20) addCandidate(candidates, el.getAttribute("href"), "link", 20000 + index, score);
    });

    var items = Object.keys(candidates).map(function (key) { return candidates[key]; });
    items = items.filter(function (item) {
      return /img\.kwcdn\.com\/product\/(open|fancy)\//i.test(item.url) || /\/product\/.*goods/i.test(item.url);
    });
    items.sort(function (a, b) {
      var productA = /\/product\/open\//i.test(a.url) ? 0 : (/\/product\/fancy\//i.test(a.url) ? 1 : 2);
      var productB = /\/product\/open\//i.test(b.url) ? 0 : (/\/product\/fancy\//i.test(b.url) ? 1 : 2);
      if (productA !== productB) return productA - productB;
      return a.indexHint - b.indexHint;
    });

    // Temu 商品页常把推荐、评价图也放在页面里。轮播图通常出现在前部，先保守取前 20 张。
    return items.slice(0, 16);
  }

  function getProductIdFromPage() {
    var text = location.href;
    var match = text.match(/(?:goods_id|product_id|item_id|_oak_pid_)=([^&]+)/i)
      || text.match(/\/([A-Za-z0-9_-]{8,})(?:\.html)?(?:[?#]|$)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function getProductTitleFromPage() {
    var h1 = document.querySelector("h1");
    if (h1 && h1.innerText.trim()) return h1.innerText.trim();
    var title = document.title || "";
    return title.replace(/\s*-\s*Temu.*$/i, "").trim();
  }

  function toCarouselCsv(items) {
    var productId = getProductIdFromPage();
    var title = getProductTitleFromPage();
    var rows = [["index", "product_id", "title", "image_url", "source"]];
    items.forEach(function (item, index) {
      rows.push([index + 1, productId, title, item.url, item.source]);
    });
    return rows.map(function (row) {
      return row.map(function (cell) {
        return "\"" + String(cell || "").replace(/"/g, "\"\"") + "\"";
      }).join(",");
    }).join("\n");
  }

  function downloadText(filename, text, type) {
    var blob = new Blob(["\ufeff" + text], { type: type || "text/plain;charset=utf-8" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () {
      URL.revokeObjectURL(a.href);
      a.remove();
    }, 500);
  }

  function filenameFromImageUrl(url, index) {
    var ext = "jpg";
    try {
      var path = new URL(url).pathname;
      var match = path.match(/\.([a-zA-Z0-9]{3,5})(?:$|\?)/);
      if (match) ext = match[1].toLowerCase().replace("jpeg", "jpg");
      if (!/^(jpg|png|webp)$/.test(ext)) ext = "jpg";
    } catch (e) {}
    return String(index + 1).padStart(2, "0") + "." + ext;
  }

  function extensionFromBlob(blob, fallbackName) {
    var type = (blob && blob.type || "").toLowerCase();
    if (type.indexOf("jpeg") >= 0 || type.indexOf("jpg") >= 0) return "jpg";
    if (type.indexOf("png") >= 0) return "png";
    if (type.indexOf("webp") >= 0) return "webp";
    if (type.indexOf("avif") >= 0) return "avif";
    if (type.indexOf("gif") >= 0) return "gif";
    var match = String(fallbackName || "").match(/\.([a-zA-Z0-9]{3,5})$/);
    return match ? match[1].toLowerCase().replace("jpeg", "jpg") : "jpg";
  }

  async function getAvailableFileHandle(dirHandle, filename) {
    var dot = filename.lastIndexOf(".");
    var base = dot >= 0 ? filename.slice(0, dot) : filename;
    var ext = dot >= 0 ? filename.slice(dot) : "";
    var candidate = filename;
    var suffix = 2;
    while (true) {
      try {
        await dirHandle.getFileHandle(candidate, { create: false });
        candidate = base + "_" + suffix + ext;
        suffix++;
      } catch (err) {
        return {
          filename: candidate,
          handle: await dirHandle.getFileHandle(candidate, { create: true }),
        };
      }
    }
  }

  function selectedCarouselItems(items) {
    var selected = [];
    items.forEach(function (item, index) {
      var checkbox = document.querySelector(".temu-carousel-select[data-index='" + index + "']");
      if (!checkbox || checkbox.checked) selected.push(item);
    });
    return selected;
  }

  async function saveCarouselImagesToFolder(items) {
    items = selectedCarouselItems(items);
    if (!items.length) {
      showToast("没有勾选需要保存的轮播图");
      return;
    }
    if (!window.showDirectoryPicker) {
      showToast("当前浏览器不支持选择文件夹，请用 Chrome/Edge 新版本");
      return;
    }

    var dirHandle = await window.showDirectoryPicker({ mode: "readwrite" });
    var saved = 0;
    var failed = [];

    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      var filename = filenameFromImageUrl(item.url, i);
      try {
        var downloadUrl = downloadUrlForProductImage(item.url);
        console.log("[TemuFilter v9] saving image", i + 1, downloadUrl, "from", item.url);
        var resp = await fetch(downloadUrl, {
          credentials: "omit",
          cache: "reload",
          referrer: location.href,
          referrerPolicy: "strict-origin-when-cross-origin",
        });
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        var blob = await resp.blob();
        console.log("[TemuFilter v9] image response", i + 1, {
          status: resp.status,
          type: blob.type,
          size: blob.size,
          url: downloadUrl,
        });
        if (!blob.type || blob.type.indexOf("image/") !== 0) {
          throw new Error("not image: " + (blob.type || "unknown"));
        }
        if (!blob || !blob.size) throw new Error("empty image");
        if (blob.size < 10000) throw new Error("too small: " + blob.size + " bytes");
        var ext = extensionFromBlob(blob, filename);
        if (/\.jpe?g$/i.test(new URL(downloadUrl).pathname)) ext = "jpg";
        filename = filename.replace(/\.[a-zA-Z0-9]{3,5}$/, "." + ext);
        var available = await getAvailableFileHandle(dirHandle, filename);
        filename = available.filename;
        var fileHandle = available.handle;
        var writable = await fileHandle.createWritable();
        await writable.write(blob);
        await writable.close();
        saved++;
      } catch (err) {
        failed.push("#" + (i + 1) + " " + err.message);
      }
    }

    showToast("已保存 " + saved + "/" + items.length + " 张" + (failed.length ? "，失败 " + failed.length + " 张" : ""));
    if (failed.length) {
      console.warn("[TemuFilter v9] carousel save failed:", failed);
    }
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
    return Promise.resolve();
  }

  function extractTitleFingerprint(title) {
    var text = String(title || "").replace(/\s+/g, " ").trim();
    var match = text.match(/(?:^|[\s，,、。])([A-Z0-9]{3})$/i);
    if (!match) match = text.match(/([A-Z0-9]{3})$/i);
    if (match && /[A-Z]/i.test(match[1]) && /\d/.test(match[1])) return match[1].toUpperCase();
    var noise = { CSS: true, WEB: true, BOX: true, SKU: true, SPU: true, RMB: true, CNY: true };
    var candidates = [];
    var re = /(?:^|[^A-Z0-9])([A-Z0-9]{3})(?=$|[^A-Z0-9])/ig;
    var item;
    while ((item = re.exec(text)) !== null) {
      var code = item[1].toUpperCase();
      if (noise[code] || !/[A-Z]/.test(code) || !/\d/.test(code)) continue;
      candidates.push(code);
    }
    return candidates.length ? candidates[candidates.length - 1] : "";
  }

  function recordsToTsv(rows) {
    if (!Array.isArray(rows)) return "";
    return rows.map(function (row) {
      if (Array.isArray(row)) return row.join("\t");
      if (row && typeof row === "object") {
        if (Array.isArray(row.values)) return row.values.join("\t");
        if (typeof row.tsv === "string") return row.tsv;
        return Object.keys(row).map(function (key) { return row[key]; }).join("\t");
      }
      return String(row || "");
    }).join("\n");
  }

  function getCurrentStoreName() {
    var input = document.getElementById("temu-filter-store");
    var value = input ? input.value : localStorage.getItem(STORAGE_KEY_STORE);
    value = String(value || DEFAULT_STORE).trim() || DEFAULT_STORE;
    localStorage.setItem(STORAGE_KEY_STORE, value);
    return value;
  }

  async function fetchFingerprintRowsData(fingerprint) {
    var fp = encodeURIComponent(fingerprint);
    var store = encodeURIComponent(getCurrentStoreName());
    var urls = [
      "http://127.0.0.1:8765/api/d-groups?d=" + fp + "&store=" + store,
      "http://127.0.0.1:8765/api/fingerprint-copy?fingerprint=" + fp,
      "http://127.0.0.1:8765/api/copy-rows-by-fingerprint?fingerprint=" + fp,
      "http://127.0.0.1:8765/api/search-rows?fingerprint=" + fp,
      "http://127.0.0.1:8765/api/search?fingerprint=" + fp,
    ];
    for (var i = 0; i < urls.length; i++) {
      try {
        var res = await fetch(urls[i], { method: "GET", cache: "no-store" });
        if (!res.ok) continue;
        var contentType = res.headers.get("content-type") || "";
        if (contentType.indexOf("application/json") >= 0) {
          var data = await res.json();
          if (Array.isArray(data.items) && data.items.length && data.items[0].tsv) {
            return { text: data.items[0].tsv, item: data.items[0], source: "d-groups" };
          }
          var text = data.clipboardText || data.tsv || data.text || recordsToTsv(data.rows || data.records || data.data);
          if (text && String(text).trim()) return { text: String(text), item: data, source: "generic-json" };
        } else {
          var raw = await res.text();
          if (raw && raw.trim()) return { text: raw, item: null, source: "text" };
        }
      } catch (err) {
        // D 值查询后台没开或接口名不一致时，继续尝试下一个地址。
      }
    }
    return null;
  }

  async function recordCopiedEvent(record, matchedItem) {
    var payload = {
      store: getCurrentStoreName(),
      D: matchedItem && matchedItem.D ? matchedItem.D : "",
      fingerprint: record && record.fingerprint ? record.fingerprint : "",
      title: record && record.title ? record.title : (matchedItem && matchedItem.title ? matchedItem.title : ""),
      source_file: matchedItem && matchedItem.file ? matchedItem.file : "",
      source_sheet: matchedItem && matchedItem.sheet ? matchedItem.sheet : "",
      row_count: matchedItem && matchedItem.row_count ? matchedItem.row_count : 0,
      declare_price: record && record.priceMatches && record.priceMatches[0] ? record.priceMatches[0].declared : null,
      declare_reference_price: record && record.priceMatches && record.priceMatches[0] ? record.priceMatches[0].reference : null,
    };
    try {
      await fetch("http://127.0.0.1:8765/api/price-copy-event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch (err) {
      console.warn("[TemuFilter v9] record copy event failed:", err);
    }
  }

  async function getCopiedStatus(record) {
    if (!record || !record.lookupKey) return null;
    try {
      var url = "http://127.0.0.1:8765/api/price-copy-status?store=" +
        encodeURIComponent(getCurrentStoreName()) +
        (record.fingerprint
          ? "&fingerprint=" + encodeURIComponent(record.fingerprint)
          : "&d=" + encodeURIComponent(record.lookupKey));
      var res = await fetch(url, { method: "GET", cache: "no-store" });
      if (!res.ok) return null;
      return await res.json();
    } catch (err) {
      return null;
    }
  }

  async function copyFingerprintRows(record) {
    var lookupKey = record && record.lookupKey ? record.lookupKey : "";
    if (!lookupKey) {
      showToast("没有识别到标题指纹或D值，无法定位表格行");
      return;
    }
    var rowsData = await fetchFingerprintRowsData(lookupKey);
    if (rowsData && rowsData.text) {
      await copyText(rowsData.text);
      await recordCopiedEvent(record, rowsData.item);
      showToast("已复制并记录：" + getCurrentStoreName() + " / " + lookupKey + (rowsData.item && rowsData.item.D ? " / " + rowsData.item.D : ""));
      return;
    }
    await copyText(lookupKey);
    showToast("8765 后台未返回行，已先复制查行键：" + lookupKey);
  }

  async function openDSearchBackend() {
    try {
      var res = await fetch("http://127.0.0.1:8765/api/ping", { method: "GET", cache: "no-store" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      window.open("http://127.0.0.1:8765/", "_blank", "noopener,noreferrer");
      showToast("D 查询后台已打开");
    } catch (err) {
      showToast("D 查询后台未启动；请运行桌面“启动Temu后台.bat”，或等开机自启");
    }
  }

  function showCarouselResults() {
    var old = document.getElementById("temu-carousel-modal");
    if (old) old.remove();

    var items = collectCarouselImages();
    var csv = toCarouselCsv(items);
    var productId = getProductIdFromPage();
    var title = getProductTitleFromPage();

    var cards = items.map(function (item, index) {
      return "<div class=\"temu-carousel-card\" data-index=\"" + index + "\" style=\"border:1px solid #eee;border-radius:8px;overflow:hidden;background:#fff;cursor:pointer;transition:all .15s;\">" +
        "<div style=\"display:flex;align-items:center;gap:6px;padding:7px 8px;border-bottom:1px solid #eee;font-size:12px;color:#333;\">" +
          "<input class=\"temu-carousel-select\" data-index=\"" + index + "\" type=\"checkbox\" style=\"pointer-events:none;\" />" +
          "<span style=\"font-weight:700;color:#1677ff;\">点击选择 #" + (index + 1) + "</span>" +
        "</div>" +
        "<div style=\"height:150px;background:#fafafa;display:flex;align-items:center;justify-content:center;\">" +
          "<img src=\"" + escapeHTML(item.url) + "\" style=\"max-width:100%;max-height:150px;object-fit:contain;\" />" +
        "</div>" +
        "<div style=\"padding:8px;font-size:12px;line-height:1.4;\">" +
          "<div style=\"font-weight:700;color:#531dab;margin-bottom:4px;\">#" + (index + 1) + " " + escapeHTML(item.source) + "</div>" +
          "<textarea readonly style=\"width:100%;height:56px;border:1px solid #eee;border-radius:6px;font-size:11px;resize:none;box-sizing:border-box;\">" + escapeHTML(item.url) + "</textarea>" +
        "</div>" +
      "</div>";
    }).join("");

    var modal = document.createElement("div");
    modal.id = "temu-carousel-modal";
    Object.assign(modal.style, {
      position: "fixed", inset: "0", background: "rgba(0,0,0,0.45)",
      zIndex: 2147483647, display: "flex", alignItems: "center", justifyContent: "center",
    });
    modal.innerHTML =
      "<div style=\"background:#fff;border-radius:12px;width:92vw;max-width:1180px;max-height:88vh;display:flex;flex-direction:column;box-shadow:0 8px 40px rgba(0,0,0,0.25);overflow:hidden;\">" +
        "<div style=\"display:flex;align-items:center;gap:12px;justify-content:space-between;padding:14px 20px;background:linear-gradient(135deg,#1677ff,#0958d9);color:#fff;\">" +
          "<div style=\"min-width:0;\">" +
            "<div style=\"font-size:16px;font-weight:700;\">Temu 轮播图采集（" + items.length + " 张）</div>" +
            "<div style=\"font-size:12px;opacity:.9;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:760px;\">" + escapeHTML(productId || "未识别ID") + " | " + escapeHTML(title || "未识别标题") + "</div>" +
          "</div>" +
          "<button id=\"temu-carousel-close\" style=\"background:rgba(255,255,255,0.2);border:1px solid rgba(255,255,255,0.4);color:#fff;font-size:18px;cursor:pointer;width:32px;height:32px;border-radius:50%;\">X</button>" +
        "</div>" +
        "<div style=\"display:flex;gap:8px;align-items:center;padding:10px 20px;border-bottom:1px solid #eee;\">" +
          "<button id=\"temu-carousel-copy\" style=\"padding:6px 14px;background:#1677ff;color:#fff;border:none;border-radius:6px;cursor:pointer;\">复制URL</button>" +
          "<button id=\"temu-carousel-save-folder\" style=\"padding:6px 14px;background:#13a8a8;color:#fff;border:none;border-radius:6px;cursor:pointer;\">选择文件夹保存图片</button>" +
          "<span style=\"font-size:12px;color:#888;\">优先采集主图/缩略图/懒加载图片，保存时使用页面原始图片地址。</span>" +
        "</div>" +
        "<div style=\"padding:16px 20px;overflow:auto;background:#fafafa;\">" +
          (items.length ? "<div style=\"display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;\">" + cards + "</div>"
            : "<div style=\"text-align:center;color:#999;padding:60px 0;\">没有采集到疑似轮播图。请先打开 Temu 商品详情页，并等待图片加载完成。</div>") +
        "</div>" +
      "</div>";
    document.body.appendChild(modal);
    modal.addEventListener("click", function (e) { if (e.target === modal) modal.remove(); });
    document.getElementById("temu-carousel-close").addEventListener("click", function () { modal.remove(); });
    document.getElementById("temu-carousel-copy").addEventListener("click", function () {
      var selected = selectedCarouselItems(items);
      copyText(selected.map(function (item) { return item.url; }).join("\n")).then(function () {
        showToast("已复制 " + selected.length + " 条轮播图URL");
      });
    });
    document.getElementById("temu-carousel-save-folder").addEventListener("click", function () {
      saveCarouselImagesToFolder(items).catch(function (err) {
        console.error("[TemuFilter v9] save folder failed:", err);
        showToast("保存失败：" + (err && err.message ? err.message : err));
      });
    });
    document.querySelectorAll(".temu-carousel-card").forEach(function (card) {
      card.addEventListener("click", function (e) {
        if (e.target && e.target.tagName === "TEXTAREA") return;
        var checkbox = card.querySelector(".temu-carousel-select");
        checkbox.checked = !checkbox.checked;
        card.style.borderColor = checkbox.checked ? "#1677ff" : "#eee";
        card.style.boxShadow = checkbox.checked ? "0 0 0 2px rgba(22,119,255,.18)" : "none";
        card.style.background = checkbox.checked ? "#f0f7ff" : "#fff";
      });
    });
  }

  // ── 弹窗 ──────────────────────────────────────────
  function showResults(minPct, maxPct, collectedMatches) {
    var old = document.getElementById("temu-filter-modal");
    if (old) old.remove();

    var matches = collectedMatches || getMatchingRows(minPct, maxPct);
    var removedKeys = {};

    function buildSimpleRecord(item, index) {
      if (!item.row && item.skuCode !== undefined) {
        var globalTitle = item.title || "";
        var globalFingerprint = extractTitleFingerprint(globalTitle);
        var globalLookupKey = globalFingerprint || item.skcCode || item.skuCode || "";
        var globalDeclare = "原申报价：￥" + (item.declarePrice ?? "") +
          "\n卖家当前报价：￥" + (item.declarePrice ?? "") +
          "\n参考申报价：￥" + (item.declareReferencePrice ?? "") +
          "\n价差：￥" + (item.diffDeclareReferencePrice ?? "") +
          "\n价差百分比：" + (item.diffPrice ?? "") + "%";
        return {
          key: "global-" + (globalLookupKey || index) + "-" + index,
          title: globalTitle,
          fingerprint: globalFingerprint,
          lookupKey: globalLookupKey,
          lookupKind: globalFingerprint ? "指纹" : (globalLookupKey ? "D值" : "无查行键"),
          image: item.image || "",
          skc: String(item.skc || item.skcCode || ""),
          sku: String(item.sku || item.skuCode || ""),
          declare: globalDeclare,
          reference: String(item.reference || item.referenceText || item.skuCode || "") + (item.referencePrice ? "\n最低参考价：￥" + item.referencePrice : ""),
          priceMatches: item.priceMatches || [],
        };
      }
      var row = item.row;
      var headerIndexes = getHeaderIndexes();
      var productCell = findProductInfoCell(row, headerIndexes);
      var skcCell = getCellByIndex(row, headerIndexes.skc);
      var skuCell = getCellByIndex(row, headerIndexes.sku);
      var declareCell = getCellByIndex(row, headerIndexes.declare);
      var skcText = skcCell ? (skcCell.innerText || skcCell.textContent || "") : "";
      var skuText = skuCell ? (skuCell.innerText || skuCell.textContent || "") : "";
      var skuCodes = extractCargoCodes(skuText);
      var skcCodes = extractCargoCodes(skcText);
      var refs = skuCodes.map(function (code) {
        var price = getConfiguredComparePrice(code);
        return price === null ? code + "：-" : code + "：¥" + price;
      });
      var title = extractProductTitle(productCell);
      var fingerprint = extractTitleFingerprint(title) || extractTitleFingerprint(row.innerText || row.textContent || "");
      var fallbackD = skcCodes[0] || "";
      return {
        key: item.key || getRowIdentity(row, item.pct || "", index) || ("match-" + index),
        title: title,
        fingerprint: fingerprint,
        lookupKey: fingerprint || fallbackD,
        lookupKind: fingerprint ? "指纹" : (fallbackD ? "D值" : "无查行键"),
        image: extractProductImage(productCell),
        skc: skcText.trim(),
        sku: skuText.trim(),
        declare: declareCell ? (declareCell.innerText || declareCell.textContent || "").trim() : "",
        reference: refs.join("\n"),
        priceMatches: item.priceMatches || [],
      };
    }

    var simpleRecords = matches.map(buildSimpleRecord);

    function highlightReferenceDeclare(text) {
      return escapeHTML(text || "").replace(
        /(参考申报价[:：]?(?:\s*¥?\s*\d+(?:\.\d+)?)?)/g,
        '<span class="temu-reference-declare-highlight">$1</span>'
      );
    }

    var modal = document.createElement("div");
    modal.id = "temu-filter-modal";
    Object.assign(modal.style, {
      position: "fixed", top: "0", left: "0", width: "100vw", height: "100vh",
      background: "rgba(0,0,0,0.45)", zIndex: 2147483647,
      display: "flex", alignItems: "center", justifyContent: "center",
    });

    function renderTable() {
      var visibleCount = simpleRecords.filter(function (record) { return !removedKeys[record.key]; }).length;
      var tableHTML = "<div style=\"display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;\">" +
        "<div style=\"font-weight:700;color:#531dab;\">当前显示 " + visibleCount + " / " + simpleRecords.length + " 条</div>" +
        "<div>" +
          "<button id=\"temu-copy-all-visible\" style=\"padding:5px 12px;background:#13a8a8;color:#fff;border:none;border-radius:6px;cursor:pointer;margin-right:6px;\">一键复制全页</button>" +
          "<button id=\"temu-copy-uncopied\" style=\"padding:5px 12px;background:#fa8c16;color:#fff;border:none;border-radius:6px;cursor:pointer;margin-right:6px;\">一键复制未复制</button>" +
          "<button id=\"temu-preview-copied-d\" style=\"padding:5px 12px;background:#fff;color:#13a8a8;border:1px solid #13a8a8;border-radius:6px;cursor:pointer;margin-right:6px;\">预览已复制D</button>" +
          "<button id=\"temu-generate-pruned-workbook\" style=\"padding:5px 12px;background:#52c41a;color:#fff;border:none;border-radius:6px;cursor:pointer;margin-right:6px;\">生成剔除D底表</button>" +
          "<button id=\"temu-preflight-full-workflow\" style=\"padding:5px 12px;background:#fff;color:#2563eb;border:1px solid #2563eb;border-radius:6px;cursor:pointer;margin-right:6px;\">预检完整流程</button>" +
          "<button id=\"temu-run-full-workflow\" style=\"padding:5px 12px;background:#2563eb;color:#fff;border:none;border-radius:6px;cursor:pointer;margin-right:6px;\">生成完整新表</button>" +
          "<button id=\"temu-restore-removed\" style=\"padding:5px 14px;background:#fff;color:#722ed1;border:1px solid #722ed1;border-radius:6px;cursor:pointer;\">恢复已删除</button>" +
        "</div>" +
      "</div>";
      tableHTML += "<div id=\"temu-new-workbook-status\" style=\"display:none;margin:0 0 10px 0;padding:8px 10px;border:1px solid #b7eb8f;background:#f6ffed;border-radius:8px;color:#135200;font-size:12px;white-space:pre-wrap;word-break:break-all;\"></div>";
      tableHTML += "<table style=\"width:100%;border-collapse:collapse;font-size:13px;\"><thead><tr style=\"background:#f9f0ff;\">" +
        "<th style=\"padding:8px 12px;border:1px solid #d3adf7;text-align:left;font-weight:600;color:#531dab;\">首图</th>" +
        "<th style=\"padding:8px 12px;border:1px solid #d3adf7;text-align:left;font-weight:600;color:#531dab;\">标题</th>" +
        "<th style=\"padding:8px 12px;border:1px solid #d3adf7;text-align:left;font-weight:600;color:#531dab;\">SKC属性</th>" +
        "<th style=\"padding:8px 12px;border:1px solid #d3adf7;text-align:left;font-weight:600;color:#531dab;\">SKU属性集</th>" +
        "<th style=\"padding:8px 12px;border:1px solid #d3adf7;text-align:left;font-weight:600;color:#531dab;\">申报价格</th>" +
        "<th style=\"padding:8px 12px;border:1px solid #d3adf7;text-align:left;font-weight:600;color:#531dab;\">最低参考价</th>" +
        "<th style=\"padding:8px 12px;border:1px solid #d3adf7;text-align:left;font-weight:600;color:#531dab;\">操作</th>" +
      "</tr></thead><tbody>";
      simpleRecords.forEach(function (record, index) {
        if (removedKeys[record.key]) return;
        var img = record.image
          ? "<img class=\"temu-match-img\" data-url=\"" + escapeHTML(record.image) + "\" src=\"" + escapeHTML(record.image) + "\" style=\"width:92px;height:92px;object-fit:contain;border:1px solid #ddd;border-radius:6px;cursor:zoom-in;background:#fff;\"/>"
          : "";
        tableHTML += "<tr style=\"border-bottom:1px solid #f0f0f0;\">" +
          "<td style=\"padding:8px 12px;border:1px solid #eee;text-align:center;\">" + img + "</td>" +
          "<td style=\"padding:8px 12px;border:1px solid #eee;white-space:pre-wrap;min-width:260px;max-width:380px;\">" + escapeHTML(record.title) + "</td>" +
          "<td style=\"padding:8px 12px;border:1px solid #eee;white-space:pre-wrap;min-width:150px;\">" + escapeHTML(record.skc) + "</td>" +
          "<td style=\"padding:8px 12px;border:1px solid #eee;white-space:pre-wrap;min-width:170px;\">" + escapeHTML(record.sku) + "</td>" +
          "<td style=\"padding:8px 12px;border:1px solid #eee;white-space:pre-wrap;min-width:130px;\">" + highlightReferenceDeclare(record.declare) + "</td>" +
          "<td style=\"padding:8px 12px;border:1px solid #eee;white-space:pre-wrap;min-width:120px;\">" + escapeHTML(record.reference) + "</td>" +
          "<td style=\"padding:8px 12px;border:1px solid #eee;min-width:112px;\">" +
            "<div style=\"font-size:12px;color:#722ed1;font-weight:700;margin-bottom:6px;\">" + escapeHTML(record.lookupKind + "：" + (record.lookupKey || "-")) + "</div>" +
            "<div id=\"temu-copy-status-" + escapeHTML(record.key) + "\" style=\"font-size:11px;color:#8c8c8c;margin-bottom:6px;\">检查中...</div>" +
            "<button class=\"temu-copy-fingerprint\" data-key=\"" + escapeHTML(record.key) + "\" style=\"padding:5px 10px;background:#13a8a8;color:#fff;border:none;border-radius:6px;cursor:pointer;margin-right:6px;margin-bottom:6px;\">复制</button>" +
            "<button class=\"temu-delete-result\" data-key=\"" + escapeHTML(record.key) + "\" style=\"padding:5px 10px;background:#ff4d4f;color:#fff;border:none;border-radius:6px;cursor:pointer;\">删除</button>" +
          "</td>" +
        "</tr>";
      });
      tableHTML += "</tbody></table>";
      return tableHTML;
    }

    modal.innerHTML =
      "<div style=\"background:#fff;border-radius:12px;width:90vw;max-width:1200px;max-height:85vh;display:flex;flex-direction:column;box-shadow:0 8px 40px rgba(0,0,0,0.25);overflow:hidden;\">" +
        "<div style=\"display:flex;align-items:center;justify-content:space-between;padding:16px 24px;background:linear-gradient(135deg,#722ed1,#531dab);color:#fff;\">" +
          "<div style=\"font-size:16px;font-weight:700;\">筛选结果：" + escapeHTML(getCurrentStoreName()) + " / 参考申报价 ≥ 最低参考价（共 " + matches.length + " 条）</div>" +
          "<button id=\"temu-modal-close\" style=\"background:rgba(255,255,255,0.2);border:1px solid rgba(255,255,255,0.4);color:#fff;font-size:18px;cursor:pointer;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;\">X</button>" +
        "</div>" +
        "<div id=\"temu-result-body\" style=\"flex:1;overflow:auto;padding:16px 24px;\">" +
          (matches.length === 0
            ? "<div style=\"text-align:center;padding:60px 0;color:#999;font-size:15px;\">暂无匹配产品<br><span style=\"font-size:12px;color:#bbb;\">请打开控制台查看解析日志</span></div>"
            : renderTable()) +
        "</div>" +
        "<div style=\"padding:12px 24px;border-top:1px solid #f0f0f0;text-align:right;\">" +
          "<button id=\"temu-modal-close2\" style=\"padding:6px 24px;background:#722ed1;color:#fff;border:none;border-radius:6px;font-size:14px;cursor:pointer;\">关闭</button>" +
        "</div>" +
      "</div>";

    document.body.appendChild(modal);
    modal.addEventListener("click", function (e) { if (e.target === modal) modal.remove(); });
    document.getElementById("temu-modal-close").addEventListener("click", function () { modal.remove(); });
    document.getElementById("temu-modal-close2").addEventListener("click", function () { modal.remove(); });

    function bindResultActions() {
      Array.from(modal.querySelectorAll(".temu-match-img")).forEach(function (img) {
        img.addEventListener("click", function () { showImageZoom(img.getAttribute("data-url")); });
      });
      Array.from(modal.querySelectorAll(".temu-delete-result")).forEach(function (btn) {
        btn.addEventListener("click", function () {
          removedKeys[btn.getAttribute("data-key")] = true;
          document.getElementById("temu-result-body").innerHTML = renderTable();
          bindResultActions();
        });
      });
      Array.from(modal.querySelectorAll(".temu-copy-fingerprint")).forEach(function (btn) {
        btn.addEventListener("click", function () {
          var key = btn.getAttribute("data-key");
          var record = simpleRecords.find(function (item) { return item.key === key; });
          copyFingerprintRows(record).then(function () {
            refreshCopiedBadges();
          }).catch(function (err) {
            console.error("[TemuFilter v9] copy fingerprint failed:", err);
            showToast("复制失败：" + (err && err.message ? err.message : err));
          });
        });
      });
      var restoreBtn = document.getElementById("temu-restore-removed");
      if (restoreBtn) {
        restoreBtn.addEventListener("click", function () {
          removedKeys = {};
          document.getElementById("temu-result-body").innerHTML = renderTable();
          bindResultActions();
          refreshCopiedBadges();
        });
      }
      var copyAllBtn = document.getElementById("temu-copy-all-visible");
      if (copyAllBtn) {
        copyAllBtn.addEventListener("click", function () {
          copyRecordsBatch(false).catch(function (err) {
            console.error("[TemuFilter v9] copy all failed:", err);
            showToast("批量复制失败：" + (err && err.message ? err.message : err));
          });
        });
      }
      var copyUncopiedBtn = document.getElementById("temu-copy-uncopied");
      if (copyUncopiedBtn) {
        copyUncopiedBtn.addEventListener("click", function () {
          copyRecordsBatch(true).catch(function (err) {
            console.error("[TemuFilter v9] copy uncopied failed:", err);
            showToast("批量复制失败：" + (err && err.message ? err.message : err));
          });
        });
      }
      var previewCopiedBtn = document.getElementById("temu-preview-copied-d");
      if (previewCopiedBtn) {
        previewCopiedBtn.addEventListener("click", function () {
          previewCopiedDForStore().catch(function (err) {
            console.error("[TemuFilter v9] preview copied D failed:", err);
            showToast("预览已复制D失败：" + (err && err.message ? err.message : err));
          });
        });
      }
      var generatePrunedBtn = document.getElementById("temu-generate-pruned-workbook");
      if (generatePrunedBtn) {
        generatePrunedBtn.addEventListener("click", function () {
          generatePrunedWorkbookForStore().catch(function (err) {
            console.error("[TemuFilter v9] generate pruned workbook failed:", err);
            showToast("生成新表格失败：" + (err && err.message ? err.message : err));
          });
        });
      }
      var runFullBtn = document.getElementById("temu-run-full-workflow");
      if (runFullBtn) {
        runFullBtn.addEventListener("click", function () {
          runFullWorkflowForStore().catch(function (err) {
            console.error("[TemuFilter v9] run full workflow failed:", err);
            showToast("生成完整新表失败：" + (err && err.message ? err.message : err));
          });
        });
      }
      var preflightFullBtn = document.getElementById("temu-preflight-full-workflow");
      if (preflightFullBtn) {
        preflightFullBtn.addEventListener("click", function () {
          preflightFullWorkflowForStore().catch(function (err) {
            console.error("[TemuFilter v9] preflight full workflow failed:", err);
            showToast("预检完整流程失败：" + (err && err.message ? err.message : err));
          });
        });
      }
    }

    function refreshCopiedBadges() {
      simpleRecords.forEach(function (record) {
        var badge = document.getElementById("temu-copy-status-" + record.key);
        if (!badge) return;
        if (!record.lookupKey) {
          badge.textContent = "无查行键";
          return;
        }
        getCopiedStatus(record).then(function (status) {
          if (!status || !status.copied) {
            badge.textContent = "未复制";
            badge.style.color = "#8c8c8c";
            return;
          }
          var latest = status.latest || {};
          badge.textContent = "已复制 " + status.count + " 次" + (latest.copied_at ? " / " + latest.copied_at : "");
          badge.style.color = "#fa8c16";
        });
      });
    }

    async function copyRecordsBatch(onlyUncopied) {
      var targets = simpleRecords.filter(function (record) {
        return !removedKeys[record.key] && record.lookupKey;
      });
      var seenLookup = {};
      var chunks = [];
      var copiedCount = 0;
      for (var i = 0; i < targets.length; i++) {
        var record = targets[i];
        if (seenLookup[record.lookupKey]) continue;
        seenLookup[record.lookupKey] = true;
        if (onlyUncopied) {
          var status = await getCopiedStatus(record);
          if (status && status.copied) continue;
        }
        var rowsData = await fetchFingerprintRowsData(record.lookupKey);
        if (!rowsData || !rowsData.text) continue;
        chunks.push(rowsData.text);
        await recordCopiedEvent(record, rowsData.item);
        copiedCount++;
      }
      if (!chunks.length) {
        showToast(onlyUncopied ? "没有未复制的可复制记录" : "没有可复制记录");
        return;
      }
      await copyText(chunks.join("\r\n"));
      showToast("已复制并记录 " + copiedCount + " 组D行");
      refreshCopiedBadges();
    }

    function setNewWorkbookStatus(message, isError) {
      var box = document.getElementById("temu-new-workbook-status");
      if (!box) return;
      box.style.display = "block";
      box.style.borderColor = isError ? "#ffa39e" : "#b7eb8f";
      box.style.background = isError ? "#fff1f0" : "#f6ffed";
      box.style.color = isError ? "#a8071a" : "#135200";
      box.textContent = message;
    }

    async function previewCopiedDForStore() {
      var store = getCurrentStoreName();
      setNewWorkbookStatus("正在读取 " + store + " 的已复制D记录……", false);
      var res = await fetch(
        "http://127.0.0.1:8765/api/store-passed-d?store=" + encodeURIComponent(store),
        { method: "GET", cache: "no-store" }
      );
      if (!res.ok) throw new Error(await res.text());
      var data = await res.json();
      var dValues = data.d_values || [];
      setNewWorkbookStatus(
        "店铺：" + data.store + "\n" +
        "复制事件：" + data.event_count + " 条\n" +
        "唯一D：" + data.d_count + " 个\n" +
        "将剔除：\n" + (dValues.join("\n") || "-"),
        false
      );
    }

    async function generatePrunedWorkbookForStore() {
      var store = getCurrentStoreName();
      setNewWorkbookStatus("正在按 " + store + " 的已复制D生成新底表……", false);
      var res = await fetch(
        "http://127.0.0.1:8765/api/store-pruned-workbook?store=" + encodeURIComponent(store),
        { method: "GET", cache: "no-store" }
      );
      if (!res.ok) throw new Error(await res.text());
      var data = await res.json();
      if (!data.ok) {
        setNewWorkbookStatus(data.error || "生成失败", true);
        return;
      }
      setNewWorkbookStatus(
        "已生成新底表（过程文件，不入D搜索库）\n" +
        "店铺：" + data.store + "\n" +
        "源表：" + data.source + "\n" +
        "输出：" + data.output + "\n" +
        "报告：" + (data.report || "-") + "\n" +
        "已复制D：" + data.passed_d_count + " 个\n" +
        "剔除：" + data.removed_d_count + " 个D / " + data.removed_row_count + " 行\n" +
        "保留：" + data.kept_row_count + " 行\n\n" +
        "下一步：用这个底表继续跑标题、T、J、U；最终确认上传后，再让最终表入库。",
        false
      );
      showPersistentWorkbookResult(data);
      try { await copyText(data.output || ""); } catch (err) {}
      showToast("已生成新底表，路径已复制：" + data.removed_d_count + " 个D / " + data.removed_row_count + " 行");
    }

    async function runFullWorkflowForStore() {
      var store = getCurrentStoreName();
      setNewWorkbookStatus("正在启动完整流程任务：" + store + "……", false);
      var body = new URLSearchParams();
      body.set("action", "store_full_workflow");
      body.set("store", store);
      var res = await fetch("http://127.0.0.1:8765/api/run", {
        method: "POST",
        body: body,
      });
      if (!res.ok) throw new Error(await res.text());
      var job = await res.json();
      var meta = job.meta || {};
      setNewWorkbookStatus(
        "完整流程任务已启动\n" +
        "任务ID：" + job.id + "\n" +
        "输入底表：" + (meta.source || "自动选择最新剔除D底表") + "\n" +
        "预计最终表：" + (meta.final_workbook || "-") + "\n" +
        "预计复检页：" + (meta.review_url || "-") + "\n\n" +
        "请打开后台任务日志查看进度：http://127.0.0.1:8765/",
        false
      );
      showPersistentFullWorkflowResult(job);
      showToast("完整流程任务已启动：" + job.id);
    }

    async function preflightFullWorkflowForStore() {
      var store = getCurrentStoreName();
      setNewWorkbookStatus("正在预检完整流程：" + store + "……", false);
      var res = await fetch(
        "http://127.0.0.1:8765/api/store-full-preflight?store=" + encodeURIComponent(store),
        { method: "GET", cache: "no-store" }
      );
      if (!res.ok) throw new Error(await res.text());
      var data = await res.json();
      var stats = data.stats || {};
      setNewWorkbookStatus(
        (data.ok ? "预检通过，可以启动完整流程\n" : "预检未通过，先修正错误\n") +
        "底表：" + (data.source || "-") + "\n" +
        "有效行/唯一D：" + (stats.effective_rows || 0) + " / " + (stats.unique_d || 0) + "\n" +
        "已复制D残留：" + (stats.residual_passed_row_count || 0) + "\n" +
        "缺指纹/重复指纹：" + (stats.missing_fingerprint_count || 0) + " / " + (stats.duplicate_fingerprint_count || 0) + "\n" +
        "T4尺寸位风险：" + (stats.bad_t4_count || 0) + "\n" +
        "错误：" + ((data.errors || []).join("；") || "无") + "\n" +
        "警告：" + ((data.warnings || []).join("；") || "无"),
        !data.ok
      );
      showToast(data.ok ? "完整流程预检通过" : "完整流程预检未通过");
    }

    bindResultActions();
    refreshCopiedBadges();
  }

  // ── Toast ───────────────────────────────────────────
  function showPersistentWorkbookResult(data) {
    var old = document.getElementById("temu-generated-workbook-result");
    if (old) old.remove();
    var box = document.createElement("div");
    box.id = "temu-generated-workbook-result";
    Object.assign(box.style, {
      position: "fixed",
      right: "18px",
      bottom: "18px",
      width: "420px",
      maxWidth: "calc(100vw - 36px)",
      background: "#fff",
      color: "#135200",
      border: "2px solid #52c41a",
      borderRadius: "12px",
      boxShadow: "0 8px 32px rgba(0,0,0,0.28)",
      zIndex: 2147483647,
      padding: "14px",
      fontSize: "13px",
      lineHeight: "1.45",
    });
    box.innerHTML =
      "<div style=\"display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:8px;\">" +
        "<b style=\"font-size:15px;color:#135200;\">✅ 新底表已生成</b>" +
        "<button id=\"temu-generated-workbook-close\" style=\"border:none;background:#f0f0f0;border-radius:50%;width:26px;height:26px;cursor:pointer;\">×</button>" +
      "</div>" +
      "<div>店铺：<b>" + escapeHTML(data.store || "-") + "</b></div>" +
      "<div>剔除：<b>" + escapeHTML(data.removed_d_count || 0) + "</b> 个D / <b>" + escapeHTML(data.removed_row_count || 0) + "</b> 行；保留 <b>" + escapeHTML(data.kept_row_count || 0) + "</b> 行</div>" +
      "<div style=\"margin-top:8px;color:#555;\">新表路径（已自动复制）：</div>" +
      "<div style=\"margin-top:4px;padding:8px;background:#f6ffed;border:1px solid #b7eb8f;border-radius:8px;word-break:break-all;white-space:pre-wrap;max-height:92px;overflow:auto;\">" + escapeHTML(data.output || "-") + "</div>" +
      "<div style=\"display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;\">" +
        "<button id=\"temu-generated-workbook-copy\" style=\"padding:6px 10px;background:#52c41a;color:#fff;border:none;border-radius:6px;cursor:pointer;\">复制新表路径</button>" +
        "<button id=\"temu-generated-workbook-report\" style=\"padding:6px 10px;background:#13a8a8;color:#fff;border:none;border-radius:6px;cursor:pointer;\">复制报告路径</button>" +
        "<button id=\"temu-generated-workbook-run-full\" style=\"padding:6px 10px;background:#2563eb;color:#fff;border:none;border-radius:6px;cursor:pointer;\">基于底表生成完整套表</button>" +
        "<button id=\"temu-generated-workbook-panel\" style=\"padding:6px 10px;background:#722ed1;color:#fff;border:none;border-radius:6px;cursor:pointer;\">打开后台</button>" +
      "</div>" +
      "<div style=\"margin-top:8px;color:#8c8c8c;font-size:12px;\">这是过程底表，不入D搜索库。后续用它继续跑标题、T、J、U。</div>";
    document.body.appendChild(box);
    document.getElementById("temu-generated-workbook-close").addEventListener("click", function () { box.remove(); });
    document.getElementById("temu-generated-workbook-copy").addEventListener("click", function () {
      copyText(data.output || "");
      showToast("已复制新表路径");
    });
    document.getElementById("temu-generated-workbook-report").addEventListener("click", function () {
      copyText(data.report || "");
      showToast("已复制报告路径");
    });
    document.getElementById("temu-generated-workbook-panel").addEventListener("click", function () {
      window.open("http://127.0.0.1:8765/", "_blank", "noopener,noreferrer");
    });
    document.getElementById("temu-generated-workbook-run-full").addEventListener("click", function () {
      runFullWorkflowForStore().catch(function (err) {
        showToast("生成完整套表失败：" + (err && err.message ? err.message : err));
      });
    });
  }

  function showPersistentFullWorkflowResult(job) {
    var old = document.getElementById("temu-full-workflow-result");
    if (old) old.remove();
    var meta = job.meta || {};
    var box = document.createElement("div");
    box.id = "temu-full-workflow-result";
    Object.assign(box.style, {
      position: "fixed",
      right: "18px",
      bottom: "18px",
      width: "440px",
      maxWidth: "calc(100vw - 36px)",
      background: "#fff",
      color: "#12356b",
      border: "2px solid #2563eb",
      borderRadius: "12px",
      boxShadow: "0 8px 32px rgba(0,0,0,0.28)",
      zIndex: 2147483647,
      padding: "14px",
      fontSize: "13px",
      lineHeight: "1.45",
    });
    box.innerHTML =
      "<div style=\"display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:8px;\">" +
        "<b style=\"font-size:15px;color:#12356b;\">🚀 完整新表任务已启动</b>" +
        "<button id=\"temu-full-workflow-close\" style=\"border:none;background:#f0f0f0;border-radius:50%;width:26px;height:26px;cursor:pointer;\">×</button>" +
      "</div>" +
      "<div>任务ID：<b>" + escapeHTML(job.id || "-") + "</b></div>" +
      "<div id=\"temu-full-workflow-status\" style=\"margin-top:6px;padding:6px 8px;background:#eff6ff;border-radius:8px;color:#1d4ed8;font-weight:700;\">状态：queued，正在等待后台接手……</div>" +
      "<div style=\"margin-top:8px;color:#555;\">预计最终表：</div>" +
      "<div style=\"margin-top:4px;padding:8px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;word-break:break-all;white-space:pre-wrap;max-height:88px;overflow:auto;\">" + escapeHTML(meta.final_workbook || "-") + "</div>" +
      "<div id=\"temu-full-workflow-log\" style=\"margin-top:8px;padding:8px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;color:#475569;font-size:12px;white-space:pre-wrap;max-height:110px;overflow:auto;\">等待日志……</div>" +
      "<div style=\"display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;\">" +
        "<button id=\"temu-full-workflow-panel\" style=\"padding:6px 10px;background:#2563eb;color:#fff;border:none;border-radius:6px;cursor:pointer;\">打开任务后台</button>" +
        "<button id=\"temu-full-workflow-copy\" style=\"padding:6px 10px;background:#13a8a8;color:#fff;border:none;border-radius:6px;cursor:pointer;\">复制最终表路径</button>" +
        "<button id=\"temu-full-workflow-review\" style=\"padding:6px 10px;background:#722ed1;color:#fff;border:none;border-radius:6px;cursor:pointer;\">复制复检页</button>" +
        "<button id=\"temu-full-workflow-open-review\" style=\"padding:6px 10px;background:#16a34a;color:#fff;border:none;border-radius:6px;cursor:pointer;\">打开复检页</button>" +
      "</div>" +
      "<div id=\"temu-full-workflow-footnote\" style=\"margin-top:8px;color:#8c8c8c;font-size:12px;\">任务在后台跑；此卡片每 3 秒刷新一次。完成后先看复检页，再确认最终表入库。</div>";
    document.body.appendChild(box);
    document.getElementById("temu-full-workflow-close").addEventListener("click", function () {
      if (box._pollTimer) clearInterval(box._pollTimer);
      box.remove();
    });
    document.getElementById("temu-full-workflow-panel").addEventListener("click", function () {
      window.open("http://127.0.0.1:8765/", "_blank", "noopener,noreferrer");
    });
    document.getElementById("temu-full-workflow-copy").addEventListener("click", function () {
      copyText(meta.final_workbook || "");
      showToast("已复制最终表路径");
    });
    document.getElementById("temu-full-workflow-review").addEventListener("click", function () {
      copyText(meta.review_url || "");
      showToast("已复制复检页链接");
    });
    document.getElementById("temu-full-workflow-open-review").addEventListener("click", function () {
      if (meta.review_url) window.open(meta.review_url, "_blank", "noopener,noreferrer");
    });
    pollFullWorkflowJob(job.id, meta, box);
  }

  async function pollFullWorkflowJob(jobId, meta, box) {
    if (!jobId || !box || !document.body.contains(box)) return;
    var statusBox = document.getElementById("temu-full-workflow-status");
    var logBox = document.getElementById("temu-full-workflow-log");
    var foot = document.getElementById("temu-full-workflow-footnote");
    try {
      var res = await fetch("http://127.0.0.1:8765/api/jobs/" + encodeURIComponent(jobId), {
        method: "GET",
        cache: "no-store",
      });
      if (!res.ok) throw new Error(await res.text());
      var data = await res.json();
      var status = data.status || "unknown";
      var color = status === "completed" ? "#15803d" : status === "failed" ? "#b91c1c" : "#1d4ed8";
      var bg = status === "completed" ? "#f0fdf4" : status === "failed" ? "#fef2f2" : "#eff6ff";
      if (statusBox) {
        statusBox.style.color = color;
        statusBox.style.background = bg;
        statusBox.textContent = "状态：" + status + (data.returncode !== null && data.returncode !== undefined ? " / code " + data.returncode : "") + (data.pid ? " / PID " + data.pid : "");
      }
      if (logBox) {
        var log = String(data.log || "").trim();
        var lines = log ? log.split(/\r?\n/).slice(-12).join("\n") : "等待日志……";
        logBox.textContent = lines;
        logBox.scrollTop = logBox.scrollHeight;
      }
      if (status === "completed") {
        if (box._pollTimer) clearInterval(box._pollTimer);
        if (foot) foot.textContent = "任务已完成。请打开复检页检查 T/J，再确认最终表入库。";
        showToast("完整新表任务已完成");
        return;
      }
      if (status === "failed") {
        if (box._pollTimer) clearInterval(box._pollTimer);
        if (foot) foot.textContent = "任务失败。请打开后台查看完整日志，或把错误发给我。";
        showToast("完整新表任务失败");
        return;
      }
    } catch (err) {
      if (statusBox) {
        statusBox.style.color = "#b91c1c";
        statusBox.style.background = "#fef2f2";
        statusBox.textContent = "状态读取失败：" + (err && err.message ? err.message : err);
      }
    }
    if (!box._pollTimer) {
      box._pollTimer = setInterval(function () {
        pollFullWorkflowJob(jobId, meta, box);
      }, 3000);
    }
  }

  function showToast(msg) {
    var toast = document.getElementById("temu-filter-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "temu-filter-toast";
      Object.assign(toast.style, {
        position: "fixed", top: "60px", right: "20px",
        background: "linear-gradient(135deg,#722ed1,#531dab)",
        color: "#fff", padding: "12px 20px", borderRadius: "8px",
        zIndex: 2147483647, fontSize: "14px", fontWeight: "600",
        boxShadow: "0 4px 16px rgba(114,46,209,0.4)",
        transition: "opacity 0.3s", opacity: "1",
      });
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = "1";
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function () { toast.style.opacity = "0"; }, 3000);
  }

  // ── 找到主内容区（有滚动的容器）─────────────────
  function findMainContentContainer() {
    // React SPA 的主内容区通常有 overflow 和固定高度
    var candidates = document.querySelectorAll("[style*=\"overflow\"]");
    for (var i = 0; i < candidates.length; i++) {
      var el = candidates[i];
      var style = getComputedStyle(el);
      if ((style.overflow === "auto" || style.overflow === "scroll" || style.overflowY === "auto" || style.overflowY === "scroll")
          && el.scrollHeight > el.clientHeight + 50) {
        console.log("[TemuFilter v9] Found scroll container:", el.tagName, el.className.substring(0, 60));
        return el;
      }
    }
    // 兜底：返回 body
    return document.body;
  }

  // ── 创建面板 ──────────────────────────────────────
  function createPanel() {
    var wrapper = document.createElement("div");
    wrapper.id = "temu-filter-panel";

    var savedMin = localStorage.getItem(STORAGE_KEY_MIN);
    var savedMax = localStorage.getItem(STORAGE_KEY_MAX);
    var savedStore = localStorage.getItem(STORAGE_KEY_STORE) || DEFAULT_STORE;
    var minVal = savedMin !== null ? savedMin : DEFAULT_MIN;
    var maxVal = savedMax !== null ? savedMax : DEFAULT_MAX;

    // fixed 定位在页面最顶部，但用 padding 推开内容
    Object.assign(wrapper.style, {
      position: "fixed",
      top: "0",
      left: "0",
      width: "100%",
      zIndex: 9999,
      display: "flex",
      alignItems: "center",
      gap: "8px",
      padding: "8px 16px",
      background: "linear-gradient(135deg, #f9f0ff, #efdbff)",
      borderBottom: "2px solid #722ed1",
      fontSize: "13px",
      flexWrap: "wrap",
      boxSizing: "border-box",
      boxShadow: "0 2px 8px rgba(114,46,209,0.15)",
    });

    wrapper.innerHTML =
      "<span style=\"color:#531dab;font-weight:700;white-space:nowrap;\">⚡ 参考价筛选</span>" +
      "<input id=\"temu-filter-store\" type=\"text\" value=\"" + escapeHTML(savedStore) + "\" list=\"temu-store-list\" title=\"当前店铺，用于记录已复制D\" style=\"width:92px;padding:4px 8px;border-radius:6px;border:1px solid #d3adf7;font-size:13px;text-align:center;font-weight:700;color:#531dab;\" />" +
      "<datalist id=\"temu-store-list\"><option value=\"DXXmall\"><option value=\"CXXmall\"><option value=\"FXXmall\"></datalist>" +
      "<input id=\"temu-filter-min\" type=\"hidden\" value=\"" + minVal + "\" />" +
      "<input id=\"temu-filter-max\" type=\"hidden\" value=\"" + maxVal + "\" />" +
      "<span style=\"color:#531dab;font-weight:600;background:#fff;border:1px solid #d3adf7;border-radius:999px;padding:3px 10px;\">参考申报价 ≥ 最低参考价</span>" +
      "<button id=\"temu-filter-extract-btn\" style=\"padding:4px 16px;background:#722ed1;color:#fff;border:none;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;\" title=\"只采集当前页/当前已加载列表，不翻分页\">当前页采集</button>" +
      "<button id=\"temu-global-scan-btn\" style=\"padding:4px 16px;background:#13a8a8;color:#fff;border:none;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;\" title=\"自动翻页扫描所有分页，并打开同一套筛选结果\">全局翻页筛选</button>" +
      "<button id=\"temu-record-page-btn\" style=\"padding:4px 12px;background:#fff;color:#2563eb;border:1px solid #2563eb;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;\" title=\"如果自动翻页失败，先点这里录制一次下一页按钮\">录制翻页</button>" +
      "<button id=\"temu-backend-open-btn\" style=\"padding:4px 16px;background:#fa8c16;color:#fff;border:none;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;\">D后台</button>" +
      "<button id=\"temu-carousel-collect-btn\" style=\"padding:4px 16px;background:#1677ff;color:#fff;border:none;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;\">采集轮播图</button>" +
      "<button id=\"temu-filter-reset-btn\" style=\"padding:4px 16px;background:#fff;color:#722ed1;border:1px solid #722ed1;border-radius:6px;font-size:13px;cursor:pointer;white-space:nowrap;\">重置</button>" +
      "<span id=\"temu-filter-count\" style=\"color:#8c8c8c;font-size:12px;margin-left:auto;\"></span>";

    console.log("[TemuFilter v9] Panel created, min=" + minVal + " max=" + maxVal);
    return wrapper;
  }

  // ── 插入面板 ──────────────────────────────────────
  var PANEL_HEIGHT = 45;

  function insertPanel() {
    if (document.getElementById("temu-filter-panel")) {
      console.log("[TemuFilter v9] Panel exists, skip");
      return;
    }

    var panel = createPanel();

    // 1. 面板加到 body
    document.body.appendChild(panel);

    // 2. 找到主滚动容器，给它加 padding-top 把内容推下去
    var container = findMainContentContainer();
    if (container !== document.body) {
      var currentPad = parseInt(getComputedStyle(container).paddingTop) || 0;
      container.style.paddingTop = (currentPad + PANEL_HEIGHT) + "px";
      container.dataset.temuFilterPad = "1";
      console.log("[TemuFilter v9] Added padding-top to scroll container");
    } else {
      // 如果找不到滚动容器，尝试给 html/body 加
      document.documentElement.style.paddingTop = PANEL_HEIGHT + "px";
      console.log("[TemuFilter v9] Added padding-top to html (fallback)");
    }

    // 3. 绑定事件
    var inputMin = document.getElementById("temu-filter-min");
    var inputMax = document.getElementById("temu-filter-max");
    var storeInput = document.getElementById("temu-filter-store");
    var btn     = document.getElementById("temu-filter-extract-btn");
    var globalScanBtn = document.getElementById("temu-global-scan-btn");
    var recordPageBtn = document.getElementById("temu-record-page-btn");
    var backendBtn = document.getElementById("temu-backend-open-btn");
    var carouselBtn = document.getElementById("temu-carousel-collect-btn");
    var reset   = document.getElementById("temu-filter-reset-btn");
    var count   = document.getElementById("temu-filter-count");

    if (!btn) { console.log("[TemuFilter v9] ERROR: button not found"); return; }
    if (storeInput) {
      storeInput.addEventListener("change", function () {
        localStorage.setItem(STORAGE_KEY_STORE, getCurrentStoreName());
        showToast("当前店铺：" + getCurrentStoreName());
      });
      storeInput.addEventListener("blur", function () {
        localStorage.setItem(STORAGE_KEY_STORE, getCurrentStoreName());
      });
    }

    var isExtracting = false;
    btn.addEventListener("click", async function () {
      if (isExtracting) {
        showToast("正在自动滚动采集中，请稍候");
        return;
      }
      var minV = 0;
      var maxV = 100;
      localStorage.setItem(STORAGE_KEY_MIN, minV);
      localStorage.setItem(STORAGE_KEY_MAX, maxV);
      isExtracting = true;
      btn.disabled = true;
      btn.textContent = "采集中...";
      count.textContent = "正在定位数据滚动条，采集参考申报价达到最低参考价的数据...";
      try {
        var matches = await autoScrollCollectMatchingRows(minV, maxV, function (progress) {
          var percent = progress.max > 0 ? Math.min(100, Math.round(progress.top / progress.max * 100)) : 100;
          count.textContent = "采集 " + percent + "%，命中 " + progress.matches + " 条";
        });
        count.textContent = "命中 " + matches.length + " 条";
        showResults(minV, maxV, matches);
      } catch (err) {
        console.error("[TemuFilter v9] auto extract failed:", err);
        showToast("自动采集失败，已尝试读取当前可见数据");
        var fallbackMatches = getMatchingRows(minV, maxV);
        count.textContent = "命中 " + fallbackMatches.length + " 条";
        showResults(minV, maxV, fallbackMatches);
      } finally {
        isExtracting = false;
        btn.disabled = false;
        btn.textContent = "当前页采集";
      }
    });

    var isGlobalScanning = false;
    globalScanBtn.addEventListener("click", async function () {
      if (isGlobalScanning || isExtracting) {
        showToast("已有采集任务正在执行，请稍候");
        return;
      }
      var minV = 0;
      var maxV = 100;
      localStorage.setItem(STORAGE_KEY_MIN, minV);
      localStorage.setItem(STORAGE_KEY_MAX, maxV);
      isGlobalScanning = true;
      globalScanBtn.disabled = true;
      btn.disabled = true;
      globalScanBtn.textContent = "扫描中...";
      count.textContent = "正在全局扫描参考申报价达到最低参考价的数据...";
      try {
        var records = await globalScanAllPages(minV, maxV, function (progress) {
          if (progress.stoppedByJump) {
            count.textContent = "分页异常：从第 " + progress.page + " 页跳到第 " + progress.jumpedPage + " 页，已停止并导出已扫描结果";
            return;
          }
          if (progress.turning) {
            count.textContent = "第 " + progress.page + "/" + (progress.totalPage || "?") + " 页完成，已暂存 " + progress.total + " 条，准备翻页...";
            return;
          }
          var percent = progress.max > 0 ? Math.min(100, Math.round(progress.top / progress.max * 100)) : 100;
          count.textContent = "第 " + progress.page + "/" + (progress.totalPage || "?") + " 页 " + percent + "%，已暂存 " + progress.total + " 条";
        });
        count.textContent = "全局扫描完成，命中 " + records.length + " 条";
        if (records.length > 0) {
          downloadGlobalScanExcel(records);
          showResults(minV, maxV, records);
          showToast("全局扫描完成，已打开结果并导出 Excel：" + records.length + " 条");
        } else {
          showToast("未找到参考申报价达到最低参考价的数据");
        }
      } catch (err) {
        console.error("[TemuFilter v9] global scan failed:", err);
        showToast("全局扫描失败：" + (err && err.message ? err.message : err));
      } finally {
        isGlobalScanning = false;
        globalScanBtn.disabled = false;
        btn.disabled = false;
        globalScanBtn.textContent = "全局翻页筛选";
      }
    });

    backendBtn.addEventListener("click", function () {
      openDSearchBackend();
    });

    recordPageBtn.addEventListener("click", function () {
      startRecordNextPageReplay();
    });

    carouselBtn.addEventListener("click", function () {
      showCarouselResults();
    });

    reset.addEventListener("click", function () {
      inputMin.value = DEFAULT_MIN;
      inputMax.value = DEFAULT_MAX;
      localStorage.removeItem(STORAGE_KEY_MIN);
      localStorage.removeItem(STORAGE_KEY_MAX);
      count.textContent = "";
      var old = document.getElementById("temu-filter-modal");
      if (old) old.remove();
      showToast("已重置");
    });

    [inputMin, inputMax].forEach(function (inp) {
      inp.addEventListener("keyup", function (e) { if (e.key === "Enter") btn.click(); });
    });

    console.log("[TemuFilter v9] Panel ready");
  }

  // ── 移除面板（路由切换时）─────────────────────────
  function removePanel() {
    var old = document.getElementById("temu-filter-panel");
    if (old) old.remove();
    // 还原 padding
    document.querySelectorAll("[data-temu-filter-pad]").forEach(function (el) {
      delete el.dataset.temuFilterPad;
    });
    document.documentElement.style.paddingTop = "";
  }

  // ── 初始化 ────────────────────────────────────────
  function scheduleInit() {
    [500, 1500, 3000, 5000].forEach(function (delay) {
      setTimeout(function () {
        if (!document.getElementById("temu-filter-panel")) {
          console.log("[TemuFilter v9] Retry after " + delay + "ms");
          insertPanel();
        }
      }, delay);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleInit);
  } else {
    scheduleInit();
  }

  var lastUrl = location.href;
  new MutationObserver(function () {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      setTimeout(function () {
        removePanel();
        scheduleInit();
      }, 1500);
    }
  }).observe(document.body, { childList: true, subtree: true });

  console.log("[TemuFilter v9] init complete");
})();
