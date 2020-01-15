"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __asyncValues = (this && this.__asyncValues) || function (o) {
    if (!Symbol.asyncIterator) throw new TypeError("Symbol.asyncIterator is not defined.");
    var m = o[Symbol.asyncIterator], i;
    return m ? m.call(o) : (o = typeof __values === "function" ? __values(o) : o[Symbol.iterator](), i = {}, verb("next"), verb("throw"), verb("return"), i[Symbol.asyncIterator] = function () { return this; }, i);
    function verb(n) { i[n] = o[n] && function (v) { return new Promise(function (resolve, reject) { v = o[n](v), settle(resolve, reject, v.done, v.value); }); }; }
    function settle(resolve, reject, d, v) { Promise.resolve(v).then(function(v) { resolve({ value: v, done: d }); }, reject); }
};
Object.defineProperty(exports, "__esModule", { value: true });
const yargs_1 = require("yargs");
const path_1 = require("path");
const sys_1 = require("./sys");
const build_1 = require("./build");
const compile_1 = require("./compile");
function read_stdin() {
    var e_1, _a;
    return __awaiter(this, void 0, void 0, function* () {
        const stdin = process.stdin;
        stdin.setEncoding("utf-8");
        stdin.resume();
        let data = "";
        try {
            for (var stdin_1 = __asyncValues(stdin), stdin_1_1; stdin_1_1 = yield stdin_1.next(), !stdin_1_1.done;) {
                const chunk = stdin_1_1.value;
                data += chunk;
            }
        }
        catch (e_1_1) { e_1 = { error: e_1_1 }; }
        finally {
            try {
                if (stdin_1_1 && !stdin_1_1.done && (_a = stdin_1.return)) yield _a.call(stdin_1);
            }
            finally { if (e_1) throw e_1.error; }
        }
        return data;
    });
}
function reply(data) {
    process.stdout.write(JSON.stringify(data));
    process.stdout.write("\n");
}
function compile() {
    return __awaiter(this, void 0, void 0, function* () {
        if (yargs_1.argv.file != null) {
            const input = {
                code: yargs_1.argv.code != null ? yargs_1.argv.code : sys_1.read(yargs_1.argv.file),
                lang: yargs_1.argv.lang || "coffeescript",
                file: yargs_1.argv.file,
                bokehjs_dir: yargs_1.argv.bokehjsDir || "./build",
            };
            return yield compile_1.compile_and_resolve_deps(input);
        }
        else {
            const input = JSON.parse(yield read_stdin());
            return yield compile_1.compile_and_resolve_deps(input);
        }
    });
}
function main() {
    return __awaiter(this, void 0, void 0, function* () {
        const cmd = yargs_1.argv._[0];
        if (cmd == "build") {
            try {
                const base_dir = path_1.resolve(yargs_1.argv.baseDir);
                const bokehjs_dir = path_1.resolve(yargs_1.argv.bokehjsDir);
                const rebuild = yargs_1.argv.rebuild;
                const bokeh_version = yargs_1.argv.bokehVersion;
                const result = yield build_1.build(base_dir, bokehjs_dir, { rebuild, bokeh_version });
                process.exit(result ? 0 : 1);
            }
            catch (error) {
                console.log(error.stack);
                process.exit(1);
            }
        }
        else if (cmd == "init") {
            try {
                const base_dir = path_1.resolve(yargs_1.argv.baseDir);
                const bokehjs_dir = path_1.resolve(yargs_1.argv.bokehjsDir);
                const interactive = yargs_1.argv.interactive;
                const bokehjs_version = yargs_1.argv.bokehjsVersion;
                const bokeh_version = yargs_1.argv.bokehVersion;
                const result = yield build_1.init(base_dir, bokehjs_dir, { interactive, bokehjs_version, bokeh_version });
                process.exit(result ? 0 : 1);
            }
            catch (error) {
                console.log(error.stack);
                process.exit(1);
            }
        }
        else {
            try {
                reply(yield compile());
            }
            catch (error) {
                reply({ error: error.stack });
            }
        }
    });
}
main();
//# sourceMappingURL=main.js.map