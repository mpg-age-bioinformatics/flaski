"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const ts = require("typescript");
const crypto = require("crypto");
const path_1 = require("path");
function scan(path, extensions, exclude, include, depth) {
    return ts.sys.readDirectory(path, extensions, exclude, include, depth).map((p) => path_1.normalize(p));
}
exports.scan = scan;
function glob(...patterns) {
    return scan(".", undefined, undefined, patterns);
}
exports.glob = glob;
exports.read = ts.sys.readFile;
exports.write = ts.sys.writeFile;
exports.file_exists = ts.sys.fileExists;
exports.directory_exists = ts.sys.directoryExists;
function rename(path, options) {
    let { dir, name, ext } = path_1.parse(path);
    if (options.dir != null) {
        if (options.base != null)
            dir = dir.replace(options.base, options.dir);
        else
            dir = options.dir;
    }
    if (options.name != null)
        name = options.name(name);
    if (options.ext != null)
        ext = options.ext;
    return path_1.format({ dir, name, ext });
}
exports.rename = rename;
function hash(data) {
    return crypto.createHash("sha256").update(data).digest("hex");
}
exports.hash = hash;
function hash_file(path) {
    const contents = exports.read(path);
    return contents != null ? hash(contents) : null;
}
exports.hash_file = hash_file;
function read_json(path) {
    const data = exports.read(path);
    if (data == null)
        return undefined;
    else {
        try {
            return JSON.parse(data);
        }
        catch (_a) {
            return undefined;
        }
    }
}
exports.read_json = read_json;
//# sourceMappingURL=sys.js.map