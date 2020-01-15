"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const dom_1 = require("../dom");
const cache = {};
function measure_font(font) {
    if (cache[font] != null)
        return cache[font];
    const text = dom_1.span({ style: { font } }, "Hg");
    const block = dom_1.div({ style: { display: "inline-block", width: "1px", height: "0px" } });
    const elem = dom_1.div({}, text, block);
    document.body.appendChild(elem);
    try {
        block.style.verticalAlign = "baseline";
        const ascent = dom_1.offset(block).top - dom_1.offset(text).top;
        block.style.verticalAlign = "bottom";
        const height = dom_1.offset(block).top - dom_1.offset(text).top;
        const result = { height, ascent, descent: height - ascent };
        cache[font] = result;
        return result;
    }
    finally {
        document.body.removeChild(elem);
    }
}
exports.measure_font = measure_font;
const _cache = {};
function measure_text(text, font) {
    const text_cache = _cache[font];
    if (text_cache != null) {
        const size = text_cache[text];
        if (size != null)
            return size;
    }
    else
        _cache[font] = {};
    const el = dom_1.div({ style: { display: "inline-block", "white-space": "nowrap", font } }, text);
    document.body.appendChild(el);
    try {
        const { width, height } = el.getBoundingClientRect();
        _cache[font][text] = { width, height };
        return { width, height };
    }
    finally {
        document.body.removeChild(el);
    }
}
exports.measure_text = measure_text;
