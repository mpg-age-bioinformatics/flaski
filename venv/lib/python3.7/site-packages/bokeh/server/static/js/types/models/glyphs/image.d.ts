import { ImageBase, ImageBaseView, ImageDataBase } from "./image_base";
import { ColorMapper } from "../mappers/color_mapper";
import { Class } from "../../core/class";
import { Arrayable } from "../../core/types";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
export interface ImageData extends ImageDataBase {
}
export interface ImageView extends ImageData {
}
export declare class ImageView extends ImageBaseView {
    model: Image;
    visuals: Image.Visuals;
    protected _width: Arrayable<number>;
    protected _height: Arrayable<number>;
    initialize(): void;
    protected _update_image(): void;
    protected _set_data(): void;
    protected _render(ctx: Context2d, indices: number[], { image_data, sx, sy, sw, sh }: ImageData): void;
}
export declare namespace Image {
    type Attrs = p.AttrsOf<Props>;
    type Props = ImageBase.Props & {
        image: p.NumberSpec;
        dw: p.DistanceSpec;
        dh: p.DistanceSpec;
        global_alpha: p.Property<number>;
        dilate: p.Property<boolean>;
        color_mapper: p.Property<ColorMapper>;
    };
    type Visuals = ImageBase.Visuals;
}
export interface Image extends Image.Attrs {
}
export declare class Image extends ImageBase {
    properties: Image.Props;
    default_view: Class<ImageView>;
    constructor(attrs?: Partial<Image.Attrs>);
    static init_Image(): void;
}
