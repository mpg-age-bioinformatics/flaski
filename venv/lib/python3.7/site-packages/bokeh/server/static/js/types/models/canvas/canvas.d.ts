import { HasProps } from "../../core/has_props";
import { DOMView } from "../../core/dom_view";
import * as p from "../../core/properties";
import { OutputBackend } from "../../core/enums";
import { BBox } from "../../core/util/bbox";
import { Context2d } from "../../core/util/canvas";
export declare type SVGRenderingContext2D = {
    getSvg(): SVGSVGElement;
    getSerializedSvg(fix_named_entities: boolean): string;
};
export declare class CanvasView extends DOMView {
    model: Canvas;
    bbox: BBox;
    _ctx: CanvasRenderingContext2D | SVGRenderingContext2D;
    readonly ctx: Context2d;
    canvas_el: HTMLCanvasElement | SVGSVGElement;
    overlays_el: HTMLElement;
    events_el: HTMLElement;
    map_el: HTMLElement | null;
    initialize(): void;
    get_canvas_element(): HTMLCanvasElement | SVGSVGElement;
    prepare_canvas(width: number, height: number): void;
}
export declare namespace Canvas {
    type Attrs = p.AttrsOf<Props>;
    type Props = HasProps.Props & {
        map: p.Property<boolean>;
        use_hidpi: p.Property<boolean>;
        pixel_ratio: p.Property<number>;
        output_backend: p.Property<OutputBackend>;
    };
}
export interface Canvas extends Canvas.Attrs {
}
export declare class Canvas extends HasProps {
    properties: Canvas.Props;
    constructor(attrs?: Partial<Canvas.Attrs>);
    static init_Canvas(): void;
}
