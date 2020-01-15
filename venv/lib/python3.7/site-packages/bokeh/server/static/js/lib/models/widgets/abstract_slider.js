"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const noUiSlider = require("nouislider");
const p = require("../../core/properties");
const dom_1 = require("../../core/dom");
const array_1 = require("../../core/util/array");
const callback_1 = require("../../core/util/callback");
const control_1 = require("./control");
const sliders_1 = require("../../styles/widgets/sliders");
const prefix = 'bk-noUi-';
class AbstractBaseSliderView extends control_1.ControlView {
    get noUiSlider() {
        return this.slider_el.noUiSlider;
    }
    initialize() {
        super.initialize();
        this._init_callback();
    }
    connect_signals() {
        super.connect_signals();
        const { callback, callback_policy, callback_throttle } = this.model.properties;
        this.on_change([callback, callback_policy, callback_throttle], () => this._init_callback());
        const { start, end, value, step, title } = this.model.properties;
        this.on_change([start, end, value, step], () => {
            const { start, end, value, step } = this._calc_to();
            this.noUiSlider.updateOptions({
                range: { min: start, max: end },
                start: value,
                step,
            });
        });
        const { bar_color } = this.model.properties;
        this.on_change(bar_color, () => {
            this._set_bar_color();
        });
        this.on_change([value, title], () => this._update_title());
    }
    _init_callback() {
        const { callback } = this.model;
        const fn = () => {
            if (callback != null)
                callback.execute(this.model);
            this.model.value_throttled = this.model.value;
        };
        switch (this.model.callback_policy) {
            case 'continuous': {
                this.callback_wrapper = fn;
                break;
            }
            case 'throttle': {
                this.callback_wrapper = callback_1.throttle(fn, this.model.callback_throttle);
                break;
            }
            default:
                this.callback_wrapper = undefined;
        }
    }
    _update_title() {
        dom_1.empty(this.title_el);
        const hide_header = this.model.title == null || (this.model.title.length == 0 && !this.model.show_value);
        this.title_el.style.display = hide_header ? "none" : "";
        if (!hide_header) {
            if (this.model.title.length != 0)
                this.title_el.textContent = `${this.model.title}: `;
            if (this.model.show_value) {
                const { value } = this._calc_to();
                const pretty = value.map((v) => this.model.pretty(v)).join(" .. ");
                this.title_el.appendChild(dom_1.span({ class: sliders_1.bk_slider_value }, pretty));
            }
        }
    }
    _set_bar_color() {
        if (!this.model.disabled) {
            const connect_el = this.slider_el.querySelector(`.${prefix}connect`);
            connect_el.style.backgroundColor = this.model.bar_color;
        }
    }
    _keypress_handle(e, idx = 0) {
        const { start, value, end, step } = this._calc_to();
        const is_range = value.length == 2;
        let low = start;
        let high = end;
        if (is_range && idx == 0) {
            high = value[1];
        }
        else if (is_range && idx == 1) {
            low = value[0];
        }
        switch (e.which) {
            case 37: {
                value[idx] = Math.max(value[idx] - step, low);
                break;
            }
            case 39: {
                value[idx] = Math.min(value[idx] + step, high);
                break;
            }
            default:
                return;
        }
        if (is_range) {
            this.model.value = value;
            this.model.properties.value.change.emit();
        }
        else {
            this.model.value = value[0];
        }
        this.noUiSlider.set(value);
        if (this.callback_wrapper != null)
            this.callback_wrapper();
    }
    render() {
        super.render();
        const { start, end, value, step } = this._calc_to();
        let tooltips; // XXX
        if (this.model.tooltips) {
            const formatter = {
                to: (value) => this.model.pretty(value),
            };
            tooltips = array_1.repeat(formatter, value.length);
        }
        else
            tooltips = false;
        if (this.slider_el == null) {
            this.slider_el = dom_1.div();
            noUiSlider.create(this.slider_el, {
                cssPrefix: prefix,
                range: { min: start, max: end },
                start: value,
                step,
                behaviour: this.model.behaviour,
                connect: this.model.connected,
                tooltips,
                orientation: this.model.orientation,
                direction: this.model.direction,
            }); // XXX: bad typings; no cssPrefix
            this.noUiSlider.on('slide', (_, __, values) => this._slide(values));
            this.noUiSlider.on('change', (_, __, values) => this._change(values));
            this._set_keypress_handles();
            const toggleTooltip = (i, show) => {
                if (!tooltips)
                    return;
                const handle = this.slider_el.querySelectorAll(`.${prefix}handle`)[i];
                const tooltip = handle.querySelector(`.${prefix}tooltip`);
                tooltip.style.display = show ? 'block' : '';
            };
            this.noUiSlider.on('start', (_, i) => toggleTooltip(i, true));
            this.noUiSlider.on('end', (_, i) => toggleTooltip(i, false));
        }
        else {
            this.noUiSlider.updateOptions({
                range: { min: start, max: end },
                start: value,
                step,
            });
        }
        this._set_bar_color();
        if (this.model.disabled)
            this.slider_el.setAttribute('disabled', 'true');
        else
            this.slider_el.removeAttribute('disabled');
        this.title_el = dom_1.div({ class: sliders_1.bk_slider_title });
        this._update_title();
        this.group_el = dom_1.div({ class: sliders_1.bk_input_group }, this.title_el, this.slider_el);
        this.el.appendChild(this.group_el);
    }
    _slide(values) {
        this.model.value = this._calc_from(values);
        if (this.callback_wrapper != null)
            this.callback_wrapper();
    }
    _change(values) {
        this.model.value = this._calc_from(values);
        this.model.value_throttled = this.model.value;
        switch (this.model.callback_policy) {
            case 'mouseup':
            case 'throttle': {
                if (this.model.callback != null)
                    this.model.callback.execute(this.model);
                break;
            }
        }
    }
}
AbstractBaseSliderView.__name__ = "AbstractBaseSliderView";
class AbstractSliderView extends AbstractBaseSliderView {
    _calc_to() {
        return {
            start: this.model.start,
            end: this.model.end,
            value: [this.model.value],
            step: this.model.step,
        };
    }
    _calc_from([value]) {
        if (Number.isInteger(this.model.start) && Number.isInteger(this.model.end) && Number.isInteger(this.model.step))
            return Math.round(value);
        else
            return value;
    }
    _set_keypress_handles() {
        // Add single cursor event
        const handle = this.slider_el.querySelector(`.${prefix}handle`);
        handle.setAttribute('tabindex', '0');
        handle.addEventListener('keydown', (e) => this._keypress_handle(e));
    }
}
exports.AbstractSliderView = AbstractSliderView;
AbstractSliderView.__name__ = "AbstractSliderView";
class AbstractRangeSliderView extends AbstractBaseSliderView {
    _calc_to() {
        return {
            start: this.model.start,
            end: this.model.end,
            value: this.model.value,
            step: this.model.step,
        };
    }
    _calc_from(values) {
        return values;
    }
    _set_keypress_handles() {
        const handle_lower = this.slider_el.querySelector(`.${prefix}handle-lower`);
        const handle_upper = this.slider_el.querySelector(`.${prefix}handle-upper`);
        handle_lower.setAttribute('tabindex', '0');
        handle_lower.addEventListener('keydown', (e) => this._keypress_handle(e, 0));
        handle_upper.setAttribute('tabindex', '1');
        handle_upper.addEventListener('keydown', (e) => this._keypress_handle(e, 1));
    }
}
exports.AbstractRangeSliderView = AbstractRangeSliderView;
AbstractRangeSliderView.__name__ = "AbstractRangeSliderView";
class AbstractSlider extends control_1.Control {
    constructor(attrs) {
        super(attrs);
        this.connected = false;
    }
    static init_AbstractSlider() {
        this.define({
            title: [p.String, ""],
            show_value: [p.Boolean, true],
            start: [p.Any],
            end: [p.Any],
            value: [p.Any],
            value_throttled: [p.Any],
            step: [p.Number, 1],
            format: [p.String],
            direction: [p.Any, "ltr"],
            tooltips: [p.Boolean, true],
            callback: [p.Any],
            callback_throttle: [p.Number, 200],
            callback_policy: [p.SliderCallbackPolicy, "throttle"],
            bar_color: [p.Color, "#e6e6e6"],
        });
    }
    _formatter(value, _format) {
        return `${value}`;
    }
    pretty(value) {
        return this._formatter(value, this.format);
    }
}
exports.AbstractSlider = AbstractSlider;
AbstractSlider.__name__ = "AbstractSlider";
AbstractSlider.init_AbstractSlider();
