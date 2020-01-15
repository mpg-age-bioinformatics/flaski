"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
class Settings {
    constructor() {
        this._dev = false;
    }
    set dev(dev) {
        this._dev = dev;
    }
    get dev() {
        return this._dev;
    }
}
exports.Settings = Settings;
Settings.__name__ = "Settings";
exports.settings = new Settings();
