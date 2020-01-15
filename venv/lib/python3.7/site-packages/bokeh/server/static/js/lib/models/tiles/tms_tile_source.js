"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const mercator_tile_source_1 = require("./mercator_tile_source");
class TMSTileSource extends mercator_tile_source_1.MercatorTileSource {
    constructor(attrs) {
        super(attrs);
    }
    get_image_url(x, y, z) {
        const image_url = this.string_lookup_replace(this.url, this.extra_url_vars);
        return image_url
            .replace("{X}", x.toString())
            .replace('{Y}', y.toString())
            .replace("{Z}", z.toString());
    }
}
exports.TMSTileSource = TMSTileSource;
TMSTileSource.__name__ = "TMSTileSource";
