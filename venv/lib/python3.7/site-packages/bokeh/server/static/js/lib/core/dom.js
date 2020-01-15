"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const types_1 = require("./util/types");
const _createElement = (tag) => {
    return (attrs = {}, ...children) => {
        const element = document.createElement(tag);
        element.classList.add("bk");
        for (const attr in attrs) {
            let value = attrs[attr];
            if (value == null || types_1.isBoolean(value) && !value)
                continue;
            if (attr === "class") {
                if (types_1.isString(value))
                    value = value.split(/\s+/);
                if (types_1.isArray(value)) {
                    for (const cls of value) {
                        if (cls != null)
                            element.classList.add(cls);
                    }
                    continue;
                }
            }
            if (attr === "style" && types_1.isPlainObject(value)) {
                for (const prop in value) {
                    element.style[prop] = value[prop];
                }
                continue;
            }
            if (attr === "data" && types_1.isPlainObject(value)) {
                for (const key in value) {
                    element.dataset[key] = value[key]; // XXX: attrs needs a better type
                }
                continue;
            }
            element.setAttribute(attr, value);
        }
        function append(child) {
            if (child instanceof HTMLElement)
                element.appendChild(child);
            else if (types_1.isString(child))
                element.appendChild(document.createTextNode(child));
            else if (child != null && child !== false)
                throw new Error(`expected an HTMLElement, string, false or null, got ${JSON.stringify(child)}`);
        }
        for (const child of children) {
            if (types_1.isArray(child)) {
                for (const _child of child)
                    append(_child);
            }
            else
                append(child);
        }
        return element;
    };
};
function createElement(tag, attrs, ...children) {
    return _createElement(tag)(attrs, ...children);
}
exports.createElement = createElement;
exports.div = _createElement("div"), exports.span = _createElement("span"), exports.canvas = _createElement("canvas"), exports.link = _createElement("link"), exports.style = _createElement("style"), exports.a = _createElement("a"), exports.p = _createElement("p"), exports.i = _createElement("i"), exports.pre = _createElement("pre"), exports.button = _createElement("button"), exports.label = _createElement("label"), exports.input = _createElement("input"), exports.select = _createElement("select"), exports.option = _createElement("option"), exports.optgroup = _createElement("optgroup"), exports.textarea = _createElement("textarea");
function nbsp() {
    return document.createTextNode("\u00a0");
}
exports.nbsp = nbsp;
function removeElement(element) {
    const parent = element.parentNode;
    if (parent != null) {
        parent.removeChild(element);
    }
}
exports.removeElement = removeElement;
function replaceWith(element, replacement) {
    const parent = element.parentNode;
    if (parent != null) {
        parent.replaceChild(replacement, element);
    }
}
exports.replaceWith = replaceWith;
function prepend(element, ...nodes) {
    const first = element.firstChild;
    for (const node of nodes) {
        element.insertBefore(node, first);
    }
}
exports.prepend = prepend;
function empty(element) {
    let child;
    while (child = element.firstChild) {
        element.removeChild(child);
    }
}
exports.empty = empty;
function display(element) {
    element.style.display = "";
}
exports.display = display;
function undisplay(element) {
    element.style.display = "none";
}
exports.undisplay = undisplay;
function show(element) {
    element.style.visibility = "";
}
exports.show = show;
function hide(element) {
    element.style.visibility = "hidden";
}
exports.hide = hide;
function offset(element) {
    const rect = element.getBoundingClientRect();
    return {
        top: rect.top + window.pageYOffset - document.documentElement.clientTop,
        left: rect.left + window.pageXOffset - document.documentElement.clientLeft,
    };
}
exports.offset = offset;
function matches(el, selector) {
    const p = Element.prototype;
    const f = p.matches || p.webkitMatchesSelector || p.mozMatchesSelector || p.msMatchesSelector;
    return f.call(el, selector);
}
exports.matches = matches;
function parent(el, selector) {
    let node = el;
    while (node = node.parentElement) {
        if (matches(node, selector))
            return node;
    }
    return null;
}
exports.parent = parent;
function num(value) {
    return parseFloat(value) || 0;
}
function extents(el) {
    const style = getComputedStyle(el);
    return {
        border: {
            top: num(style.borderTopWidth),
            bottom: num(style.borderBottomWidth),
            left: num(style.borderLeftWidth),
            right: num(style.borderRightWidth),
        },
        margin: {
            top: num(style.marginTop),
            bottom: num(style.marginBottom),
            left: num(style.marginLeft),
            right: num(style.marginRight),
        },
        padding: {
            top: num(style.paddingTop),
            bottom: num(style.paddingBottom),
            left: num(style.paddingLeft),
            right: num(style.paddingRight),
        },
    };
}
exports.extents = extents;
function size(el) {
    const rect = el.getBoundingClientRect();
    return {
        width: Math.ceil(rect.width),
        height: Math.ceil(rect.height),
    };
}
exports.size = size;
function scroll_size(el) {
    return {
        width: Math.ceil(el.scrollWidth),
        height: Math.ceil(el.scrollHeight),
    };
}
exports.scroll_size = scroll_size;
function outer_size(el) {
    const { margin: { left, right, top, bottom } } = extents(el);
    const { width, height } = size(el);
    return {
        width: Math.ceil(width + left + right),
        height: Math.ceil(height + top + bottom),
    };
}
exports.outer_size = outer_size;
function content_size(el) {
    const { left, top } = el.getBoundingClientRect();
    const { padding } = extents(el);
    let width = 0;
    let height = 0;
    for (const child of children(el)) {
        const rect = child.getBoundingClientRect();
        width = Math.max(width, Math.ceil(rect.left - left - padding.left + rect.width));
        height = Math.max(height, Math.ceil(rect.top - top - padding.top + rect.height));
    }
    return { width, height };
}
exports.content_size = content_size;
function position(el, box, margin) {
    const { style } = el;
    style.left = `${box.x}px`;
    style.top = `${box.y}px`;
    style.width = `${box.width}px`;
    style.height = `${box.height}px`;
    if (margin == null)
        style.margin = "";
    else {
        const { top, right, bottom, left } = margin;
        style.margin = `${top}px ${right}px ${bottom}px ${left}px`;
    }
}
exports.position = position;
function children(el) {
    return Array.from(el.children);
}
exports.children = children;
class ClassList {
    constructor(el) {
        this.el = el;
        this.classList = el.classList;
    }
    get values() {
        const values = [];
        for (let i = 0; i < this.classList.length; i++) {
            const item = this.classList.item(i);
            if (item != null)
                values.push(item);
        }
        return values;
    }
    has(cls) {
        return this.classList.contains(cls);
    }
    add(...classes) {
        for (const cls of classes)
            this.classList.add(cls);
        return this;
    }
    remove(...classes) {
        for (const cls of classes)
            this.classList.remove(cls);
        return this;
    }
    clear() {
        for (const cls of this.values) {
            if (cls != "bk")
                this.classList.remove(cls);
        }
        return this;
    }
    toggle(cls, activate) {
        const add = activate != null ? activate : !this.has(cls);
        if (add)
            this.add(cls);
        else
            this.remove(cls);
        return this;
    }
}
exports.ClassList = ClassList;
ClassList.__name__ = "ClassList";
function classes(el) {
    return new ClassList(el);
}
exports.classes = classes;
var Keys;
(function (Keys) {
    Keys[Keys["Backspace"] = 8] = "Backspace";
    Keys[Keys["Tab"] = 9] = "Tab";
    Keys[Keys["Enter"] = 13] = "Enter";
    Keys[Keys["Esc"] = 27] = "Esc";
    Keys[Keys["PageUp"] = 33] = "PageUp";
    Keys[Keys["PageDown"] = 34] = "PageDown";
    Keys[Keys["Left"] = 37] = "Left";
    Keys[Keys["Up"] = 38] = "Up";
    Keys[Keys["Right"] = 39] = "Right";
    Keys[Keys["Down"] = 40] = "Down";
    Keys[Keys["Delete"] = 46] = "Delete";
})(Keys = exports.Keys || (exports.Keys = {}));
function undisplayed(el, fn) {
    const { display } = el.style;
    el.style.display = "none";
    try {
        return fn();
    }
    finally {
        el.style.display = display;
    }
}
exports.undisplayed = undisplayed;
function unsized(el, fn) {
    return sized(el, {}, fn);
}
exports.unsized = unsized;
function sized(el, size, fn) {
    const { width, height, position, display } = el.style;
    el.style.position = "absolute";
    el.style.display = "";
    el.style.width = size.width != null && size.width != Infinity ? `${size.width}px` : "auto";
    el.style.height = size.height != null && size.height != Infinity ? `${size.height}px` : "auto";
    try {
        return fn();
    }
    finally {
        el.style.position = position;
        el.style.display = display;
        el.style.width = width;
        el.style.height = height;
    }
}
exports.sized = sized;
class StyleSheet {
    constructor() {
        this.style = exports.style({ type: "text/css" });
        prepend(document.head, this.style);
    }
    append(css) {
        this.style.appendChild(document.createTextNode(css));
    }
}
exports.StyleSheet = StyleSheet;
StyleSheet.__name__ = "StyleSheet";
exports.styles = new StyleSheet();
