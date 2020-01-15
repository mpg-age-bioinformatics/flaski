"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const wmts_tile_source_1 = require("./wmts_tile_source");
const data_renderer_1 = require("../renderers/data_renderer");
const range1d_1 = require("../ranges/range1d");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const image_1 = require("../../core/util/image");
const array_1 = require("../../core/util/array");
const types_1 = require("../../core/util/types");
const selection_manager_1 = require("../../core/selection_manager");
const column_data_source_1 = require("../sources/column_data_source");
const tiles_1 = require("../../styles/tiles");
class TileRendererView extends data_renderer_1.DataRendererView {
    initialize() {
        this._tiles = [];
        super.initialize();
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.change, () => this.request_render());
        this.connect(this.model.tile_source.change, () => this.request_render());
    }
    get_extent() {
        return [this.x_range.start, this.y_range.start, this.x_range.end, this.y_range.end];
    }
    get map_plot() {
        return this.plot_model;
    }
    get map_canvas() {
        return this.plot_view.canvas_view.ctx;
    }
    get map_frame() {
        return this.plot_view.frame;
    }
    get x_range() {
        return this.map_plot.x_range;
    }
    get y_range() {
        return this.map_plot.y_range;
    }
    _set_data() {
        this.extent = this.get_extent();
        this._last_height = undefined;
        this._last_width = undefined;
    }
    _update_attribution() {
        if (this.attribution_el != null)
            dom_1.removeElement(this.attribution_el);
        const { attribution } = this.model.tile_source;
        if (types_1.isString(attribution) && attribution.length > 0) {
            const { layout, frame } = this.plot_view;
            const offset_right = layout._width.value - frame._right.value;
            const offset_bottom = layout._height.value - frame._bottom.value;
            const max_width = frame._width.value;
            this.attribution_el = dom_1.div({
                class: tiles_1.bk_tile_attribution,
                style: {
                    position: "absolute",
                    right: `${offset_right}px`,
                    bottom: `${offset_bottom}px`,
                    'max-width': `${max_width - 4 /*padding*/}px`,
                    padding: "2px",
                    'background-color': 'rgba(255,255,255,0.5)',
                    'font-size': '7pt',
                    'line-height': '1.05',
                    'white-space': 'nowrap',
                    overflow: 'hidden',
                    'text-overflow': 'ellipsis',
                },
            });
            const overlays = this.plot_view.canvas_view.events_el;
            overlays.appendChild(this.attribution_el);
            this.attribution_el.innerHTML = attribution;
            this.attribution_el.title = this.attribution_el.textContent.replace(/\s*\n\s*/g, " ");
        }
    }
    _map_data() {
        this.initial_extent = this.get_extent();
        const zoom_level = this.model.tile_source.get_level_by_extent(this.initial_extent, this.map_frame._height.value, this.map_frame._width.value);
        const new_extent = this.model.tile_source.snap_to_zoom_level(this.initial_extent, this.map_frame._height.value, this.map_frame._width.value, zoom_level);
        this.x_range.start = new_extent[0];
        this.y_range.start = new_extent[1];
        this.x_range.end = new_extent[2];
        this.y_range.end = new_extent[3];
        if (this.x_range instanceof range1d_1.Range1d) {
            this.x_range.reset_start = new_extent[0];
            this.x_range.reset_end = new_extent[2];
        }
        if (this.y_range instanceof range1d_1.Range1d) {
            this.y_range.reset_start = new_extent[1];
            this.y_range.reset_end = new_extent[3];
        }
        this._update_attribution();
    }
    _create_tile(x, y, z, bounds, cache_only = false) {
        const [nx, ny, nz] = this.model.tile_source.normalize_xyz(x, y, z);
        const tile = {
            img: undefined,
            tile_coords: [x, y, z],
            normalized_coords: [nx, ny, nz],
            quadkey: this.model.tile_source.tile_xyz_to_quadkey(x, y, z),
            cache_key: this.model.tile_source.tile_xyz_to_key(x, y, z),
            bounds,
            loaded: false,
            finished: false,
            x_coord: bounds[0],
            y_coord: bounds[3],
        };
        const src = this.model.tile_source.get_image_url(nx, ny, nz);
        new image_1.ImageLoader(src, {
            loaded: (img) => {
                Object.assign(tile, { img, loaded: true });
                if (cache_only) {
                    tile.finished = true;
                    this.notify_finished();
                }
                else
                    this.request_render();
            },
            failed() {
                tile.finished = true;
            },
        });
        this.model.tile_source.tiles.set(tile.cache_key, tile);
        this._tiles.push(tile);
    }
    _enforce_aspect_ratio() {
        // brute force way of handling resize or sizing_mode event -------------------------------------------------------------
        if ((this._last_height !== this.map_frame._height.value) || (this._last_width !== this.map_frame._width.value)) {
            const extent = this.get_extent();
            const zoom_level = this.model.tile_source.get_level_by_extent(extent, this.map_frame._height.value, this.map_frame._width.value);
            const new_extent = this.model.tile_source.snap_to_zoom_level(extent, this.map_frame._height.value, this.map_frame._width.value, zoom_level);
            this.x_range.setv({ start: new_extent[0], end: new_extent[2] });
            this.y_range.setv({ start: new_extent[1], end: new_extent[3] });
            this.extent = new_extent;
            this._last_height = this.map_frame._height.value;
            this._last_width = this.map_frame._width.value;
        }
    }
    has_finished() {
        if (!super.has_finished()) {
            return false;
        }
        if (this._tiles.length === 0) {
            return false;
        }
        for (const tile of this._tiles) {
            if (!tile.finished) {
                return false;
            }
        }
        return true;
    }
    render() {
        if (this.map_initialized == null) {
            this._set_data();
            this._map_data();
            this.map_initialized = true;
        }
        this._enforce_aspect_ratio();
        this._update();
        if (this.prefetch_timer != null) {
            clearTimeout(this.prefetch_timer);
        }
        this.prefetch_timer = setTimeout(this._prefetch_tiles.bind(this), 500);
        if (this.has_finished()) {
            this.notify_finished();
        }
    }
    _draw_tile(tile_key) {
        const tile_data = this.model.tile_source.tiles.get(tile_key);
        if (tile_data != null && tile_data.loaded) {
            const [[sxmin], [symin]] = this.plot_view.map_to_screen([tile_data.bounds[0]], [tile_data.bounds[3]]);
            const [[sxmax], [symax]] = this.plot_view.map_to_screen([tile_data.bounds[2]], [tile_data.bounds[1]]);
            const sw = sxmax - sxmin;
            const sh = symax - symin;
            const sx = sxmin;
            const sy = symin;
            const old_smoothing = this.map_canvas.getImageSmoothingEnabled();
            this.map_canvas.setImageSmoothingEnabled(this.model.smoothing);
            this.map_canvas.drawImage(tile_data.img, sx, sy, sw, sh);
            this.map_canvas.setImageSmoothingEnabled(old_smoothing);
            tile_data.finished = true;
        }
    }
    _set_rect() {
        const outline_width = this.plot_model.properties.outline_line_width.value();
        const l = this.map_frame._left.value + (outline_width / 2);
        const t = this.map_frame._top.value + (outline_width / 2);
        const w = this.map_frame._width.value - outline_width;
        const h = this.map_frame._height.value - outline_width;
        this.map_canvas.rect(l, t, w, h);
        this.map_canvas.clip();
    }
    _render_tiles(tile_keys) {
        this.map_canvas.save();
        this._set_rect();
        this.map_canvas.globalAlpha = this.model.alpha;
        for (const tile_key of tile_keys) {
            this._draw_tile(tile_key);
        }
        this.map_canvas.restore();
    }
    _prefetch_tiles() {
        const { tile_source } = this.model;
        const extent = this.get_extent();
        const h = this.map_frame._height.value;
        const w = this.map_frame._width.value;
        const zoom_level = this.model.tile_source.get_level_by_extent(extent, h, w);
        const tiles = this.model.tile_source.get_tiles_by_extent(extent, zoom_level);
        for (let t = 0, end = Math.min(10, tiles.length); t < end; t++) {
            const [x, y, z] = tiles[t];
            const children = this.model.tile_source.children_by_tile_xyz(x, y, z);
            for (const c of children) {
                const [cx, cy, cz, cbounds] = c;
                if (tile_source.tiles.has(tile_source.tile_xyz_to_key(cx, cy, cz))) {
                    continue;
                }
                else {
                    this._create_tile(cx, cy, cz, cbounds, true);
                }
            }
        }
    }
    _fetch_tiles(tiles) {
        for (const tile of tiles) {
            const [x, y, z, bounds] = tile;
            this._create_tile(x, y, z, bounds);
        }
    }
    _update() {
        const { tile_source } = this.model;
        const { min_zoom } = tile_source;
        const { max_zoom } = tile_source;
        let extent = this.get_extent();
        const zooming_out = (this.extent[2] - this.extent[0]) < (extent[2] - extent[0]);
        const h = this.map_frame._height.value;
        const w = this.map_frame._width.value;
        let zoom_level = tile_source.get_level_by_extent(extent, h, w);
        let snap_back = false;
        if (zoom_level < min_zoom) {
            extent = this.extent;
            zoom_level = min_zoom;
            snap_back = true;
        }
        else if (zoom_level > max_zoom) {
            extent = this.extent;
            zoom_level = max_zoom;
            snap_back = true;
        }
        if (snap_back) {
            this.x_range.setv({ x_range: { start: extent[0], end: extent[2] } });
            this.y_range.setv({ start: extent[1], end: extent[3] });
            this.extent = extent;
        }
        this.extent = extent;
        const tiles = tile_source.get_tiles_by_extent(extent, zoom_level);
        const need_load = [];
        const cached = [];
        const parents = [];
        const children = [];
        for (const t of tiles) {
            const [x, y, z] = t;
            const key = tile_source.tile_xyz_to_key(x, y, z);
            const tile = tile_source.tiles.get(key);
            if (tile != null && tile.loaded) {
                cached.push(key);
            }
            else {
                if (this.model.render_parents) {
                    const [px, py, pz] = tile_source.get_closest_parent_by_tile_xyz(x, y, z);
                    const parent_key = tile_source.tile_xyz_to_key(px, py, pz);
                    const parent_tile = tile_source.tiles.get(parent_key);
                    if ((parent_tile != null) && parent_tile.loaded && !array_1.includes(parents, parent_key)) {
                        parents.push(parent_key);
                    }
                    if (zooming_out) {
                        const child_tiles = tile_source.children_by_tile_xyz(x, y, z);
                        for (const [cx, cy, cz] of child_tiles) {
                            const child_key = tile_source.tile_xyz_to_key(cx, cy, cz);
                            if (tile_source.tiles.has(child_key))
                                children.push(child_key);
                        }
                    }
                }
            }
            if (tile == null)
                need_load.push(t);
        }
        // draw stand-in parents ----------
        this._render_tiles(parents);
        this._render_tiles(children);
        // draw cached ----------
        this._render_tiles(cached);
        // fetch missing -------
        if (this.render_timer != null) {
            clearTimeout(this.render_timer);
        }
        this.render_timer = setTimeout((() => this._fetch_tiles(need_load)), 65);
    }
}
exports.TileRendererView = TileRendererView;
TileRendererView.__name__ = "TileRendererView";
class TileRenderer extends data_renderer_1.DataRenderer {
    constructor(attrs) {
        super(attrs);
        // XXX: tile renderer doesn't allow selection, but needs to fulfil the APIs
        this._selection_manager = new selection_manager_1.SelectionManager({
            source: new column_data_source_1.ColumnDataSource(),
        });
    }
    static init_TileRenderer() {
        this.prototype.default_view = TileRendererView;
        this.define({
            alpha: [p.Number, 1.0],
            smoothing: [p.Boolean, true],
            tile_source: [p.Instance, () => new wmts_tile_source_1.WMTSTileSource()],
            render_parents: [p.Boolean, true],
        });
    }
    get_selection_manager() {
        return this._selection_manager;
    }
}
exports.TileRenderer = TileRenderer;
TileRenderer.__name__ = "TileRenderer";
TileRenderer.init_TileRenderer();
