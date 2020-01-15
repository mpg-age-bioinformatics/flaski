"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const cell_formatters_1 = require("./cell_formatters");
const cell_editors_1 = require("./cell_editors");
const p = require("../../../core/properties");
const string_1 = require("../../../core/util/string");
const model_1 = require("../../../model");
class TableColumn extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_TableColumn() {
        this.define({
            field: [p.String],
            title: [p.String],
            width: [p.Number, 300],
            formatter: [p.Instance, () => new cell_formatters_1.StringFormatter()],
            editor: [p.Instance, () => new cell_editors_1.StringEditor()],
            sortable: [p.Boolean, true],
            default_sort: [p.Sort, "ascending"],
        });
    }
    toColumn() {
        return {
            id: string_1.uniqueId(),
            field: this.field,
            name: this.title,
            width: this.width,
            formatter: this.formatter != null ? this.formatter.doFormat.bind(this.formatter) : undefined,
            model: this.editor,
            editor: this.editor.default_view,
            sortable: this.sortable,
            defaultSortAsc: this.default_sort == "ascending",
        };
    }
}
exports.TableColumn = TableColumn;
TableColumn.__name__ = "TableColumn";
TableColumn.init_TableColumn();
