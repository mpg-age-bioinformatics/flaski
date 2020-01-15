"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const layout_1 = require("../../core/layout");
const dom_1 = require("../../core/dom");
const array_1 = require("../../core/util/array");
const p = require("../../core/properties");
const layout_dom_1 = require("./layout_dom");
const model_1 = require("../../model");
const mixins_1 = require("../../styles/mixins");
const tabs_1 = require("../../styles/tabs");
const buttons_1 = require("../../styles/buttons");
const menus_1 = require("../../styles/menus");
class TabsView extends layout_dom_1.LayoutDOMView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.tabs.change, () => this.rebuild());
        this.connect(this.model.properties.active.change, () => this.on_active_change());
    }
    get child_models() {
        return this.model.tabs.map((tab) => tab.child);
    }
    _update_layout() {
        const loc = this.model.tabs_location;
        const vertical = loc == "above" || loc == "below";
        // XXX: this is a hack, this should be handled by "fit" policy in grid layout
        const { scroll_el, headers_el } = this;
        this.header = new class extends layout_1.ContentBox {
            _measure(viewport) {
                const min_headers = 3;
                const scroll = dom_1.size(scroll_el);
                const headers = dom_1.children(headers_el).slice(0, min_headers).map((el) => dom_1.size(el));
                const { width, height } = super._measure(viewport);
                if (vertical) {
                    const min_width = scroll.width + array_1.sum(headers.map((size) => size.width));
                    return { width: viewport.width != Infinity ? viewport.width : min_width, height };
                }
                else {
                    const min_height = scroll.height + array_1.sum(headers.map((size) => size.height));
                    return { width, height: viewport.height != Infinity ? viewport.height : min_height };
                }
            }
        }(this.header_el);
        if (vertical)
            this.header.set_sizing({ width_policy: "fit", height_policy: "fixed" });
        else
            this.header.set_sizing({ width_policy: "fixed", height_policy: "fit" });
        let row = 1;
        let col = 1;
        switch (loc) {
            case "above":
                row -= 1;
                break;
            case "below":
                row += 1;
                break;
            case "left":
                col -= 1;
                break;
            case "right":
                col += 1;
                break;
        }
        const header = { layout: this.header, row, col };
        const panels = this.child_views.map((child_view) => {
            return { layout: child_view.layout, row: 1, col: 1 };
        });
        this.layout = new layout_1.Grid([header, ...panels]);
        this.layout.set_sizing(this.box_sizing());
    }
    update_position() {
        super.update_position();
        this.header_el.style.position = "absolute"; // XXX: do it in position()
        dom_1.position(this.header_el, this.header.bbox);
        const loc = this.model.tabs_location;
        const vertical = loc == "above" || loc == "below";
        const scroll_el_size = dom_1.size(this.scroll_el);
        const headers_el_size = dom_1.scroll_size(this.headers_el);
        if (vertical) {
            const { width } = this.header.bbox;
            if (headers_el_size.width > width) {
                this.wrapper_el.style.maxWidth = `${width - scroll_el_size.width}px`;
                dom_1.display(this.scroll_el);
            }
            else {
                this.wrapper_el.style.maxWidth = "";
                dom_1.undisplay(this.scroll_el);
            }
        }
        else {
            const { height } = this.header.bbox;
            if (headers_el_size.height > height) {
                this.wrapper_el.style.maxHeight = `${height - scroll_el_size.height}px`;
                dom_1.display(this.scroll_el);
            }
            else {
                this.wrapper_el.style.maxHeight = "";
                dom_1.undisplay(this.scroll_el);
            }
        }
        const { child_views } = this;
        for (const child_view of child_views)
            dom_1.hide(child_view.el);
        const tab = child_views[this.model.active];
        if (tab != null)
            dom_1.show(tab.el);
    }
    render() {
        super.render();
        const { active } = this.model;
        const loc = this.model.tabs_location;
        const vertical = loc == "above" || loc == "below";
        const headers = this.model.tabs.map((tab, i) => {
            const el = dom_1.div({ class: [tabs_1.bk_tab, i == active ? mixins_1.bk_active : null] }, tab.title);
            el.addEventListener("click", (event) => {
                if (event.target == event.currentTarget)
                    this.change_active(i);
            });
            if (tab.closable) {
                const close_el = dom_1.div({ class: tabs_1.bk_close });
                close_el.addEventListener("click", (event) => {
                    if (event.target == event.currentTarget) {
                        this.model.tabs = array_1.remove_at(this.model.tabs, i);
                        const ntabs = this.model.tabs.length;
                        if (this.model.active > ntabs - 1)
                            this.model.active = ntabs - 1;
                    }
                });
                el.appendChild(close_el);
            }
            return el;
        });
        this.headers_el = dom_1.div({ class: [tabs_1.bk_headers] }, headers);
        this.wrapper_el = dom_1.div({ class: tabs_1.bk_headers_wrapper }, this.headers_el);
        const left_el = dom_1.div({ class: [buttons_1.bk_btn, buttons_1.bk_btn_default], disabled: "" }, dom_1.div({ class: [menus_1.bk_caret, mixins_1.bk_left] }));
        const right_el = dom_1.div({ class: [buttons_1.bk_btn, buttons_1.bk_btn_default] }, dom_1.div({ class: [menus_1.bk_caret, mixins_1.bk_right] }));
        let scroll_index = 0;
        const do_scroll = (dir) => {
            return () => {
                const ntabs = this.model.tabs.length;
                if (dir == "left")
                    scroll_index = Math.max(scroll_index - 1, 0);
                else
                    scroll_index = Math.min(scroll_index + 1, ntabs - 1);
                if (scroll_index == 0)
                    left_el.setAttribute("disabled", "");
                else
                    left_el.removeAttribute("disabled");
                if (scroll_index == ntabs - 1)
                    right_el.setAttribute("disabled", "");
                else
                    right_el.removeAttribute("disabled");
                const sizes = dom_1.children(this.headers_el)
                    .slice(0, scroll_index)
                    .map((el) => el.getBoundingClientRect());
                if (vertical) {
                    const left = -array_1.sum(sizes.map((size) => size.width));
                    this.headers_el.style.left = `${left}px`;
                }
                else {
                    const top = -array_1.sum(sizes.map((size) => size.height));
                    this.headers_el.style.top = `${top}px`;
                }
            };
        };
        left_el.addEventListener("click", do_scroll("left"));
        right_el.addEventListener("click", do_scroll("right"));
        this.scroll_el = dom_1.div({ class: buttons_1.bk_btn_group }, left_el, right_el);
        this.header_el = dom_1.div({ class: [tabs_1.bk_tabs_header, mixins_1.bk_side(loc)] }, this.scroll_el, this.wrapper_el);
        this.el.appendChild(this.header_el);
    }
    change_active(i) {
        if (i != this.model.active) {
            this.model.active = i;
            if (this.model.callback != null)
                this.model.callback.execute(this.model);
        }
    }
    on_active_change() {
        const i = this.model.active;
        const headers = dom_1.children(this.headers_el);
        for (const el of headers)
            el.classList.remove(mixins_1.bk_active);
        headers[i].classList.add(mixins_1.bk_active);
        const { child_views } = this;
        for (const child_view of child_views)
            dom_1.hide(child_view.el);
        dom_1.show(child_views[i].el);
    }
}
exports.TabsView = TabsView;
TabsView.__name__ = "TabsView";
class Tabs extends layout_dom_1.LayoutDOM {
    constructor(attrs) {
        super(attrs);
    }
    static init_Tabs() {
        this.prototype.default_view = TabsView;
        this.define({
            tabs: [p.Array, []],
            tabs_location: [p.Location, "above"],
            active: [p.Number, 0],
            callback: [p.Any],
        });
    }
}
exports.Tabs = Tabs;
Tabs.__name__ = "Tabs";
Tabs.init_Tabs();
class Panel extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_Panel() {
        this.define({
            title: [p.String, ""],
            child: [p.Instance],
            closable: [p.Boolean, false],
        });
    }
}
exports.Panel = Panel;
Panel.__name__ = "Panel";
Panel.init_Panel();
