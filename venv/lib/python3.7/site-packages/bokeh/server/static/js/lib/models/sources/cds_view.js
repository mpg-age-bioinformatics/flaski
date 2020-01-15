"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const model_1 = require("../../model");
const p = require("../../core/properties");
const selection_1 = require("../selections/selection");
const array_1 = require("../../core/util/array");
const columnar_data_source_1 = require("./columnar_data_source");
class CDSView extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_CDSView() {
        this.define({
            filters: [p.Array, []],
            source: [p.Instance],
        });
        this.internal({
            indices: [p.Array, []],
            indices_map: [p.Any, {}],
        });
    }
    initialize() {
        super.initialize();
        this.compute_indices();
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.properties.filters.change, () => {
            this.compute_indices();
            this.change.emit();
        });
        const connect_listeners = () => {
            const fn = () => this.compute_indices();
            if (this.source != null) {
                this.connect(this.source.change, fn);
                if (this.source instanceof columnar_data_source_1.ColumnarDataSource) {
                    this.connect(this.source.streaming, fn);
                    this.connect(this.source.patching, fn);
                }
            }
        };
        let initialized = this.source != null;
        if (initialized)
            connect_listeners();
        else {
            this.connect(this.properties.source.change, () => {
                if (!initialized) {
                    connect_listeners();
                    initialized = true;
                }
            });
        }
    }
    compute_indices() {
        const indices = this.filters
            .map((filter) => filter.compute_indices(this.source))
            .filter((indices) => indices != null);
        if (indices.length > 0)
            this.indices = array_1.intersection.apply(this, indices);
        else if (this.source instanceof columnar_data_source_1.ColumnarDataSource)
            this.indices = this.source.get_indices();
        this.indices_map_to_subset();
    }
    indices_map_to_subset() {
        this.indices_map = {};
        for (let i = 0; i < this.indices.length; i++) {
            this.indices_map[this.indices[i]] = i;
        }
    }
    convert_selection_from_subset(selection_subset) {
        const selection_full = new selection_1.Selection();
        selection_full.update_through_union(selection_subset);
        const indices_1d = selection_subset.indices.map((i) => this.indices[i]);
        selection_full.indices = indices_1d;
        selection_full.image_indices = selection_subset.image_indices;
        return selection_full;
    }
    convert_selection_to_subset(selection_full) {
        const selection_subset = new selection_1.Selection();
        selection_subset.update_through_union(selection_full);
        const indices_1d = selection_full.indices.map((i) => this.indices_map[i]);
        selection_subset.indices = indices_1d;
        selection_subset.image_indices = selection_full.image_indices;
        return selection_subset;
    }
    convert_indices_from_subset(indices) {
        return indices.map((i) => this.indices[i]);
    }
}
exports.CDSView = CDSView;
CDSView.__name__ = "CDSView";
CDSView.init_CDSView();
