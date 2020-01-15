"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tz = require("timezone");
const abstract_slider_1 = require("./abstract_slider");
class DateSliderView extends abstract_slider_1.AbstractSliderView {
}
exports.DateSliderView = DateSliderView;
DateSliderView.__name__ = "DateSliderView";
class DateSlider extends abstract_slider_1.AbstractSlider {
    constructor(attrs) {
        super(attrs);
        this.behaviour = "tap";
        this.connected = [true, false];
    }
    static init_DateSlider() {
        this.prototype.default_view = DateSliderView;
        this.override({
            format: "%d %b %Y",
        });
    }
    _formatter(value, format) {
        return tz(value, format);
    }
}
exports.DateSlider = DateSlider;
DateSlider.__name__ = "DateSlider";
DateSlider.init_DateSlider();
