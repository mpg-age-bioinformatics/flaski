import { Grid as SlickGrid, DataProvider } from "slickgrid";
import * as p from "../../../core/properties";
import { TableWidget } from "./table_widget";
import { TableColumn, ColumnType, Item } from "./table_column";
import { WidgetView } from "../widget";
import { ColumnDataSource } from "../../sources/column_data_source";
import { CDSView } from "../../sources/cds_view";
export declare const DTINDEX_NAME = "__bkdt_internal_index__";
export declare class TableDataProvider implements DataProvider<Item> {
    readonly source: ColumnDataSource;
    readonly view: CDSView;
    readonly index: number[];
    constructor(source: ColumnDataSource, view: CDSView);
    getLength(): number;
    getItem(offset: number): Item;
    getField(offset: number, field: string): any;
    setField(offset: number, field: string, value: any): void;
    getItemMetadata(_index: number): any;
    getRecords(): Item[];
    sort(columns: any[]): void;
}
export declare class DataTableView extends WidgetView {
    model: DataTable;
    protected data: TableDataProvider;
    protected grid: SlickGrid<Item>;
    protected _in_selection_update: boolean;
    protected _warned_not_reorderable: boolean;
    connect_signals(): void;
    _update_layout(): void;
    update_position(): void;
    updateGrid(): void;
    updateSelection(): void;
    newIndexColumn(): ColumnType;
    css_classes(): string[];
    render(): void;
    _hide_header(): void;
}
export declare namespace DataTable {
    type Attrs = p.AttrsOf<Props>;
    type Props = TableWidget.Props & {
        columns: p.Property<TableColumn[]>;
        fit_columns: p.Property<boolean>;
        sortable: p.Property<boolean>;
        reorderable: p.Property<boolean>;
        editable: p.Property<boolean>;
        selectable: p.Property<boolean | "checkbox">;
        index_position: p.Property<number | null>;
        index_header: p.Property<string>;
        index_width: p.Property<number>;
        scroll_to_selection: p.Property<boolean>;
        header_row: p.Property<boolean>;
        row_height: p.Property<number>;
    };
}
export interface DataTable extends DataTable.Attrs {
}
export declare class DataTable extends TableWidget {
    properties: DataTable.Props;
    private _sort_columns;
    readonly sort_columns: any[];
    constructor(attrs?: Partial<DataTable.Attrs>);
    static init_DataTable(): void;
    update_sort_columns(sortCols: any): null;
    get_scroll_index(grid_range: {
        top: number;
        bottom: number;
    }, selected_indices: number[]): number | null;
}
