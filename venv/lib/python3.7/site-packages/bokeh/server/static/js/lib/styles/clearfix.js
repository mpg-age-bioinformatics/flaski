"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
require("./root");
const _a = require("../core/dom");
_a.styles.append(".bk-root .bk-clearfix:before,\n.bk-root .bk-clearfix:after {\n  content: \"\";\n  display: table;\n}\n.bk-root .bk-clearfix:after {\n  clear: both;\n}\n");
exports.bk_clearfix = "bk-clearfix";
