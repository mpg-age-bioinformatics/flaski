import { DataRenderer, DataRendererView } from "./data_renderer";
import { Glyph, GlyphView } from "../glyphs/glyph";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import { Scale } from "../scales/scale";
import { CDSView } from "../sources/cds_view";
import { Class } from "../../core/class";
import * as p from "../../core/properties";
import * as hittest from "../../core/hittest";
import { Geometry } from "../../core/geometry";
import { SelectionManager } from "../../core/selection_manager";
import { Context2d } from "../../core/util/canvas";
export declare class GlyphRendererView extends DataRendererView {
    model: GlyphRenderer;
    glyph: GlyphView;
    selection_glyph: GlyphView;
    nonselection_glyph: GlyphView;
    hover_glyph?: GlyphView;
    muted_glyph?: GlyphView;
    decimated_glyph: GlyphView;
    xscale: Scale;
    yscale: Scale;
    protected all_indices: number[];
    protected decimated: number[];
    set_data_timestamp: number;
    protected last_dtrender: number;
    initialize(): void;
    build_glyph_view<T extends Glyph>(model: T): GlyphView;
    connect_signals(): void;
    have_selection_glyphs(): boolean;
    set_data(request_render?: boolean, indices?: number[] | null): void;
    readonly has_webgl: boolean;
    render(): void;
    draw_legend(ctx: Context2d, x0: number, x1: number, y0: number, y1: number, field: string | null, label: string, index: number | null): void;
    hit_test(geometry: Geometry): hittest.HitTestResult;
}
export declare namespace GlyphRenderer {
    type Attrs = p.AttrsOf<Props>;
    type Props = DataRenderer.Props & {
        data_source: p.Property<ColumnarDataSource>;
        view: p.Property<CDSView>;
        glyph: p.Property<Glyph>;
        hover_glyph: p.Property<Glyph>;
        nonselection_glyph: p.Property<Glyph | "auto">;
        selection_glyph: p.Property<Glyph | "auto">;
        muted_glyph: p.Property<Glyph>;
        muted: p.Property<boolean>;
    };
}
export interface GlyphRenderer extends GlyphRenderer.Attrs {
}
export declare class GlyphRenderer extends DataRenderer {
    properties: GlyphRenderer.Props;
    default_view: Class<GlyphRendererView>;
    constructor(attrs?: Partial<GlyphRenderer.Attrs>);
    static init_GlyphRenderer(): void;
    initialize(): void;
    get_reference_point(field: string | null, value?: any): number;
    get_selection_manager(): SelectionManager;
}
