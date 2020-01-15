"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const model_1 = require("../../model");
const p = require("../../core/properties");
const array_1 = require("../../core/util/array");
const object_1 = require("../../core/util/object");
class Selection extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_Selection() {
        this.define({
            indices: [p.Array, []],
            line_indices: [p.Array, []],
            multiline_indices: [p.Any, {}],
        });
        this.internal({
            final: [p.Boolean],
            selected_glyphs: [p.Array, []],
            get_view: [p.Any],
            image_indices: [p.Array, []],
        });
    }
    initialize() {
        super.initialize();
        this['0d'] = { glyph: null, indices: [], flag: false, get_view: () => null };
        this['1d'] = { indices: this.indices };
        this['2d'] = { indices: {} };
        this.get_view = () => null;
        this.connect(this.properties.indices.change, () => this['1d'].indices = this.indices);
        this.connect(this.properties.line_indices.change, () => {
            this['0d'].indices = this.line_indices;
            this['0d'].flag = this.line_indices.length != 0;
        });
        this.connect(this.properties.selected_glyphs.change, () => this['0d'].glyph = this.selected_glyph);
        this.connect(this.properties.get_view.change, () => this['0d'].get_view = this.get_view);
        this.connect(this.properties.multiline_indices.change, () => this['2d'].indices = this.multiline_indices);
    }
    get selected_glyph() {
        return this.selected_glyphs.length > 0 ? this.selected_glyphs[0] : null;
    }
    add_to_selected_glyphs(glyph) {
        this.selected_glyphs.push(glyph);
    }
    update(selection, final, append) {
        this.final = final;
        if (append)
            this.update_through_union(selection);
        else {
            this.indices = selection.indices;
            this.line_indices = selection.line_indices;
            this.selected_glyphs = selection.selected_glyphs;
            this.get_view = selection.get_view;
            this.multiline_indices = selection.multiline_indices;
            this.image_indices = selection.image_indices;
        }
    }
    clear() {
        this.final = true;
        this.indices = [];
        this.line_indices = [];
        this.multiline_indices = {};
        this.get_view = () => null;
        this.selected_glyphs = [];
    }
    is_empty() {
        return this.indices.length == 0 && this.line_indices.length == 0 && this.image_indices.length == 0;
    }
    update_through_union(other) {
        this.indices = array_1.union(other.indices, this.indices);
        this.selected_glyphs = array_1.union(other.selected_glyphs, this.selected_glyphs);
        this.line_indices = array_1.union(other.line_indices, this.line_indices);
        if (!this.get_view())
            this.get_view = other.get_view;
        this.multiline_indices = object_1.merge(other.multiline_indices, this.multiline_indices);
    }
    update_through_intersection(other) {
        this.indices = array_1.intersection(other.indices, this.indices);
        // TODO: think through and fix any logic below
        this.selected_glyphs = array_1.union(other.selected_glyphs, this.selected_glyphs);
        this.line_indices = array_1.union(other.line_indices, this.line_indices);
        if (!this.get_view())
            this.get_view = other.get_view;
        this.multiline_indices = object_1.merge(other.multiline_indices, this.multiline_indices);
    }
}
exports.Selection = Selection;
Selection.__name__ = "Selection";
Selection.init_Selection();
