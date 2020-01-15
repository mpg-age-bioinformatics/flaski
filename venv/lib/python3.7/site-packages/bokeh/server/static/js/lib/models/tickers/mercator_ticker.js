"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const basic_ticker_1 = require("./basic_ticker");
const p = require("../../core/properties");
const projections_1 = require("../../core/util/projections");
class MercatorTicker extends basic_ticker_1.BasicTicker {
    constructor(attrs) {
        super(attrs);
    }
    static init_MercatorTicker() {
        this.define({
            dimension: [p.LatLon],
        });
    }
    get_ticks_no_defaults(data_low, data_high, cross_loc, desired_n_ticks) {
        if (this.dimension == null) {
            throw new Error("MercatorTicker.dimension not configured");
        }
        [data_low, data_high] = projections_1.clip_mercator(data_low, data_high, this.dimension);
        let proj_low, proj_high, proj_cross_loc;
        if (this.dimension === "lon") {
            [proj_low, proj_cross_loc] = projections_1.wgs84_mercator.inverse([data_low, cross_loc]);
            [proj_high, proj_cross_loc] = projections_1.wgs84_mercator.inverse([data_high, cross_loc]);
        }
        else {
            [proj_cross_loc, proj_low] = projections_1.wgs84_mercator.inverse([cross_loc, data_low]);
            [proj_cross_loc, proj_high] = projections_1.wgs84_mercator.inverse([cross_loc, data_high]);
        }
        const proj_ticks = super.get_ticks_no_defaults(proj_low, proj_high, cross_loc, desired_n_ticks);
        const major = [];
        const minor = [];
        if (this.dimension === "lon") {
            for (const tick of proj_ticks.major) {
                if (projections_1.in_bounds(tick, 'lon')) {
                    const [lon] = projections_1.wgs84_mercator.forward([tick, proj_cross_loc]);
                    major.push(lon);
                }
            }
            for (const tick of proj_ticks.minor) {
                if (projections_1.in_bounds(tick, 'lon')) {
                    const [lon] = projections_1.wgs84_mercator.forward([tick, proj_cross_loc]);
                    minor.push(lon);
                }
            }
        }
        else {
            for (const tick of proj_ticks.major) {
                if (projections_1.in_bounds(tick, 'lat')) {
                    const [, lat] = projections_1.wgs84_mercator.forward([proj_cross_loc, tick]);
                    major.push(lat);
                }
            }
            for (const tick of proj_ticks.minor) {
                if (projections_1.in_bounds(tick, 'lat')) {
                    const [, lat] = projections_1.wgs84_mercator.forward([proj_cross_loc, tick]);
                    minor.push(lat);
                }
            }
        }
        return { major, minor };
    }
}
exports.MercatorTicker = MercatorTicker;
MercatorTicker.__name__ = "MercatorTicker";
MercatorTicker.init_MercatorTicker();
