import { Annotation, AnnotationView } from "./annotation";
import { TooltipAttachment, Side } from "../../core/enums";
import * as p from "../../core/properties";
export declare function compute_side(attachment: TooltipAttachment, sx: number, sy: number, hcenter: number, vcenter: number): Side;
export declare class TooltipView extends AnnotationView {
    model: Tooltip;
    initialize(): void;
    connect_signals(): void;
    css_classes(): string[];
    render(): void;
    protected _draw_tips(): void;
}
export declare namespace Tooltip {
    type Attrs = p.AttrsOf<Props>;
    type Props = Annotation.Props & {
        attachment: p.Property<TooltipAttachment>;
        inner_only: p.Property<boolean>;
        show_arrow: p.Property<boolean>;
        data: p.Property<[number, number, HTMLElement][]>;
        custom: p.Property<boolean>;
    };
}
export interface Tooltip extends Tooltip.Attrs {
}
export declare class Tooltip extends Annotation {
    properties: Tooltip.Props;
    constructor(attrs?: Partial<Tooltip.Attrs>);
    static init_Tooltip(): void;
    clear(): void;
    add(sx: number, sy: number, content: HTMLElement): void;
}
