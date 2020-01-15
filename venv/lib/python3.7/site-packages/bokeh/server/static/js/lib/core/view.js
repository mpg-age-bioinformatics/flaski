"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const signaling_1 = require("./signaling");
const types_1 = require("./util/types");
const string_1 = require("./util/string");
class View extends signaling_1.Signalable() {
    constructor(options) {
        super();
        this.removed = new signaling_1.Signal0(this, "removed");
        if (options.model != null)
            this.model = options.model;
        else
            throw new Error("model of a view wasn't configured");
        this._parent = options.parent;
        this.id = options.id || string_1.uniqueId();
        this.initialize();
        if (options.connect_signals !== false)
            this.connect_signals();
    }
    initialize() { }
    remove() {
        this._parent = undefined;
        this.disconnect_signals();
        this.removed.emit();
    }
    toString() {
        return `${this.model.type}View(${this.id})`;
    }
    serializable_state() {
        return { type: this.model.type };
    }
    get parent() {
        if (this._parent !== undefined)
            return this._parent;
        else
            throw new Error("parent of a view wasn't configured");
    }
    get is_root() {
        return this.parent === null;
    }
    get root() {
        return this.is_root ? this : this.parent.root;
    }
    assert_root() {
        if (!this.is_root)
            throw new Error(`${this.toString()} is not a root layout`);
    }
    connect_signals() { }
    disconnect_signals() {
        signaling_1.Signal.disconnectReceiver(this);
    }
    on_change(properties, fn) {
        for (const property of types_1.isArray(properties) ? properties : [properties])
            this.connect(property.change, fn);
    }
}
exports.View = View;
View.__name__ = "View";
