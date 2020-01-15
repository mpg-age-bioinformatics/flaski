"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const mercator_tile_source_1 = require("./mercator_tile_source");
const p = require("../../core/properties");
class BBoxTileSource extends mercator_tile_source_1.MercatorTileSource {
    constructor(attrs) {
        super(attrs);
    }
    static init_BBoxTileSource() {
        this.define({
            use_latlon: [p.Boolean, false],
        });
    }
    get_image_url(x, y, z) {
        const image_url = this.string_lookup_replace(this.url, this.extra_url_vars);
        let xmax, xmin, ymax, ymin;
        if (this.use_latlon)
            [xmin, ymin, xmax, ymax] = this.get_tile_geographic_bounds(x, y, z);
        else
            [xmin, ymin, xmax, ymax] = this.get_tile_meter_bounds(x, y, z);
        return image_url
            .replace("{XMIN}", xmin.toString())
            .replace("{YMIN}", ymin.toString())
            .replace("{XMAX}", xmax.toString())
            .replace("{YMAX}", ymax.toString());
    }
}
exports.BBoxTileSource = BBoxTileSource;
BBoxTileSource.__name__ = "BBoxTileSource";
BBoxTileSource.init_BBoxTileSource();
