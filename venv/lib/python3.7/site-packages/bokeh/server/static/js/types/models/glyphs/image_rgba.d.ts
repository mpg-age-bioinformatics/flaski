import { ImageBase, ImageBaseView, ImageDataBase } from "./image_base";
import { Arrayable } from "../../core/types";
import { Class } from "../../core/class";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
export interface ImageRGBAData extends ImageDataBase {
}
export interface ImageRGBAView extends ImageRGBAData {
}
export declare class ImageRGBAView extends ImageBaseView {
    model: ImageRGBA;
    visuals: ImageRGBA.Visuals;
    protected _width: Arrayable<number>;
    protected _height: Arrayable<number>;
    initialize(): void;
    protected _set_data(indices: number[] | null): void;
    protected _render(ctx: Context2d, indices: number[], { image_data, sx, sy, sw, sh }: ImageRGBAData): void;
}
export declare namespace ImageRGBA {
    type Attrs = p.AttrsOf<Props>;
    type Props = ImageBase.Props & {
        image: p.NumberSpec;
        dw: p.DistanceSpec;
        dh: p.DistanceSpec;
        global_alpha: p.Property<number>;
        dilate: p.Property<boolean>;
    };
    type Visuals = ImageBase.Visuals;
}
export interface ImageRGBA extends ImageRGBA.Attrs {
}
export declare class ImageRGBA extends ImageBase {
    properties: ImageRGBA.Props;
    default_view: Class<ImageRGBAView>;
    constructor(attrs?: Partial<ImageRGBA.Attrs>);
    static init_ImageRGBA(): void;
}
