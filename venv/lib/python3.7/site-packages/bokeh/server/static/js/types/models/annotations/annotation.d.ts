import { SidePanel } from "../../core/layout/side_panel";
import { Size } from "../../core/layout";
import { Context2d } from "../../core/util/canvas";
import { Renderer, RendererView } from "../renderers/renderer";
import { ColumnarDataSource } from "../sources/columnar_data_source";
export declare abstract class AnnotationView extends RendererView {
    model: Annotation;
    layout: SidePanel;
    readonly panel: SidePanel | undefined;
    get_size(): Size;
    connect_signals(): void;
    protected _get_size(): Size;
    readonly ctx: Context2d;
    set_data(source: ColumnarDataSource): void;
    readonly needs_clip: boolean;
    serializable_state(): {
        [key: string]: unknown;
    };
}
export declare namespace Annotation {
    type Attrs = Renderer.Attrs;
    type Props = Renderer.Props;
    type Visuals = Renderer.Visuals;
}
export interface Annotation extends Annotation.Attrs {
}
export declare abstract class Annotation extends Renderer {
    properties: Annotation.Props;
    constructor(attrs?: Partial<Annotation.Attrs>);
    static init_Annotation(): void;
}
