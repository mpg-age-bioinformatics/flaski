"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const layout_provider_1 = require("./layout_provider");
const p = require("../../core/properties");
class StaticLayoutProvider extends layout_provider_1.LayoutProvider {
    constructor(attrs) {
        super(attrs);
    }
    static init_StaticLayoutProvider() {
        this.define({
            graph_layout: [p.Any, {}],
        });
    }
    get_node_coordinates(node_source) {
        const xs = [];
        const ys = [];
        const index = node_source.data.index;
        for (let i = 0, end = index.length; i < end; i++) {
            const point = this.graph_layout[index[i]];
            const [x, y] = point != null ? point : [NaN, NaN];
            xs.push(x);
            ys.push(y);
        }
        return [xs, ys];
    }
    get_edge_coordinates(edge_source) {
        const xs = [];
        const ys = [];
        const starts = edge_source.data.start;
        const ends = edge_source.data.end;
        const has_paths = (edge_source.data.xs != null) && (edge_source.data.ys != null);
        for (let i = 0, endi = starts.length; i < endi; i++) {
            const in_layout = (this.graph_layout[starts[i]] != null) && (this.graph_layout[ends[i]] != null);
            if (has_paths && in_layout) {
                xs.push(edge_source.data.xs[i]);
                ys.push(edge_source.data.ys[i]);
            }
            else {
                let end, start;
                if (in_layout)
                    [start, end] = [this.graph_layout[starts[i]], this.graph_layout[ends[i]]];
                else
                    [start, end] = [[NaN, NaN], [NaN, NaN]];
                xs.push([start[0], end[0]]);
                ys.push([start[1], end[1]]);
            }
        }
        return [xs, ys];
    }
}
exports.StaticLayoutProvider = StaticLayoutProvider;
StaticLayoutProvider.__name__ = "StaticLayoutProvider";
StaticLayoutProvider.init_StaticLayoutProvider();
