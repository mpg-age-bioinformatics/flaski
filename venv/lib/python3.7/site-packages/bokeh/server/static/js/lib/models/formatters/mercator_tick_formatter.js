"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const basic_tick_formatter_1 = require("./basic_tick_formatter");
const p = require("../../core/properties");
const projections_1 = require("../../core/util/projections");
class MercatorTickFormatter extends basic_tick_formatter_1.BasicTickFormatter {
    constructor(attrs) {
        super(attrs);
    }
    static init_MercatorTickFormatter() {
        this.define({
            dimension: [p.LatLon],
        });
    }
    doFormat(ticks, opts) {
        if (this.dimension == null)
            throw new Error("MercatorTickFormatter.dimension not configured");
        if (ticks.length == 0)
            return [];
        const n = ticks.length;
        const proj_ticks = new Array(n);
        if (this.dimension == "lon") {
            for (let i = 0; i < n; i++) {
                const [lon] = projections_1.wgs84_mercator.inverse([ticks[i], opts.loc]);
                proj_ticks[i] = lon;
            }
        }
        else {
            for (let i = 0; i < n; i++) {
                const [, lat] = projections_1.wgs84_mercator.inverse([opts.loc, ticks[i]]);
                proj_ticks[i] = lat;
            }
        }
        return super.doFormat(proj_ticks, opts);
    }
}
exports.MercatorTickFormatter = MercatorTickFormatter;
MercatorTickFormatter.__name__ = "MercatorTickFormatter";
MercatorTickFormatter.init_MercatorTickFormatter();
