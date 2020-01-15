"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const model_1 = require("../../model");
const columnar_data_source_1 = require("../sources/columnar_data_source");
const vectorization_1 = require("../../core/vectorization");
const p = require("../../core/properties");
const logging_1 = require("../../core/logging");
const array_1 = require("../../core/util/array");
class LegendItem extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_LegendItem() {
        this.define({
            label: [p.StringSpec, null],
            renderers: [p.Array, []],
            index: [p.Number, null],
        });
    }
    /*protected*/ _check_data_sources_on_renderers() {
        const field = this.get_field_from_label_prop();
        if (field != null) {
            if (this.renderers.length < 1) {
                return false;
            }
            const source = this.renderers[0].data_source;
            if (source != null) {
                for (const r of this.renderers) {
                    if (r.data_source != source) {
                        return false;
                    }
                }
            }
        }
        return true;
    }
    /*protected*/ _check_field_label_on_data_source() {
        const field = this.get_field_from_label_prop();
        if (field != null) {
            if (this.renderers.length < 1) {
                return false;
            }
            const source = this.renderers[0].data_source;
            if (source != null && !array_1.includes(source.columns(), field)) {
                return false;
            }
        }
        return true;
    }
    initialize() {
        super.initialize();
        this.legend = null;
        this.connect(this.change, () => { if (this.legend != null)
            this.legend.item_change.emit(); });
        // Validate data_sources match
        const data_source_validation = this._check_data_sources_on_renderers();
        if (!data_source_validation)
            logging_1.logger.error("Non matching data sources on legend item renderers");
        // Validate label in data_source
        const field_validation = this._check_field_label_on_data_source();
        if (!field_validation)
            logging_1.logger.error(`Bad column name on label: ${this.label}`);
    }
    get_field_from_label_prop() {
        const { label } = this;
        return vectorization_1.isField(label) ? label.field : null;
    }
    get_labels_list_from_label_prop() {
        // Always return a list of the labels
        if (vectorization_1.isValue(this.label)) {
            const { value } = this.label;
            return value != null ? [value] : [];
        }
        const field = this.get_field_from_label_prop();
        if (field != null) {
            let source;
            if (this.renderers[0] && this.renderers[0].data_source != null)
                source = this.renderers[0].data_source;
            else
                return ["No source found"];
            if (source instanceof columnar_data_source_1.ColumnarDataSource) {
                const data = source.get_column(field);
                if (data != null)
                    return array_1.uniq(Array.from(data));
                else
                    return ["Invalid field"];
            }
        }
        return [];
    }
}
exports.LegendItem = LegendItem;
LegendItem.__name__ = "LegendItem";
LegendItem.init_LegendItem();
