import { LayoutDOM } from "./models";
import { SizingMode, Location } from "../core/enums";
export interface GridPlotOpts {
    toolbar_location?: Location | null;
    merge_tools?: boolean;
    sizing_mode?: SizingMode;
    plot_width?: number;
    plot_height?: number;
}
export declare function gridplot(children: (LayoutDOM | null)[][], opts?: GridPlotOpts): LayoutDOM;
