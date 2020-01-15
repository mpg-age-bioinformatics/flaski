"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const p = require("../../../core/properties");
const dom_1 = require("../../../core/dom");
const dom_view_1 = require("../../../core/dom_view");
const model_1 = require("../../../model");
const data_table_1 = require("./data_table");
const tables_1 = require("../../../styles/widgets/tables");
class CellEditorView extends dom_view_1.DOMView {
    constructor(options) {
        super(Object.assign({ model: options.column.model }, options));
        this.args = options;
        this.render(); // XXX: this isn't governed by layout
    }
    get emptyValue() {
        return null;
    }
    initialize() {
        super.initialize();
        this.inputEl = this._createInput();
        this.defaultValue = null;
    }
    css_classes() {
        return super.css_classes().concat(tables_1.bk_cell_editor);
    }
    render() {
        super.render();
        this.args.container.append(this.el);
        this.el.appendChild(this.inputEl);
        this.renderEditor();
        this.disableNavigation();
    }
    renderEditor() { }
    disableNavigation() {
        this.inputEl.addEventListener("keydown", (event) => {
            switch (event.keyCode) {
                case dom_1.Keys.Left:
                case dom_1.Keys.Right:
                case dom_1.Keys.Up:
                case dom_1.Keys.Down:
                case dom_1.Keys.PageUp:
                case dom_1.Keys.PageDown:
                    event.stopImmediatePropagation();
            }
        });
    }
    destroy() {
        this.remove();
    }
    focus() {
        this.inputEl.focus();
    }
    show() { }
    hide() { }
    position() { }
    getValue() {
        return this.inputEl.value;
    }
    setValue(val) {
        this.inputEl.value = val;
    }
    serializeValue() {
        return this.getValue();
    }
    isValueChanged() {
        return !(this.getValue() == "" && this.defaultValue == null) && this.getValue() !== this.defaultValue;
    }
    applyValue(item, state) {
        const grid_data = this.args.grid.getData();
        const offset = grid_data.index.indexOf(item[data_table_1.DTINDEX_NAME]);
        grid_data.setField(offset, this.args.column.field, state);
    }
    loadValue(item) {
        const value = item[this.args.column.field];
        this.defaultValue = value != null ? value : this.emptyValue;
        this.setValue(this.defaultValue);
    }
    validateValue(value) {
        if (this.args.column.validator) {
            const result = this.args.column.validator(value);
            if (!result.valid) {
                return result;
            }
        }
        return { valid: true, msg: null };
    }
    validate() {
        return this.validateValue(this.getValue());
    }
}
exports.CellEditorView = CellEditorView;
CellEditorView.__name__ = "CellEditorView";
class CellEditor extends model_1.Model {
}
exports.CellEditor = CellEditor;
CellEditor.__name__ = "CellEditor";
class StringEditorView extends CellEditorView {
    get emptyValue() {
        return "";
    }
    _createInput() {
        return dom_1.input({ type: "text" });
    }
    renderEditor() {
        //completions = @model.completions
        //if completions.length != 0
        //  @inputEl.classList.add("bk-cell-editor-completion")
        //  $(@inputEl).autocomplete({source: completions})
        //  $(@inputEl).autocomplete("widget")
        this.inputEl.focus();
        this.inputEl.select();
    }
    loadValue(item) {
        super.loadValue(item);
        this.inputEl.defaultValue = this.defaultValue;
        this.inputEl.select();
    }
}
exports.StringEditorView = StringEditorView;
StringEditorView.__name__ = "StringEditorView";
class StringEditor extends CellEditor {
    static init_StringEditor() {
        this.prototype.default_view = StringEditorView;
        this.define({
            completions: [p.Array, []],
        });
    }
}
exports.StringEditor = StringEditor;
StringEditor.__name__ = "StringEditor";
StringEditor.init_StringEditor();
class TextEditorView extends CellEditorView {
    _createInput() {
        return dom_1.textarea();
    }
}
exports.TextEditorView = TextEditorView;
TextEditorView.__name__ = "TextEditorView";
class TextEditor extends CellEditor {
    static init_TextEditor() {
        this.prototype.default_view = TextEditorView;
    }
}
exports.TextEditor = TextEditor;
TextEditor.__name__ = "TextEditor";
TextEditor.init_TextEditor();
class SelectEditorView extends CellEditorView {
    _createInput() {
        return dom_1.select();
    }
    renderEditor() {
        for (const opt of this.model.options) {
            this.inputEl.appendChild(dom_1.option({ value: opt }, opt));
        }
        this.focus();
    }
}
exports.SelectEditorView = SelectEditorView;
SelectEditorView.__name__ = "SelectEditorView";
class SelectEditor extends CellEditor {
    static init_SelectEditor() {
        this.prototype.default_view = SelectEditorView;
        this.define({
            options: [p.Array, []],
        });
    }
}
exports.SelectEditor = SelectEditor;
SelectEditor.__name__ = "SelectEditor";
SelectEditor.init_SelectEditor();
class PercentEditorView extends CellEditorView {
    _createInput() {
        return dom_1.input({ type: "text" });
    }
}
exports.PercentEditorView = PercentEditorView;
PercentEditorView.__name__ = "PercentEditorView";
class PercentEditor extends CellEditor {
    static init_PercentEditor() {
        this.prototype.default_view = PercentEditorView;
    }
}
exports.PercentEditor = PercentEditor;
PercentEditor.__name__ = "PercentEditor";
PercentEditor.init_PercentEditor();
class CheckboxEditorView extends CellEditorView {
    _createInput() {
        return dom_1.input({ type: "checkbox", value: "true" });
    }
    renderEditor() {
        this.focus();
    }
    loadValue(item) {
        this.defaultValue = !!item[this.args.column.field];
        this.inputEl.checked = this.defaultValue;
    }
    serializeValue() {
        return this.inputEl.checked;
    }
}
exports.CheckboxEditorView = CheckboxEditorView;
CheckboxEditorView.__name__ = "CheckboxEditorView";
class CheckboxEditor extends CellEditor {
    static init_CheckboxEditor() {
        this.prototype.default_view = CheckboxEditorView;
    }
}
exports.CheckboxEditor = CheckboxEditor;
CheckboxEditor.__name__ = "CheckboxEditor";
CheckboxEditor.init_CheckboxEditor();
class IntEditorView extends CellEditorView {
    _createInput() {
        return dom_1.input({ type: "text" });
    }
    renderEditor() {
        //$(@inputEl).spinner({step: @model.step})
        this.inputEl.focus();
        this.inputEl.select();
    }
    remove() {
        //$(@inputEl).spinner("destroy")
        super.remove();
    }
    serializeValue() {
        return parseInt(this.getValue(), 10) || 0;
    }
    loadValue(item) {
        super.loadValue(item);
        this.inputEl.defaultValue = this.defaultValue;
        this.inputEl.select();
    }
    validateValue(value) {
        if (isNaN(value))
            return { valid: false, msg: "Please enter a valid integer" };
        else
            return super.validateValue(value);
    }
}
exports.IntEditorView = IntEditorView;
IntEditorView.__name__ = "IntEditorView";
class IntEditor extends CellEditor {
    static init_IntEditor() {
        this.prototype.default_view = IntEditorView;
        this.define({
            step: [p.Number, 1],
        });
    }
}
exports.IntEditor = IntEditor;
IntEditor.__name__ = "IntEditor";
IntEditor.init_IntEditor();
class NumberEditorView extends CellEditorView {
    _createInput() {
        return dom_1.input({ type: "text" });
    }
    renderEditor() {
        //$(@inputEl).spinner({step: @model.step})
        this.inputEl.focus();
        this.inputEl.select();
    }
    remove() {
        //$(@inputEl).spinner("destroy")
        super.remove();
    }
    serializeValue() {
        return parseFloat(this.getValue()) || 0.0;
    }
    loadValue(item) {
        super.loadValue(item);
        this.inputEl.defaultValue = this.defaultValue;
        this.inputEl.select();
    }
    validateValue(value) {
        if (isNaN(value))
            return { valid: false, msg: "Please enter a valid number" };
        else
            return super.validateValue(value);
    }
}
exports.NumberEditorView = NumberEditorView;
NumberEditorView.__name__ = "NumberEditorView";
class NumberEditor extends CellEditor {
    static init_NumberEditor() {
        this.prototype.default_view = NumberEditorView;
        this.define({
            step: [p.Number, 0.01],
        });
    }
}
exports.NumberEditor = NumberEditor;
NumberEditor.__name__ = "NumberEditor";
NumberEditor.init_NumberEditor();
class TimeEditorView extends CellEditorView {
    _createInput() {
        return dom_1.input({ type: "text" });
    }
}
exports.TimeEditorView = TimeEditorView;
TimeEditorView.__name__ = "TimeEditorView";
class TimeEditor extends CellEditor {
    static init_TimeEditor() {
        this.prototype.default_view = TimeEditorView;
    }
}
exports.TimeEditor = TimeEditor;
TimeEditor.__name__ = "TimeEditor";
TimeEditor.init_TimeEditor();
class DateEditorView extends CellEditorView {
    _createInput() {
        return dom_1.input({ type: "text" });
    }
    get emptyValue() {
        return new Date();
    }
    renderEditor() {
        //this.calendarOpen = false
        //@$datepicker = $(@inputEl).datepicker({
        //  showOn: "button"
        //  buttonImageOnly: true
        //  beforeShow: () => @calendarOpen = true
        //  onClose: () => @calendarOpen = false
        //})
        //@$datepicker.siblings(".ui-datepicker-trigger").css("vertical-align": "middle")
        //@$datepicker.width(@$datepicker.width() - (14 + 2*4 + 4)) # img width + margins + edge distance
        this.inputEl.focus();
        this.inputEl.select();
    }
    destroy() {
        //$.datepicker.dpDiv.stop(true, true)
        //@$datepicker.datepicker("hide")
        //@$datepicker.datepicker("destroy")
        super.destroy();
    }
    show() {
        //if @calendarOpen
        //  $.datepicker.dpDiv.stop(true, true).show()
        super.show();
    }
    hide() {
        //if @calendarOpen
        //  $.datepicker.dpDiv.stop(true, true).hide()
        super.hide();
    }
    position( /*_position*/) {
        //if @calendarOpen
        //  $.datepicker.dpDiv.css(top: position.top + 30, left: position.left)
        return super.position();
    }
    getValue() {
        //return @$datepicker.datepicker("getDate").getTime()
    }
    setValue(_val) {
        //@$datepicker.datepicker("setDate", new Date(val))
    }
}
exports.DateEditorView = DateEditorView;
DateEditorView.__name__ = "DateEditorView";
class DateEditor extends CellEditor {
    static init_DateEditor() {
        this.prototype.default_view = DateEditorView;
    }
}
exports.DateEditor = DateEditor;
DateEditor.__name__ = "DateEditor";
DateEditor.init_DateEditor();
