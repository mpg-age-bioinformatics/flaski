"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const { RowSelectionModel } = require("slickgrid/plugins/slick.rowselectionmodel");
const { CheckboxSelectColumn } = require("slickgrid/plugins/slick.checkboxselectcolumn");
const { CellExternalCopyManager } = require("slickgrid/plugins/slick.cellexternalcopymanager");
const slickgrid_1 = require("slickgrid");
const p = require("../../../core/properties");
const string_1 = require("../../../core/util/string");
const types_1 = require("../../../core/util/types");
const array_1 = require("../../../core/util/array");
const object_1 = require("../../../core/util/object");
const logging_1 = require("../../../core/logging");
const layout_1 = require("../../../core/layout");
const table_widget_1 = require("./table_widget");
const widget_1 = require("../widget");
const tables_1 = require("../../../styles/widgets/tables");
exports.DTINDEX_NAME = "__bkdt_internal_index__";
class TableDataProvider {
    constructor(source, view) {
        this.source = source;
        this.view = view;
        if (exports.DTINDEX_NAME in this.source.data)
            throw new Error(`special name ${exports.DTINDEX_NAME} cannot be used as a data table column`);
        this.index = this.view.indices;
    }
    getLength() {
        return this.index.length;
    }
    getItem(offset) {
        const item = {};
        for (const field of object_1.keys(this.source.data)) {
            item[field] = this.source.data[field][this.index[offset]];
        }
        item[exports.DTINDEX_NAME] = this.index[offset];
        return item;
    }
    getField(offset, field) {
        // offset is the
        if (field == exports.DTINDEX_NAME) {
            return this.index[offset];
        }
        return this.source.data[field][this.index[offset]];
    }
    setField(offset, field, value) {
        // field assumed never to be internal index name (ctor would throw)
        const index = this.index[offset];
        this.source.patch({ [field]: [[index, value]] });
    }
    getItemMetadata(_index) {
        return null;
    }
    getRecords() {
        return array_1.range(0, this.getLength()).map((i) => this.getItem(i));
    }
    sort(columns) {
        let cols = columns.map((column) => [column.sortCol.field, column.sortAsc ? 1 : -1]);
        if (cols.length == 0) {
            cols = [[exports.DTINDEX_NAME, 1]];
        }
        const records = this.getRecords();
        const old_index = this.index.slice();
        this.index.sort(function (i1, i2) {
            for (const [field, sign] of cols) {
                const value1 = records[old_index.indexOf(i1)][field];
                const value2 = records[old_index.indexOf(i2)][field];
                const result = value1 == value2 ? 0 : value1 > value2 ? sign : -sign;
                if (result != 0)
                    return result;
            }
            return 0;
        });
    }
}
exports.TableDataProvider = TableDataProvider;
TableDataProvider.__name__ = "TableDataProvider";
class DataTableView extends widget_1.WidgetView {
    constructor() {
        super(...arguments);
        this._in_selection_update = false;
        this._warned_not_reorderable = false;
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.change, () => this.render());
        this.connect(this.model.source.streaming, () => this.updateGrid());
        this.connect(this.model.source.patching, () => this.updateGrid());
        this.connect(this.model.source.change, () => this.updateGrid());
        this.connect(this.model.source.properties.data.change, () => this.updateGrid());
        this.connect(this.model.source.selected.change, () => this.updateSelection());
        this.connect(this.model.source.selected.properties.indices.change, () => this.updateSelection());
    }
    _update_layout() {
        this.layout = new layout_1.LayoutItem();
        this.layout.set_sizing(this.box_sizing());
    }
    update_position() {
        super.update_position();
        this.grid.resizeCanvas();
    }
    updateGrid() {
        // TODO (bev) This is to ensure that CDSView indices are properly computed
        // before passing to the DataProvider. This will result in extra calls to
        // compute_indices. This "over execution" will be addressed in a more
        // general look at events
        this.model.view.compute_indices();
        this.data.constructor(this.model.source, this.model.view);
        // This is obnoxious but there is no better way to programmatically force
        // a re-sort on the existing sorted columns until/if we start using DataView
        if (this.model.sortable) {
            const columns = this.grid.getColumns();
            const sorters = this.grid.getSortColumns().map((x) => ({
                sortCol: {
                    field: columns[this.grid.getColumnIndex(x.columnId)].field,
                },
                sortAsc: x.sortAsc,
            }));
            this.data.sort(sorters);
        }
        this.grid.invalidate();
        this.grid.render();
    }
    updateSelection() {
        if (this._in_selection_update)
            return;
        const { selected } = this.model.source;
        const permuted_indices = selected.indices.map((x) => this.data.index.indexOf(x)).sort();
        this._in_selection_update = true;
        this.grid.setSelectedRows(permuted_indices);
        this._in_selection_update = false;
        // If the selection is not in the current slickgrid viewport, scroll the
        // datatable to start at the row before the first selected row, so that
        // the selection is immediately brought into view. We don't scroll when
        // the selection is already in the viewport so that selecting from the
        // datatable itself does not re-scroll.
        const cur_grid_range = this.grid.getViewport();
        const scroll_index = this.model.get_scroll_index(cur_grid_range, permuted_indices);
        if (scroll_index != null)
            this.grid.scrollRowToTop(scroll_index);
    }
    newIndexColumn() {
        return {
            id: string_1.uniqueId(),
            name: this.model.index_header,
            field: exports.DTINDEX_NAME,
            width: this.model.index_width,
            behavior: "select",
            cannotTriggerInsert: true,
            resizable: false,
            selectable: false,
            sortable: true,
            cssClass: tables_1.bk_cell_index,
            headerCssClass: tables_1.bk_header_index,
        };
    }
    css_classes() {
        return super.css_classes().concat(tables_1.bk_data_table);
    }
    render() {
        let checkboxSelector;
        let columns = this.model.columns.map((column) => column.toColumn());
        if (this.model.selectable == "checkbox") {
            checkboxSelector = new CheckboxSelectColumn({ cssClass: tables_1.bk_cell_select });
            columns.unshift(checkboxSelector.getColumnDefinition());
        }
        if (this.model.index_position != null) {
            const index_position = this.model.index_position;
            const index = this.newIndexColumn();
            // This is to be able to provide negative index behaviour that
            // matches what python users will expect
            if (index_position == -1)
                columns.push(index);
            else if (index_position < -1)
                columns.splice(index_position + 1, 0, index);
            else
                columns.splice(index_position, 0, index);
        }
        let { reorderable } = this.model;
        if (reorderable && !(typeof $ !== "undefined" && $.fn != null && $.fn.sortable != null)) {
            if (!this._warned_not_reorderable) {
                logging_1.logger.warn("jquery-ui is required to enable DataTable.reorderable");
                this._warned_not_reorderable = true;
            }
            reorderable = false;
        }
        const options = {
            enableCellNavigation: this.model.selectable !== false,
            enableColumnReorder: reorderable,
            forceFitColumns: this.model.fit_columns,
            multiColumnSort: this.model.sortable,
            editable: this.model.editable,
            autoEdit: false,
            rowHeight: this.model.row_height,
        };
        this.data = new TableDataProvider(this.model.source, this.model.view);
        this.grid = new slickgrid_1.Grid(this.el, this.data, columns, options);
        this.grid.onSort.subscribe((_event, args) => {
            if (!this.model.sortable)
                return;
            columns = args.sortCols;
            this.data.sort(columns);
            this.grid.invalidate();
            this.updateSelection();
            this.grid.render();
            if (!this.model.header_row) {
                this._hide_header();
            }
            this.model.update_sort_columns(columns);
        });
        if (this.model.selectable !== false) {
            this.grid.setSelectionModel(new RowSelectionModel({ selectActiveRow: checkboxSelector == null }));
            if (checkboxSelector != null)
                this.grid.registerPlugin(checkboxSelector);
            const pluginOptions = {
                dataItemColumnValueExtractor(val, col) {
                    // As defined in this file, Item can contain any type values
                    let value = val[col.field];
                    if (types_1.isString(value)) {
                        value = value.replace(/\n/g, "\\n");
                    }
                    return value;
                },
                includeHeaderWhenCopying: false,
            };
            this.grid.registerPlugin(new CellExternalCopyManager(pluginOptions));
            this.grid.onSelectedRowsChanged.subscribe((_event, args) => {
                if (this._in_selection_update) {
                    return;
                }
                this.model.source.selected.indices = args.rows.map((i) => this.data.index[i]);
            });
            this.updateSelection();
            if (!this.model.header_row) {
                this._hide_header();
            }
        }
    }
    _hide_header() {
        for (const el of Array.from(this.el.querySelectorAll('.slick-header-columns'))) {
            el.style.height = "0px";
        }
        this.grid.resizeCanvas();
    }
}
exports.DataTableView = DataTableView;
DataTableView.__name__ = "DataTableView";
class DataTable extends table_widget_1.TableWidget {
    constructor(attrs) {
        super(attrs);
        this._sort_columns = [];
    }
    get sort_columns() { return this._sort_columns; }
    static init_DataTable() {
        this.prototype.default_view = DataTableView;
        this.define({
            columns: [p.Array, []],
            fit_columns: [p.Boolean, true],
            sortable: [p.Boolean, true],
            reorderable: [p.Boolean, true],
            editable: [p.Boolean, false],
            selectable: [p.Any, true],
            index_position: [p.Int, 0],
            index_header: [p.String, "#"],
            index_width: [p.Int, 40],
            scroll_to_selection: [p.Boolean, true],
            header_row: [p.Boolean, true],
            row_height: [p.Int, 25],
        });
        this.override({
            width: 600,
            height: 400,
        });
    }
    update_sort_columns(sortCols) {
        this._sort_columns = sortCols.map((x) => ({ field: x.sortCol.field, sortAsc: x.sortAsc }));
        return null;
    }
    get_scroll_index(grid_range, selected_indices) {
        if (!this.scroll_to_selection || (selected_indices.length == 0))
            return null;
        if (!array_1.some(selected_indices, i => grid_range.top <= i && i <= grid_range.bottom)) {
            return Math.max(0, Math.min(...selected_indices) - 1);
        }
        return null;
    }
}
exports.DataTable = DataTable;
DataTable.__name__ = "DataTable";
DataTable.init_DataTable();
