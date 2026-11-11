/*! justified-gallery v4.0.2 | MIT License
 * https://github.com/miromannino/Justified-Gallery
 * Vendored verbatim from
 * https://cdn.jsdelivr.net/npm/justified-gallery@4.0.2/dist/justified-gallery.js
 * ES module: load it with <script type="module">. Do not edit by hand.
 */
//#region src/helpers.ts
var e = () => {
	let e = document.createElement("div");
	e.className = "jg-spinner";
	for (let t = 0; t < 3; t++) {
		let t = document.createElement("span");
		e.appendChild(t);
	}
	return e;
}, t = (e) => {
	let t, n, r;
	for (t = e.length - 1; t > 0; t--) n = Math.floor(Math.random() * (t + 1)), r = e[t], e[t] = e[n], e[n] = r;
	return e;
}, n = (e, t) => {
	let n = e[t];
	if (typeof n == "string" && (e[t] = parseFloat(n)), typeof e[t] == "number") {
		if (isNaN(e[t])) throw Error(`Invalid number for ${t}`);
	} else throw Error(`${t} must be a number`);
}, r = /* @__PURE__ */ function(e) {
	return e.JUSTIFY = "justify", e.NO_JUSTIFY = "nojustify", e.LEFT = "left", e.CENTER = "center", e.RIGHT = "right", e.HIDE = "hide", e;
}({}), i = (e) => {
	if (typeof e.sizeRangeSuffixes != "object" || e.sizeRangeSuffixes === null) throw Error("sizeRangeSuffixes must be defined and must be an object");
	let t = Object.keys(e.sizeRangeSuffixes), n = {};
	for (let r of t) {
		let t = parseInt(r.replace(/^[a-z]+/, ""), 10);
		if (isNaN(t)) throw Error(`sizeRangeSuffixes keys must contain correct numbers (invalid key '${r}')`);
		n[t] = e.sizeRangeSuffixes[r];
	}
	e.sizeRangeSuffixes = n;
}, a = (e) => Object.keys(e.sizeRangeSuffixes).map((e) => parseInt(e, 10)).sort((e, t) => e - t), o = (e) => {
	if (i(e), n(e, "rowHeight"), n(e, "margins"), n(e, "border"), n(e, "maxRowsCount"), !Object.values(r).includes(e.lastRow)) throw Error(`lastRow must be one of: ${Object.values(r).join(", ")}`);
	if (n(e, "justifyThreshold"), e.justifyThreshold < 0 || e.justifyThreshold > 1) throw Error("justifyThreshold must be in the interval [0, 1]");
	if (typeof e.captions != "boolean") throw Error("captions must be a boolean");
	if (n(e, "refreshTime"), n(e, "refreshSensitivity"), typeof e.randomize != "boolean") throw Error("randomize must be a boolean");
	if (typeof e.selector != "string") throw Error("selector must be a string");
	if (e.sort !== !1 && typeof e.sort != "function") throw Error("sort must be false or a comparison function");
	if (e.filter !== !1 && typeof e.filter != "function" && typeof e.filter != "string") throw Error("filter must be false, a string, or a filter function");
}, s = (e) => {
	let { rowHeight: t, maxRowHeight: n } = e, r;
	if (typeof n == "string") {
		let e = n.match(/^([0-9]+)%$/);
		r = e ? t * parseFloat(e[1]) / 100 : parseFloat(n);
	} else if (typeof n == "number") r = n;
	else if (n === !1 || n == null) return;
	else throw Error("maxRowHeight must be a number or a percentage");
	if (isNaN(r)) throw Error("Invalid number for maxRowHeight");
	return Math.max(r, t);
}, c = {
	sizeRangeSuffixes: {
		100: "_t",
		240: "_m",
		320: "_n",
		500: "",
		640: "_z",
		1024: "_b"
	},
	thumbnailPath: void 0,
	rowHeight: 120,
	maxRowHeight: !1,
	maxRowsCount: 0,
	margins: 1,
	border: -1,
	lastRow: r.NO_JUSTIFY,
	justifyThreshold: .9,
	waitThumbnailsLoad: !0,
	captions: !0,
	rel: null,
	target: null,
	extension: /\.[^.\\/]+$/,
	refreshTime: 200,
	refreshSensitivity: 0,
	randomize: !1,
	rtl: !1,
	sort: !1,
	filter: !1,
	selector: "a",
	imgSelector: "img, a > img, svg, a > svg",
	triggerEvent: () => {}
}, l = (e, t) => e.querySelector(t), u = (e) => e.querySelector(".jg-caption"), d = (e) => e != null && e.trim().length > 0, f = (e, t) => {
	e.classList.add("jg-entry-visible"), t && t();
}, p = (e, t, n) => {
	let r = l(e, t);
	if (r && n) {
		let t = u(e);
		if (t === null) {
			let n = r.getAttribute("alt");
			d(n) || (n = e.getAttribute("title")), d(n) && (t = document.createElement("div"), t.className = "jg-caption", t.textContent = n, e.appendChild(t), e.dataset.jgCreatedCaption = "true");
		}
	}
}, m = (e, t) => Array.from(e.children).filter((e) => e.classList.contains("jg-spinner") ? !1 : e.matches(t) || e.matches("div")), h = (e, t) => {
	let n = [], r = e.nextElementSibling;
	for (; r;) !r.classList.contains("jg-spinner") && r.matches(t) && n.push(r), r = r.nextElementSibling;
	return n;
}, g = (e) => {
	e.forEach((e) => e.classList.remove("jg-filtered"));
}, _ = (e, t) => {
	if (typeof t == "string") return e.filter((e) => e.matches(t) ? (e.classList.remove("jg-filtered"), !0) : (e.classList.add("jg-filtered"), e.classList.remove("jg-entry-visible"), !1));
	if (typeof t == "function") {
		let n = e.filter(t);
		return e.forEach((e) => {
			n.includes(e) ? e.classList.remove("jg-filtered") : (e.classList.add("jg-filtered"), e.classList.remove("jg-entry-visible"));
		}), n;
	}
	return e;
}, v = /* @__PURE__ */ function(e) {
	return e.RowFlush = "jg.rowflush", e.Resize = "jg.resize", e.Complete = "jg.complete", e.Destroy = "jg.destroy", e;
}({}), y = class {
	constructor(e) {
		this.gallery = e, this.prevStaticHeight = 0;
	}
	remember() {
		this.prevStaticHeight = this.gallery.clientHeight, this.gallery.style.height = `${this.prevStaticHeight}px`;
	}
	setTemp(e) {
		this.prevStaticHeight = Math.max(e, this.prevStaticHeight), this.gallery.style.height = `${this.prevStaticHeight}px`;
	}
	setFinal(e) {
		this.prevStaticHeight = e, this.gallery.style.height = `${e}px`;
	}
}, b = (e, t, n, r) => {
	let i = Math.max(e, t);
	for (let e of r) if (i <= e) return n.sizeRangeSuffixes[e];
	let a = r[r.length - 1];
	return n.sizeRangeSuffixes[a];
}, x = (e, t) => t.length > 0 && e.endsWith(t) ? e.slice(0, -t.length) : e, S = (e, t) => {
	for (let n of Object.keys(t.sizeRangeSuffixes)) {
		let r = t.sizeRangeSuffixes[parseInt(n)];
		if (r.length !== 0 && e.endsWith(r)) return r;
	}
	return "";
}, C = (e, t, n, r, i, a) => {
	let o;
	if (i.thumbnailPath) o = i.thumbnailPath(e, t, n, r);
	else {
		let r = e.match(i.extension), s = r ? r[0] : "";
		o = e.replace(i.extension, ""), o = x(o, S(o, i)), o += b(t, n, i, a) + s;
	}
	return o;
}, w = (e) => {
	let t = e.dataset.safeSrc ?? e.getAttribute("src") ?? "", n = e.dataset.safeSrc ? "data-safe-src" : "src";
	return e.dataset.jgOriginalSrc = t, e.dataset.jgSrc = t, e.dataset.jgOriginalSrcLoc = n, t;
}, T = (e) => {
	e.src = e.dataset.jgOriginalSrcLoc === "src" && e.dataset.jgOriginalSrc || "";
}, E = (e, t, n) => {
	if (!t && !n) return;
	let r = new Image(), i = () => {
		r.removeEventListener("load", i), r.removeEventListener("error", a), t?.(r);
	}, a = () => {
		r.removeEventListener("load", i), r.removeEventListener("error", a), n?.(r);
	};
	t && r.addEventListener("load", i, { once: !0 }), n && r.addEventListener("error", a, { once: !0 }), r.src = e;
};
//#endregion
//#region src/row-layout.ts
function D(e) {
	e.entriesBuff = [], e.aspectRatio = 0, e.width = 0;
}
function O(e, t, n, r) {
	let i = !0, a = 0, o = t.galleryWidth - 2 * t.border - (e.entriesBuff.length - 1) * t.margins, s = o / e.aspectRatio, c = t.rowHeight, l = e.width / o > t.justifyThreshold;
	return r || n && t.lastRow === "hide" && !l ? (e.entriesBuff.forEach((e) => {
		e.classList.remove("jg-entry-visible");
	}), -1) : (n && !l && t.lastRow !== "justify" && t.lastRow !== "hide" && (i = !1, t.rows > 0 && (c = (t.offY - t.border - t.margins * t.rows) / t.rows, i = c * e.aspectRatio / o > t.justifyThreshold)), e.entriesBuff.forEach((t, n) => {
		let r = parseFloat(t.dataset.jgWidth ?? "0") / parseFloat(t.dataset.jgHeight ?? "1"), l, u;
		i ? (l = n === e.entriesBuff.length - 1 ? o : s * r, u = s) : (l = c * r, u = c), o -= Math.round(l), t.dataset.jgJwidth = Math.round(l).toString(), t.dataset.jgJheight = Math.ceil(u).toString(), (n === 0 || a > u) && (a = u);
	}), e.height = a, i);
}
//#endregion
//#region src/spinner.ts
var k = class {
	constructor() {
		this.phase = 0, this.timeSlot = 150, this.element = e();
	}
	get isRunning() {
		return this.intervalId !== void 0;
	}
	start(e, t) {
		let n = Array.from(this.element.querySelectorAll("span"));
		this.intervalId &&= (clearInterval(this.intervalId), void 0), e.appendChild(this.element), t(this.element.offsetHeight), this.intervalId = window.setInterval(() => {
			this.phase < n.length ? n[this.phase].style.opacity = "1" : n[this.phase - n.length].style.opacity = "0", this.phase = (this.phase + 1) % (n.length * 2);
		}, this.timeSlot);
	}
	stop(e) {
		this.intervalId &&= (clearInterval(this.intervalId), void 0), e(this.element.offsetHeight), this.element.remove();
	}
}, A = class {
	constructor(e, t, n, r) {
		this.gallery = e, this.refreshTime = t, this.refreshSensitivity = n, this.onWidthChanged = r, this.width = e.offsetWidth;
	}
	start() {
		this.intervalId = window.setInterval(() => {
			if (!this.gallery.offsetParent) return;
			let e = this.gallery.clientWidth;
			Math.abs(e - this.width) > this.refreshSensitivity && (this.width = e, this.onWidthChanged(e));
		}, this.refreshTime);
	}
	stop() {
		clearInterval(this.intervalId), this.intervalId = void 0;
	}
}, j = class {
	imgFromEntry(e) {
		return l(e, this.settings.imgSelector);
	}
	displayEntry(e, t, n, r, i, a) {
		e.style.width = `${r}px`, e.style.height = `${a}px`, e.style.top = `${n}px`, e.style.left = `${t}px`;
		let o = this.imgFromEntry(e);
		if (o) {
			o.style.width = `${r}px`, o.style.height = `${i}px`, o.style.marginLeft = `${-r / 2}px`, o.style.marginTop = `${-i / 2}px`;
			let t = o.dataset.jgSrc;
			if (t) {
				let n = C(t, r, i, o, this.settings, this.suffixRanges);
				o.addEventListener("error", () => T(o), { once: !0 });
				let a = () => {
					o.setAttribute("src", n);
				};
				e.dataset.jgLoaded === "skipped" && n ? E(n, () => {
					f(e, a), e.dataset.jgLoaded = "true";
				}) : f(e, a);
			}
		} else f(e);
		p(e, this.settings.imgSelector, this.settings.captions);
	}
	flushRow(e, t) {
		let n = this.settings, r = O(this.buildingRow, {
			galleryWidth: this.galleryWidth,
			border: this.border,
			margins: n.margins,
			justifyThreshold: n.justifyThreshold,
			rowHeight: n.rowHeight,
			lastRow: n.lastRow,
			rows: this.rows,
			offY: this.offY
		}, e, t);
		if (t || e && n.lastRow === "hide" && r === -1) {
			D(this.buildingRow);
			return;
		}
		this.maxRowHeight && this.buildingRow.height > this.maxRowHeight && (this.buildingRow.height = this.maxRowHeight);
		let i = this.border;
		if (e && (n.lastRow === "center" || n.lastRow === "right")) {
			let e = this.galleryWidth - 2 * this.border - (this.buildingRow.entriesBuff.length - 1) * n.margins;
			for (let t of this.buildingRow.entriesBuff) e -= parseFloat(t.dataset.jgJwidth ?? "0");
			n.lastRow === "center" ? i += Math.round(e / 2) : n.lastRow === "right" && (i += e);
		}
		let a = this.buildingRow.entriesBuff.length - 1;
		for (let e = 0; e <= a; e++) {
			let t = this.buildingRow.entriesBuff[n.rtl ? a - e : e], r = parseFloat(t.dataset.jgJwidth ?? "0"), o = parseFloat(t.dataset.jgJheight ?? "0");
			this.displayEntry(t, i, this.offY, r, o, this.buildingRow.height), i += r + n.margins;
		}
		this.galleryHeightToSet = this.offY + this.buildingRow.height + this.border, this.height.setTemp(this.galleryHeightToSet + this.spinner.element.offsetHeight), (!e || this.buildingRow.height <= n.rowHeight && r) && (this.offY += this.buildingRow.height + n.margins, this.rows += 1, D(this.buildingRow), this.settings.triggerEvent.call(this, v.RowFlush));
	}
	stopLoadingSpinnerAnimation() {
		this.spinner.stop((e) => {
			this.height.setTemp(this.gallery.clientHeight - e);
		});
	}
	startLoadingSpinnerAnimation() {
		this.spinner.start(this.gallery, (e) => {
			this.height.setTemp(this.offY + this.buildingRow.height + e);
		});
	}
	rewind() {
		this.lastFetchedEntry = void 0, this.lastAnalyzedIndex = -1, this.offY = this.settings.border, this.rows = 0, D(this.buildingRow);
	}
	updateEntries(e) {
		let n;
		return e && this.lastFetchedEntry ? n = h(this.lastFetchedEntry, this.settings.selector) : (this.entries = [], n = m(this.gallery, this.settings.selector)), n.length > 0 && (typeof this.settings.sort == "function" ? n = n.sort(this.settings.sort) : this.settings.randomize && (n = t(n)), this.lastFetchedEntry = n[n.length - 1], this.settings.filter ? n = _(n, this.settings.filter) : g(n)), this.entries = this.entries.concat(n), !0;
	}
	destroy() {
		this.widthWatcher.stop(), this.stopImgAnalyzerStarter(), m(this.gallery, this.settings.selector).forEach((e) => {
			e.style.width = "", e.style.height = "", e.style.top = "", e.style.left = "", e.removeAttribute("data-jg-loaded"), e.classList.remove("jg-entry", "jg-filtered", "jg-entry-visible");
			let t = this.imgFromEntry(e);
			t && (t.style.width = "", t.style.height = "", t.style.marginLeft = "", t.style.marginTop = "", T(t), t.removeAttribute("data-jg-original-src"), t.removeAttribute("data-jg-original-srcloc"), t.removeAttribute("data-jg-src"));
			let n = e.querySelector(".jg-caption");
			n && e.dataset.jgCreatedCaption && (delete e.dataset.jgCreatedCaption, n.remove());
		}), this.gallery.style.height = "", this.gallery.classList.remove("justified-gallery"), this.gallery.removeAttribute("data-jg-controller"), this.settings.triggerEvent.call(this, v.Destroy);
	}
	analyzeImages(e) {
		for (let t = this.lastAnalyzedIndex + 1; t < this.entries.length; t++) {
			let n = this.entries[t], r = n.dataset.jgLoaded;
			if (r === "true" || r === "skipped") {
				let r = this.galleryWidth - 2 * this.border - (this.buildingRow.entriesBuff.length - 1) * this.settings.margins, i = parseFloat(n.dataset.jgWidth || "0") / parseFloat(n.dataset.jgHeight || "1");
				if (this.buildingRow.entriesBuff.push(n), this.buildingRow.aspectRatio += i, this.buildingRow.width += i * this.settings.rowHeight, this.lastAnalyzedIndex = t, r / (this.buildingRow.aspectRatio + i) < this.settings.rowHeight && (this.flushRow(!1, this.settings.maxRowsCount > 0 && this.rows === this.settings.maxRowsCount), ++this.yield.flushed >= this.yield.every)) {
					this.startImgAnalyzer(e);
					return;
				}
			} else if (r !== "error") return;
		}
		this.buildingRow.entriesBuff.length > 0 && this.flushRow(!0, this.settings.maxRowsCount > 0 && this.rows === this.settings.maxRowsCount), this.spinner.isRunning && this.stopLoadingSpinnerAnimation(), this.stopImgAnalyzerStarter(), this.height.setFinal(this.galleryHeightToSet), this.settings.triggerEvent.call(this, e ? v.Resize : v.Complete);
	}
	stopImgAnalyzerStarter() {
		this.yield.flushed = 0, this.imgAnalyzerTimeout &&= (clearTimeout(this.imgAnalyzerTimeout), void 0);
	}
	startImgAnalyzer(e) {
		this.stopImgAnalyzerStarter(), this.imgAnalyzerTimeout = window.setTimeout(() => {
			this.analyzeImages(e);
		}, 1);
	}
	init() {
		this.gallery.classList.add("justified-gallery");
		let e = !1, t = !1;
		this.updateEntries(!1), this.entries.forEach((n) => {
			let r = this.imgFromEntry(n);
			if (n.classList.add("jg-entry"), n.dataset.jgLoaded !== "true" && n.dataset.jgLoaded !== "skipped") {
				if (this.settings.rel !== null && n.setAttribute("rel", this.settings.rel), this.settings.target !== null && n.setAttribute("target", this.settings.target), r !== null) {
					let i = w(r);
					if (!this.settings.waitThumbnailsLoad || !i) {
						let e = parseFloat(r.getAttribute("width") || "NaN"), i = parseFloat(r.getAttribute("height") || "NaN");
						if (r.tagName === "svg" && r instanceof SVGGraphicsElement) {
							let t = r.getBBox();
							e = t.width, i = t.height;
						}
						if (!isNaN(e) && !isNaN(i)) {
							n.dataset.jgWidth = e.toString(), n.dataset.jgHeight = i.toString(), n.dataset.jgLoaded = "skipped", t = !0, this.startImgAnalyzer(!1);
							return;
						}
					}
					n.dataset.jgLoaded = "false", e = !0, this.spinner.isRunning || this.startLoadingSpinnerAnimation(), E(i, (e) => {
						n.dataset.jgWidth = e.width.toString(), n.dataset.jgHeight = e.height.toString(), n.dataset.jgLoaded = "true", this.startImgAnalyzer(!1);
					}, () => {
						n.dataset.jgLoaded = "error", this.startImgAnalyzer(!1);
					});
				} else n.dataset.jgLoaded = "true", n.dataset.jgWidth = (n.clientWidth || parseFloat(getComputedStyle(n).width) || 1).toString(), n.dataset.jgHeight = (n.clientHeight || parseFloat(getComputedStyle(n).height) || 1).toString();
			}
		}), !e && !t && this.startImgAnalyzer(!1), this.widthWatcher.start();
	}
	constructor(e, t) {
		this.imgAnalyzerTimeout = void 0, this.entries = [], this.lastFetchedEntry = void 0, this.buildingRow = {
			entriesBuff: [],
			aspectRatio: 0,
			width: 0,
			height: 0
		}, this.lastAnalyzedIndex = -1, this.yield = {
			every: 2,
			flushed: 0
		}, this.rows = 0, this.scrollBarOn = !1, this.galleryHeightToSet = 0, this.spinner = new k(), this.gallery = e, this.settings = {
			...c,
			...t
		}, o(this.settings), this.border = this.settings.border >= 0 ? this.settings.border : this.settings.margins, this.maxRowHeight = s(this.settings), this.suffixRanges = a(this.settings), this.offY = this.border, this.galleryWidth = e.offsetWidth, this.height = new y(e), this.widthWatcher = new A(e, this.settings.refreshTime, this.settings.refreshSensitivity, (e) => {
			this.galleryWidth = e, this.rewind(), this.height.remember(), this.startImgAnalyzer(!0);
		});
	}
};
//#endregion
export { j as JustifiedGallery };
