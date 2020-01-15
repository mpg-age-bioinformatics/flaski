import { Callback } from "./callback";
import * as p from "../../core/properties";
export declare namespace CustomJS {
    type Attrs = p.AttrsOf<Props>;
    type Props = Callback.Props & {
        args: p.Property<{
            [key: string]: unknown;
        }>;
        code: p.Property<string>;
        use_strict: p.Property<boolean>;
    };
}
export interface CustomJS extends CustomJS.Attrs {
}
export declare class CustomJS extends Callback {
    properties: CustomJS.Props;
    constructor(attrs?: Partial<CustomJS.Attrs>);
    static init_CustomJS(): void;
    readonly names: string[];
    readonly values: any[];
    readonly func: Function;
    execute(cb_obj: unknown, cb_data?: {
        [key: string]: unknown;
    }): unknown;
}
