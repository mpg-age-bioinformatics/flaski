"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
class AssertionError extends Error {
}
exports.AssertionError = AssertionError;
AssertionError.__name__ = "AssertionError";
function assert(condition, message) {
    if (condition === true || (condition !== false && condition()))
        return;
    throw new AssertionError(message || "Assertion failed");
}
exports.assert = assert;
