"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
require("./root");
const _a = require("../core/dom");
_a.styles.append("/* notebook specific tweaks so no black outline and matching padding\n/* can't be wrapped inside bk-root. here are the offending jupyter lines:\n/* https://github.com/jupyter/notebook/blob/master/notebook/static/notebook/less/renderedhtml.less#L59-L76 */\n.rendered_html .bk-root .bk-tooltip table,\n.rendered_html .bk-root .bk-tooltip tr,\n.rendered_html .bk-root .bk-tooltip th,\n.rendered_html .bk-root .bk-tooltip td {\n  border: none;\n  padding: 1px;\n}\n");
