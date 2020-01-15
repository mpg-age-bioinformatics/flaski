"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const numbro = require("numbro");
const abstract_slider_1 = require("./abstract_slider");
class RangeSliderView extends abstract_slider_1.AbstractRangeSliderView {
}
exports.RangeSliderView = RangeSliderView;
RangeSliderView.__name__ = "RangeSliderView";
class RangeSlider extends abstract_slider_1.AbstractSlider {
    constructor(attrs) {
        super(attrs);
        this.behaviour = "drag";
        this.connected = [false, true, false];
    }
    static init_RangeSlider() {
        this.prototype.default_view = RangeSliderView;
        this.override({
            format: "0[.]00",
        });
    }
    _formatter(value, format) {
        return numbro.format(value, format);
    }
}
exports.RangeSlider = RangeSlider;
RangeSlider.__name__ = "RangeSlider";
RangeSlider.init_RangeSlider();
