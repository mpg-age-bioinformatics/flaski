"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const ts = require("typescript");
function apply(node, ...transforms) {
    const result = ts.transform(node, transforms);
    return result.transformed[0];
}
exports.apply = apply;
function is_require(node) {
    return ts.isCallExpression(node) &&
        ts.isIdentifier(node.expression) &&
        node.expression.text === "require" &&
        node.arguments.length === 1;
}
function relativize_modules(relativize) {
    function relativize_specifier(source, expr) {
        if (expr != null && ts.isStringLiteralLike(expr) && expr.text.length > 0) {
            const relative = relativize(source.fileName, expr.text);
            if (relative != null)
                return ts.createLiteral(relative);
        }
        return null;
    }
    return (context) => (root) => {
        function visit(node) {
            if (ts.isImportDeclaration(node)) {
                const moduleSpecifier = relativize_specifier(root, node.moduleSpecifier);
                if (moduleSpecifier != null) {
                    const { decorators, modifiers, importClause } = node;
                    return ts.updateImportDeclaration(node, decorators, modifiers, importClause, moduleSpecifier);
                }
            }
            if (ts.isExportDeclaration(node)) {
                const moduleSpecifier = relativize_specifier(root, node.moduleSpecifier);
                if (moduleSpecifier != null) {
                    const { decorators, modifiers, exportClause } = node;
                    return ts.updateExportDeclaration(node, decorators, modifiers, exportClause, moduleSpecifier);
                }
            }
            if (is_require(node)) {
                const moduleSpecifier = relativize_specifier(root, node.arguments[0]);
                if (moduleSpecifier != null) {
                    const { expression, typeArguments } = node;
                    return ts.updateCall(node, expression, typeArguments, [moduleSpecifier]);
                }
            }
            return ts.visitEachChild(node, visit, context);
        }
        return ts.visitNode(root, visit);
    };
}
exports.relativize_modules = relativize_modules;
function import_txt(load) {
    return (context) => (root) => {
        function visit(node) {
            if (ts.isImportDeclaration(node)) {
                const { importClause, moduleSpecifier } = node;
                if (ts.isStringLiteralLike(moduleSpecifier)) {
                    const txt_path = moduleSpecifier.text;
                    if (txt_path.endsWith(".txt") && importClause != null && importClause.name != null) {
                        const txt_text = load(txt_path);
                        if (txt_text != null) {
                            return ts.createVariableDeclaration(importClause.name, ts.createKeywordTypeNode(ts.SyntaxKind.StringKeyword), ts.createStringLiteral(txt_text));
                        }
                    }
                }
            }
            return ts.visitEachChild(node, visit, context);
        }
        return ts.visitNode(root, visit);
    };
}
exports.import_txt = import_txt;
function css_loader(css_text) {
    const dom = ts.createTempVariable(undefined);
    return [
        ts.createImportDeclaration(undefined, undefined, ts.createImportClause(undefined, ts.createNamespaceImport(dom)), ts.createStringLiteral("core/dom")),
        ts.createExpressionStatement(ts.createCall(ts.createPropertyAccess(ts.createPropertyAccess(dom, "styles"), "append"), undefined, [ts.createStringLiteral(css_text)])),
    ];
}
function import_css(load) {
    return (context) => (root) => {
        function visit(node) {
            if (ts.isImportDeclaration(node)) {
                const { importClause, moduleSpecifier } = node;
                if (ts.isStringLiteralLike(moduleSpecifier)) {
                    const css_path = moduleSpecifier.text;
                    if (importClause == null && css_path.endsWith(".css")) {
                        const css_text = load(css_path);
                        if (css_text != null) {
                            return css_loader(css_text);
                        }
                    }
                }
            }
            return ts.visitEachChild(node, visit, context);
        }
        return ts.visitNode(root, visit);
    };
}
exports.import_css = import_css;
function is_static(node) {
    return node.modifiers != null && node.modifiers.find((modifier) => modifier.kind == ts.SyntaxKind.StaticKeyword) != null;
}
function add_init_class() {
    return (context) => (root) => {
        function visit(node) {
            node = ts.visitEachChild(node, visit, context);
            if (ts.isClassDeclaration(node) && node.name != null) {
                const name = `init_${node.name.getText()}`;
                if (node.members.find((member) => ts.isMethodDeclaration(member) && member.name.getText() == name && is_static(member)) != null) {
                    const init = ts.createExpressionStatement(ts.createCall(ts.createPropertyAccess(node.name, name), undefined, undefined));
                    return [node, init];
                }
            }
            return node;
        }
        return ts.visitNode(root, visit);
    };
}
exports.add_init_class = add_init_class;
function insert_class_name() {
    function has__name__(node) {
        return node.members.find((member) => ts.isPropertyDeclaration(member) && member.name.getText() == "__name__" && is_static(member)) != null;
    }
    return (context) => (root) => {
        function visit(node) {
            node = ts.visitEachChild(node, visit, context);
            if (ts.isClassDeclaration(node) && node.name != null && !has__name__(node)) {
                const property = ts.createProperty(undefined, ts.createModifiersFromModifierFlags(ts.ModifierFlags.Static), "__name__", undefined, undefined, ts.createStringLiteral(node.name.text));
                node = ts.updateClassDeclaration(node, node.decorators, node.modifiers, node.name, node.typeParameters, node.heritageClauses, [property, ...node.members]);
            }
            return node;
        }
        return ts.visitNode(root, visit);
    };
}
exports.insert_class_name = insert_class_name;
function remove_use_strict() {
    return (_context) => (root) => {
        const statements = root.statements.filter((node) => {
            if (ts.isExpressionStatement(node)) {
                const expr = node.expression;
                if (ts.isStringLiteral(expr) && expr.text == "use strict")
                    return false;
            }
            return true;
        });
        return ts.updateSourceFileNode(root, statements);
    };
}
exports.remove_use_strict = remove_use_strict;
function remove_esmodule() {
    return (_context) => (root) => {
        const statements = root.statements.filter((node) => {
            if (ts.isExpressionStatement(node)) {
                const expr = node.expression;
                if (ts.isCallExpression(expr) && expr.arguments.length == 3) {
                    const [, arg] = expr.arguments;
                    if (ts.isStringLiteral(arg) && arg.text == "__esModule")
                        return false;
                }
            }
            return true;
        });
        return ts.updateSourceFileNode(root, statements);
    };
}
exports.remove_esmodule = remove_esmodule;
function collect_deps(source) {
    function traverse(node) {
        if (is_require(node)) {
            const [arg] = node.arguments;
            if (ts.isStringLiteral(arg) && arg.text.length > 0)
                deps.add(arg.text);
        }
        ts.forEachChild(node, traverse);
    }
    const deps = new Set();
    traverse(source);
    return [...deps];
}
exports.collect_deps = collect_deps;
function rewrite_deps(resolve) {
    return (context) => (root) => {
        function visit(node) {
            if (is_require(node)) {
                const [arg] = node.arguments;
                if (ts.isStringLiteral(arg) && arg.text.length > 0) {
                    const dep = arg.text;
                    const val = resolve(dep);
                    if (val != null) {
                        node = ts.updateCall(node, node.expression, node.typeArguments, [ts.createLiteral(val)]);
                        ts.addSyntheticTrailingComment(node, ts.SyntaxKind.MultiLineCommentTrivia, ` ${dep} `, false);
                    }
                    return node;
                }
            }
            return ts.visitEachChild(node, visit, context);
        }
        return ts.visitNode(root, visit);
    };
}
exports.rewrite_deps = rewrite_deps;
function add_json_export() {
    return (_context) => (root) => {
        if (root.statements.length == 1) {
            const [statement] = root.statements;
            if (ts.isExpressionStatement(statement)) {
                const left = ts.createPropertyAccess(ts.createIdentifier("module"), "exports");
                const right = statement.expression;
                const assign = ts.createStatement(ts.createAssignment(left, right));
                return ts.updateSourceFileNode(root, [assign]);
            }
        }
        return root;
    };
}
exports.add_json_export = add_json_export;
function wrap_in_function(module_name) {
    return (_context) => (root) => {
        const p = (name) => ts.createParameter(undefined, undefined, undefined, name);
        const params = [p("require"), p("module"), p("exports")];
        const block = ts.createBlock(root.statements, true);
        const func = ts.createFunctionDeclaration(undefined, undefined, undefined, "_", undefined, params, undefined, block);
        ts.addSyntheticLeadingComment(func, ts.SyntaxKind.MultiLineCommentTrivia, ` ${module_name} `, false);
        return ts.updateSourceFileNode(root, [func]);
    };
}
exports.wrap_in_function = wrap_in_function;
function parse_es(file, code, target = ts.ScriptTarget.ES2015) {
    return ts.createSourceFile(file, code != null ? code : ts.sys.readFile(file), target, true, ts.ScriptKind.JS);
}
exports.parse_es = parse_es;
function print_es(source) {
    const printer = ts.createPrinter();
    return printer.printNode(ts.EmitHint.SourceFile, source, source);
}
exports.print_es = print_es;
//# sourceMappingURL=transforms.js.map