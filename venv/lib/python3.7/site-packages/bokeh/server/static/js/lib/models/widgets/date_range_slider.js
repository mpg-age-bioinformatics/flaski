"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tz = require("timezone");
const abstract_slider_1 = require("./abstract_slider");
class DateRangeSliderView extends abstract_slider_1.AbstractRangeSliderView {
}
exports.DateRangeSliderView = DateRangeSliderView;
DateRangeSliderView.__name__ = "DateRangeSliderView";
class DateRangeSlider extends abstract_slider_1.AbstractSlider {
    constructor(attrs) {
        super(attrs);
        this.behaviour = "drag";
        this.connected = [false, true, false];
    }
    static init_DateRangeSlider() {
        this.prototype.default_view = DateRangeSliderView;
        this.override({
            format: "%d %b %Y",
        });
    }
    _formatter(value, format) {
        return tz(value, format);
    }
}
exports.DateRangeSlider = DateRangeSlider;
DateRangeSlider.__name__ = "DateRangeSlider";
DateRangeSlider.init_DateRangeSlider();
