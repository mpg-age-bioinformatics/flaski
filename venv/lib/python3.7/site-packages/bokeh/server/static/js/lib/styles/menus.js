"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
require("./root");
const _a = require("../core/dom");
_a.styles.append(".bk-root .bk-menu {\n  position: absolute;\n  left: 0;\n  width: 100%;\n  z-index: 100;\n  cursor: pointer;\n  font-size: 12px;\n  background-color: #fff;\n  border: 1px solid #ccc;\n  border-radius: 4px;\n  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.175);\n}\n.bk-root .bk-menu.bk-above {\n  bottom: 100%;\n}\n.bk-root .bk-menu.bk-below {\n  top: 100%;\n}\n.bk-root .bk-menu > .bk-divider {\n  height: 1px;\n  margin: 7.5px 0;\n  overflow: hidden;\n  background-color: #e5e5e5;\n}\n.bk-root .bk-menu > :not(.bk-divider) {\n  padding: 6px 12px;\n}\n.bk-root .bk-menu > :not(.bk-divider):hover,\n.bk-root .bk-menu > :not(.bk-divider).bk-active {\n  background-color: #e6e6e6;\n}\n.bk-root .bk-caret {\n  display: inline-block;\n  vertical-align: middle;\n  width: 0;\n  height: 0;\n  margin: 0 5px;\n}\n.bk-root .bk-caret.bk-down {\n  border-top: 4px solid;\n}\n.bk-root .bk-caret.bk-up {\n  border-bottom: 4px solid;\n}\n.bk-root .bk-caret.bk-down,\n.bk-root .bk-caret.bk-up {\n  border-right: 4px solid transparent;\n  border-left: 4px solid transparent;\n}\n.bk-root .bk-caret.bk-left {\n  border-right: 4px solid;\n}\n.bk-root .bk-caret.bk-right {\n  border-left: 4px solid;\n}\n.bk-root .bk-caret.bk-left,\n.bk-root .bk-caret.bk-right {\n  border-top: 4px solid transparent;\n  border-bottom: 4px solid transparent;\n}\n");
exports.bk_menu = "bk-menu";
exports.bk_caret = "bk-caret";
exports.bk_divider = "bk-divider";
