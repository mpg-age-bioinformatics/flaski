import { TickFormatter } from "./tick_formatter";
import * as p from "../../core/properties";
export declare namespace FuncTickFormatter {
    type Attrs = p.AttrsOf<Props>;
    type Props = TickFormatter.Props & {
        args: p.Property<{
            [key: string]: unknown;
        }>;
        code: p.Property<string>;
        use_strict: p.Property<boolean>;
    };
}
export interface FuncTickFormatter extends FuncTickFormatter.Attrs {
}
export declare class FuncTickFormatter extends TickFormatter {
    properties: FuncTickFormatter.Props;
    constructor(attrs?: Partial<FuncTickFormatter.Attrs>);
    static init_FuncTickFormatter(): void;
    readonly names: string[];
    readonly values: any[];
    _make_func(): Function;
    doFormat(ticks: number[], _opts: {
        loc: number;
    }): string[];
}
