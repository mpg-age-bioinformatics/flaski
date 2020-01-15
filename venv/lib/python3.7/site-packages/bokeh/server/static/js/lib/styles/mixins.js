"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const _a = require("../core/dom");
_a.styles.append("");
exports.bk_active = "bk-active";
exports.bk_inline = "bk-inline";
exports.bk_left = "bk-left";
exports.bk_right = "bk-right";
exports.bk_above = "bk-above";
exports.bk_below = "bk-below";
exports.bk_up = "bk-up";
exports.bk_down = "bk-down";
function bk_side(side) {
    switch (side) {
        case "above": return exports.bk_above;
        case "below": return exports.bk_below;
        case "left": return exports.bk_left;
        case "right": return exports.bk_right;
    }
}
exports.bk_side = bk_side;
