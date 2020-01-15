"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const numbro = require("numbro");
const abstract_slider_1 = require("./abstract_slider");
class SliderView extends abstract_slider_1.AbstractSliderView {
}
exports.SliderView = SliderView;
SliderView.__name__ = "SliderView";
class Slider extends abstract_slider_1.AbstractSlider {
    constructor(attrs) {
        super(attrs);
        this.behaviour = "tap";
        this.connected = [true, false];
    }
    static init_Slider() {
        this.prototype.default_view = SliderView;
        this.override({
            format: "0[.]00",
        });
    }
    _formatter(value, format) {
        return numbro.format(value, format);
    }
}
exports.Slider = Slider;
Slider.__name__ = "Slider";
Slider.init_Slider();
