"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const mercator_tile_source_1 = require("./mercator_tile_source");
class QUADKEYTileSource extends mercator_tile_source_1.MercatorTileSource {
    constructor(attrs) {
        super(attrs);
    }
    get_image_url(x, y, z) {
        const image_url = this.string_lookup_replace(this.url, this.extra_url_vars);
        const [wx, wy, wz] = this.tms_to_wmts(x, y, z);
        const quadKey = this.tile_xyz_to_quadkey(wx, wy, wz);
        return image_url.replace("{Q}", quadKey);
    }
}
exports.QUADKEYTileSource = QUADKEYTileSource;
QUADKEYTileSource.__name__ = "QUADKEYTileSource";
