import { GuideRenderer, GuideRendererView } from "../renderers/guide_renderer";
import { Ticker } from "../tickers/ticker";
import { TickFormatter } from "../formatters/tick_formatter";
import { Range } from "../ranges/range";
import * as visuals from "../../core/visuals";
import * as mixins from "../../core/property_mixins";
import * as p from "../../core/properties";
import { Side, TickLabelOrientation, SpatialUnits } from "../../core/enums";
import { Size } from "../../core/layout";
import { SidePanel, Orient } from "../../core/layout/side_panel";
import { Context2d } from "../../core/util/canvas";
import { Factor } from "../ranges/factor_range";
export interface Extents {
    tick: number;
    tick_label: number[];
    axis_label: number;
}
export declare type Coords = [number[], number[]];
export interface TickCoords {
    major: Coords;
    minor: Coords;
}
export declare class AxisView extends GuideRendererView {
    model: Axis;
    visuals: Axis.Visuals;
    layout: SidePanel;
    readonly rotate: boolean;
    readonly panel: SidePanel;
    render(): void;
    protected _render?(ctx: Context2d, extents: Extents, tick_coords: TickCoords): void;
    connect_signals(): void;
    get_size(): Size;
    protected _get_size(): number;
    readonly needs_clip: boolean;
    protected _draw_rule(ctx: Context2d, _extents: Extents): void;
    protected _draw_major_ticks(ctx: Context2d, _extents: Extents, tick_coords: TickCoords): void;
    protected _draw_minor_ticks(ctx: Context2d, _extents: Extents, tick_coords: TickCoords): void;
    protected _draw_major_labels(ctx: Context2d, extents: Extents, tick_coords: TickCoords): void;
    protected _draw_axis_label(ctx: Context2d, extents: Extents, _tick_coords: TickCoords): void;
    protected _draw_ticks(ctx: Context2d, coords: Coords, tin: number, tout: number, visuals: visuals.Line): void;
    protected _draw_oriented_labels(ctx: Context2d, labels: string[], coords: Coords, orient: Orient | number, _side: Side, standoff: number, visuals: visuals.Text, units?: SpatialUnits): void;
    _axis_label_extent(): number;
    _tick_extent(): number;
    _tick_label_extent(): number;
    protected _tick_label_extents(): number[];
    protected _oriented_labels_extent(labels: string[], orient: Orient | number, side: Side, standoff: number, visuals: visuals.Text): number;
    readonly normals: [number, number];
    readonly dimension: 0 | 1;
    compute_labels(ticks: number[]): string[];
    readonly offsets: [number, number];
    readonly ranges: [Range, Range];
    readonly computed_bounds: [number, number];
    readonly rule_coords: Coords;
    readonly tick_coords: TickCoords;
    readonly loc: number;
    serializable_state(): {
        [key: string]: unknown;
    };
}
export declare namespace Axis {
    type Attrs = p.AttrsOf<Props>;
    type Props = GuideRenderer.Props & {
        bounds: p.Property<[number, number] | "auto">;
        ticker: p.Property<Ticker<any>>;
        formatter: p.Property<TickFormatter>;
        x_range_name: p.Property<string>;
        y_range_name: p.Property<string>;
        axis_label: p.Property<string | null>;
        axis_label_standoff: p.Property<number>;
        major_label_standoff: p.Property<number>;
        major_label_orientation: p.Property<TickLabelOrientation | number>;
        major_label_overrides: p.Property<{
            [key: string]: string;
        }>;
        major_tick_in: p.Property<number>;
        major_tick_out: p.Property<number>;
        minor_tick_in: p.Property<number>;
        minor_tick_out: p.Property<number>;
        fixed_location: p.Property<number | Factor | null>;
    } & mixins.AxisLine & mixins.MajorTickLine & mixins.MinorTickLine & mixins.MajorLabelText & mixins.AxisLabelText;
    type Visuals = GuideRenderer.Visuals & {
        axis_line: visuals.Line;
        major_tick_line: visuals.Line;
        minor_tick_line: visuals.Line;
        major_label_text: visuals.Text;
        axis_label_text: visuals.Text;
    };
}
export interface Axis extends Axis.Attrs {
    panel: SidePanel;
}
export declare class Axis extends GuideRenderer {
    properties: Axis.Props;
    constructor(attrs?: Partial<Axis.Attrs>);
    static init_Axis(): void;
}
