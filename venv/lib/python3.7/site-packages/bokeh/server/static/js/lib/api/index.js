"use strict";
function __export(m) {
    for (var p in m) if (!exports.hasOwnProperty(p)) exports[p] = m[p];
}
Object.defineProperty(exports, "__esModule", { value: true });
const LinAlg = require("./linalg");
exports.LinAlg = LinAlg;
const Charts = require("./charts");
exports.Charts = Charts;
const Plotting = require("./plotting");
exports.Plotting = Plotting;
var document_1 = require("../document");
exports.Document = document_1.Document;
var templating_1 = require("../core/util/templating");
exports.sprintf = templating_1.sprintf;
__export(require("./models"));
