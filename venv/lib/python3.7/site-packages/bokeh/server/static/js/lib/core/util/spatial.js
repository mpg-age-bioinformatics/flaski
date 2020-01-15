"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const FlatBush = require("flatbush");
const bbox_1 = require("./bbox");
class SpatialIndex {
    constructor(points) {
        this.points = points;
        this.index = null;
        if (points.length > 0) {
            this.index = new FlatBush(points.length);
            for (const p of points) {
                const { x0, y0, x1, y1 } = p;
                this.index.add(x0, y0, x1, y1);
            }
            this.index.finish();
        }
    }
    _normalize(rect) {
        let { x0, y0, x1, y1 } = rect;
        if (x0 > x1)
            [x0, x1] = [x1, x0];
        if (y0 > y1)
            [y0, y1] = [y1, y0];
        return { x0, y0, x1, y1 };
    }
    get bbox() {
        if (this.index == null)
            return bbox_1.empty();
        else {
            const { minX, minY, maxX, maxY } = this.index;
            return { x0: minX, y0: minY, x1: maxX, y1: maxY };
        }
    }
    search(rect) {
        if (this.index == null)
            return [];
        else {
            const { x0, y0, x1, y1 } = this._normalize(rect);
            const indices = this.index.search(x0, y0, x1, y1);
            return indices.map((j) => this.points[j]);
        }
    }
    indices(rect) {
        return this.search(rect).map(({ i }) => i);
    }
}
exports.SpatialIndex = SpatialIndex;
SpatialIndex.__name__ = "SpatialIndex";
