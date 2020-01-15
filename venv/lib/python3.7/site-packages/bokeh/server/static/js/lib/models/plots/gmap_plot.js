"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const logging_1 = require("../../core/logging");
const plot_1 = require("./plot");
const p = require("../../core/properties");
const model_1 = require("../../model");
const range1d_1 = require("../ranges/range1d");
const gmap_plot_canvas_1 = require("./gmap_plot_canvas");
exports.GMapPlotView = gmap_plot_canvas_1.GMapPlotView;
class MapOptions extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_MapOptions() {
        this.define({
            lat: [p.Number],
            lng: [p.Number],
            zoom: [p.Number, 12],
        });
    }
}
exports.MapOptions = MapOptions;
MapOptions.__name__ = "MapOptions";
MapOptions.init_MapOptions();
class GMapOptions extends MapOptions {
    constructor(attrs) {
        super(attrs);
    }
    static init_GMapOptions() {
        this.define({
            map_type: [p.String, "roadmap"],
            scale_control: [p.Boolean, false],
            styles: [p.String],
            tilt: [p.Int, 45],
        });
    }
}
exports.GMapOptions = GMapOptions;
GMapOptions.__name__ = "GMapOptions";
GMapOptions.init_GMapOptions();
class GMapPlot extends plot_1.Plot {
    constructor(attrs) {
        super(attrs);
    }
    static init_GMapPlot() {
        this.prototype.default_view = gmap_plot_canvas_1.GMapPlotView;
        // This seems to be necessary so that everything can initialize.
        // Feels very clumsy, but I'm not sure how the properties system wants
        // to handle something like this situation.
        this.define({
            map_options: [p.Instance],
            api_key: [p.String],
        });
        this.override({
            x_range: () => new range1d_1.Range1d(),
            y_range: () => new range1d_1.Range1d(),
        });
    }
    initialize() {
        super.initialize();
        this.use_map = true;
        if (!this.api_key)
            logging_1.logger.error("api_key is required. See https://developers.google.com/maps/documentation/javascript/get-api-key for more information on how to obtain your own.");
    }
}
exports.GMapPlot = GMapPlot;
GMapPlot.__name__ = "GMapPlot";
GMapPlot.init_GMapPlot();
