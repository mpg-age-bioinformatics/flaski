"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Numbro = require("numbro");
const compile_template = require("underscore.template");
const tz = require("timezone");
const p = require("../../../core/properties");
const dom_1 = require("../../../core/dom");
const types_1 = require("../../../core/util/types");
const model_1 = require("../../../model");
class CellFormatter extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    doFormat(_row, _cell, value, _columnDef, _dataContext) {
        if (value == null)
            return "";
        else
            return (value + "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }
}
exports.CellFormatter = CellFormatter;
CellFormatter.__name__ = "CellFormatter";
class StringFormatter extends CellFormatter {
    constructor(attrs) {
        super(attrs);
    }
    static init_StringFormatter() {
        this.define({
            font_style: [p.FontStyle, "normal"],
            text_align: [p.TextAlign, "left"],
            text_color: [p.Color],
        });
    }
    doFormat(_row, _cell, value, _columnDef, _dataContext) {
        const { font_style, text_align, text_color } = this;
        const text = dom_1.div({}, value == null ? "" : `${value}`);
        switch (font_style) {
            case "bold":
                text.style.fontWeight = "bold";
                break;
            case "italic":
                text.style.fontStyle = "italic";
                break;
        }
        if (text_align != null)
            text.style.textAlign = text_align;
        if (text_color != null)
            text.style.color = text_color;
        return text.outerHTML;
    }
}
exports.StringFormatter = StringFormatter;
StringFormatter.__name__ = "StringFormatter";
StringFormatter.init_StringFormatter();
class NumberFormatter extends StringFormatter {
    constructor(attrs) {
        super(attrs);
    }
    static init_NumberFormatter() {
        this.define({
            format: [p.String, '0,0'],
            language: [p.String, 'en'],
            rounding: [p.RoundingFunction, 'round'],
        });
    }
    doFormat(row, cell, value, columnDef, dataContext) {
        const { format, language } = this;
        const rounding = (() => {
            switch (this.rounding) {
                case "round":
                case "nearest": return Math.round;
                case "floor":
                case "rounddown": return Math.floor;
                case "ceil":
                case "roundup": return Math.ceil;
            }
        })();
        value = Numbro.format(value, format, language, rounding);
        return super.doFormat(row, cell, value, columnDef, dataContext);
    }
}
exports.NumberFormatter = NumberFormatter;
NumberFormatter.__name__ = "NumberFormatter";
NumberFormatter.init_NumberFormatter();
class BooleanFormatter extends CellFormatter {
    constructor(attrs) {
        super(attrs);
    }
    static init_BooleanFormatter() {
        this.define({
            icon: [p.String, 'check'],
        });
    }
    doFormat(_row, _cell, value, _columnDef, _dataContext) {
        return !!value ? dom_1.i({ class: this.icon }).outerHTML : "";
    }
}
exports.BooleanFormatter = BooleanFormatter;
BooleanFormatter.__name__ = "BooleanFormatter";
BooleanFormatter.init_BooleanFormatter();
class DateFormatter extends CellFormatter {
    constructor(attrs) {
        super(attrs);
    }
    static init_DateFormatter() {
        this.define({
            format: [p.String, 'ISO-8601'],
        });
    }
    getFormat() {
        // using definitions provided here: https://api.jqueryui.com/datepicker/
        // except not implementing TICKS
        switch (this.format) {
            case "ATOM":
            case "W3C":
            case "RFC-3339":
            case "ISO-8601":
                return "%Y-%m-%d";
            case "COOKIE":
                return "%a, %d %b %Y";
            case "RFC-850":
                return "%A, %d-%b-%y";
            case "RFC-1123":
            case "RFC-2822":
                return "%a, %e %b %Y";
            case "RSS":
            case "RFC-822":
            case "RFC-1036":
                return "%a, %e %b %y";
            case "TIMESTAMP":
                return undefined;
            default:
                return this.format;
        }
    }
    doFormat(row, cell, value, columnDef, dataContext) {
        value = types_1.isString(value) ? parseInt(value, 10) : value;
        const date = tz(value, this.getFormat());
        return super.doFormat(row, cell, date, columnDef, dataContext);
    }
}
exports.DateFormatter = DateFormatter;
DateFormatter.__name__ = "DateFormatter";
DateFormatter.init_DateFormatter();
class HTMLTemplateFormatter extends CellFormatter {
    constructor(attrs) {
        super(attrs);
    }
    static init_HTMLTemplateFormatter() {
        this.define({
            template: [p.String, '<%= value %>'],
        });
    }
    doFormat(_row, _cell, value, _columnDef, dataContext) {
        const { template } = this;
        if (value == null)
            return "";
        else {
            const compiled_template = compile_template(template);
            const context = Object.assign(Object.assign({}, dataContext), { value });
            return compiled_template(context);
        }
    }
}
exports.HTMLTemplateFormatter = HTMLTemplateFormatter;
HTMLTemplateFormatter.__name__ = "HTMLTemplateFormatter";
HTMLTemplateFormatter.init_HTMLTemplateFormatter();
