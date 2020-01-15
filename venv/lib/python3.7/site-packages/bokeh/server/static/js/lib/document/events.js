"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const has_props_1 = require("../core/has_props");
class DocumentChangedEvent {
    constructor(document) {
        this.document = document;
    }
}
exports.DocumentChangedEvent = DocumentChangedEvent;
DocumentChangedEvent.__name__ = "DocumentChangedEvent";
class ModelChangedEvent extends DocumentChangedEvent {
    constructor(document, model, attr, old, new_, setter_id, hint) {
        super(document);
        this.model = model;
        this.attr = attr;
        this.old = old;
        this.new_ = new_;
        this.setter_id = setter_id;
        this.hint = hint;
    }
    json(references) {
        if (this.attr === "id") {
            throw new Error("'id' field should never change, whatever code just set it is wrong");
        }
        if (this.hint != null)
            return this.hint.json(references);
        const value = this.new_;
        const value_json = has_props_1.HasProps._value_to_json(this.attr, value, this.model);
        const value_refs = {};
        has_props_1.HasProps._value_record_references(value, value_refs, true); // true = recurse
        if (this.model.id in value_refs && this.model !== value) {
            // we know we don't want a whole new copy of the obj we're
            // patching unless it's also the value itself
            delete value_refs[this.model.id];
        }
        for (const id in value_refs) {
            references[id] = value_refs[id];
        }
        return {
            kind: "ModelChanged",
            model: this.model.ref(),
            attr: this.attr,
            new: value_json,
        };
    }
}
exports.ModelChangedEvent = ModelChangedEvent;
ModelChangedEvent.__name__ = "ModelChangedEvent";
class ColumnsPatchedEvent extends DocumentChangedEvent {
    constructor(document, column_source, patches) {
        super(document);
        this.column_source = column_source;
        this.patches = patches;
    }
    json(_references) {
        return {
            kind: "ColumnsPatched",
            column_source: this.column_source,
            patches: this.patches,
        };
    }
}
exports.ColumnsPatchedEvent = ColumnsPatchedEvent;
ColumnsPatchedEvent.__name__ = "ColumnsPatchedEvent";
class ColumnsStreamedEvent extends DocumentChangedEvent {
    constructor(document, column_source, data, rollover) {
        super(document);
        this.column_source = column_source;
        this.data = data;
        this.rollover = rollover;
    }
    json(_references) {
        return {
            kind: "ColumnsStreamed",
            column_source: this.column_source,
            data: this.data,
            rollover: this.rollover,
        };
    }
}
exports.ColumnsStreamedEvent = ColumnsStreamedEvent;
ColumnsStreamedEvent.__name__ = "ColumnsStreamedEvent";
class TitleChangedEvent extends DocumentChangedEvent {
    constructor(document, title, setter_id) {
        super(document);
        this.title = title;
        this.setter_id = setter_id;
    }
    json(_references) {
        return {
            kind: "TitleChanged",
            title: this.title,
        };
    }
}
exports.TitleChangedEvent = TitleChangedEvent;
TitleChangedEvent.__name__ = "TitleChangedEvent";
class RootAddedEvent extends DocumentChangedEvent {
    constructor(document, model, setter_id) {
        super(document);
        this.model = model;
        this.setter_id = setter_id;
    }
    json(references) {
        has_props_1.HasProps._value_record_references(this.model, references, true);
        return {
            kind: "RootAdded",
            model: this.model.ref(),
        };
    }
}
exports.RootAddedEvent = RootAddedEvent;
RootAddedEvent.__name__ = "RootAddedEvent";
class RootRemovedEvent extends DocumentChangedEvent {
    constructor(document, model, setter_id) {
        super(document);
        this.model = model;
        this.setter_id = setter_id;
    }
    json(_references) {
        return {
            kind: "RootRemoved",
            model: this.model.ref(),
        };
    }
}
exports.RootRemovedEvent = RootRemovedEvent;
RootRemovedEvent.__name__ = "RootRemovedEvent";
