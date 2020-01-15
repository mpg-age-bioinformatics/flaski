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
Object.defineProperty(exports, "__esModule", { value: true });
const path = require("path");
const ts = require("typescript");
const coffee = require("coffeescript");
const lesscss = require("less");
const compiler_1 = require("./compiler");
const sys_1 = require("./sys");
const transforms = require("./transforms");
const tsconfig_json = require("./tsconfig.ext.json");
function compile_typescript(base_dir, inputs, bokehjs_dir) {
    const preconfigure = {
        paths: {
            "*": [
                path.join(bokehjs_dir, "js/lib/*"),
                path.join(bokehjs_dir, "js/types/*"),
            ],
        },
        outDir: undefined,
    };
    // XXX: silence the config validator. We are providing inputs through `inputs` argument anyway.
    const json = Object.assign(Object.assign({}, tsconfig_json), { include: undefined, files: ["dummy.ts"] });
    const tsconfig = compiler_1.parse_tsconfig(json, base_dir, preconfigure);
    if (tsconfig.diagnostics != null)
        return { diagnostics: tsconfig.diagnostics };
    const host = compiler_1.compiler_host(inputs, tsconfig.options, bokehjs_dir);
    const transformers = compiler_1.default_transformers(tsconfig.options);
    const outputs = new Map();
    host.writeFile = (name, data) => {
        outputs.set(name, data);
    };
    const files = [...inputs.keys()];
    return Object.assign({ outputs }, compiler_1.compile_files(files, tsconfig.options, transformers, host));
}
exports.compile_typescript = compile_typescript;
function compile_javascript(file, code) {
    const result = ts.transpileModule(code, {
        fileName: file,
        reportDiagnostics: true,
        compilerOptions: {
            target: ts.ScriptTarget.ES5,
            module: ts.ModuleKind.CommonJS,
        },
    });
    const format_host = {
        getCanonicalFileName: (path) => path,
        getCurrentDirectory: ts.sys.getCurrentDirectory,
        getNewLine: () => ts.sys.newLine,
    };
    const { outputText, diagnostics } = result;
    if (diagnostics == null || diagnostics.length == 0)
        return { output: outputText };
    else {
        const error = ts.formatDiagnosticsWithColorAndContext(ts.sortAndDeduplicateDiagnostics(diagnostics), format_host);
        return { output: outputText, error };
    }
}
function normalize(path) {
    return path.replace(/\\/g, "/");
}
function compile_and_resolve_deps(input) {
    return __awaiter(this, void 0, void 0, function* () {
        const { file, lang, bokehjs_dir } = input;
        let { code } = input;
        let output;
        switch (lang) {
            case "typescript":
                const inputs = new Map([[normalize(file), code]]);
                const { outputs, diagnostics } = compile_typescript(".", inputs, bokehjs_dir);
                if (diagnostics != null && diagnostics.length != 0) {
                    const failure = compiler_1.report_diagnostics(diagnostics);
                    return { error: failure.text };
                }
                else {
                    const js_file = normalize(sys_1.rename(file, { ext: ".js" }));
                    output = outputs.get(js_file);
                }
                break;
            case "coffeescript":
                try {
                    code = coffee.compile(code, { bare: true, shiftLine: true });
                }
                catch (error) {
                    return { error: error.toString() };
                }
            case "javascript": {
                const result = compile_javascript(file, code);
                if (result.error == null)
                    output = result.output;
                else
                    return { error: result.error };
                break;
            }
            case "less":
                try {
                    const { css } = yield lesscss.render(code, { filename: file, compress: true });
                    return { code: css };
                }
                catch (error) {
                    return { error: error.toString() };
                }
            default:
                throw new Error(`unsupported input type: ${lang}`);
        }
        const source = ts.createSourceFile(file, output, ts.ScriptTarget.ES5, true, ts.ScriptKind.JS);
        const deps = transforms.collect_deps(source);
        return { code: output, deps };
    });
}
exports.compile_and_resolve_deps = compile_and_resolve_deps;
//# sourceMappingURL=compile.js.map