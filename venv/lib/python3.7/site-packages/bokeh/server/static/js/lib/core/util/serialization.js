"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const types_1 = require("./types");
const compat_1 = require("./compat");
exports.ARRAY_TYPES = {
    uint8: Uint8Array,
    int8: Int8Array,
    uint16: Uint16Array,
    int16: Int16Array,
    uint32: Uint32Array,
    int32: Int32Array,
    float32: Float32Array,
    float64: Float64Array,
};
exports.DTYPES = {
    Uint8Array: "uint8",
    Int8Array: "int8",
    Uint16Array: "uint16",
    Int16Array: "int16",
    Uint32Array: "uint32",
    Int32Array: "int32",
    Float32Array: "float32",
    Float64Array: "float64",
};
function arrayName(array) {
    if ("name" in array.constructor)
        return array.constructor.name;
    else {
        switch (true) {
            case array instanceof Uint8Array: return "Uint8Array";
            case array instanceof Int8Array: return "Int8Array";
            case array instanceof Uint16Array: return "Uint16Array";
            case array instanceof Int16Array: return "Int16Array";
            case array instanceof Uint32Array: return "Uint32Array";
            case array instanceof Int32Array: return "Int32Array";
            case array instanceof Float32Array: return "Float32Array";
            case array instanceof Float64Array: return "Float64Array";
            default:
                throw new Error("unsupported typed array");
        }
    }
}
exports.BYTE_ORDER = compat_1.is_little_endian ? "little" : "big";
function swap16(a) {
    const x = new Uint8Array(a.buffer, a.byteOffset, a.length * 2);
    for (let i = 0, end = x.length; i < end; i += 2) {
        const t = x[i];
        x[i] = x[i + 1];
        x[i + 1] = t;
    }
}
exports.swap16 = swap16;
function swap32(a) {
    const x = new Uint8Array(a.buffer, a.byteOffset, a.length * 4);
    for (let i = 0, end = x.length; i < end; i += 4) {
        let t = x[i];
        x[i] = x[i + 3];
        x[i + 3] = t;
        t = x[i + 1];
        x[i + 1] = x[i + 2];
        x[i + 2] = t;
    }
}
exports.swap32 = swap32;
function swap64(a) {
    const x = new Uint8Array(a.buffer, a.byteOffset, a.length * 8);
    for (let i = 0, end = x.length; i < end; i += 8) {
        let t = x[i];
        x[i] = x[i + 7];
        x[i + 7] = t;
        t = x[i + 1];
        x[i + 1] = x[i + 6];
        x[i + 6] = t;
        t = x[i + 2];
        x[i + 2] = x[i + 5];
        x[i + 5] = t;
        t = x[i + 3];
        x[i + 3] = x[i + 4];
        x[i + 4] = t;
    }
}
exports.swap64 = swap64;
function process_buffer(specification, buffers) {
    const need_swap = specification.order !== exports.BYTE_ORDER;
    const { shape } = specification;
    let bytes = null;
    for (const buf of buffers) {
        const header = JSON.parse(buf[0]);
        if (header.id === specification.__buffer__) {
            bytes = buf[1];
            break;
        }
    }
    const arr = new (exports.ARRAY_TYPES[specification.dtype])(bytes);
    if (need_swap) {
        if (arr.BYTES_PER_ELEMENT === 2) {
            swap16(arr);
        }
        else if (arr.BYTES_PER_ELEMENT === 4) {
            swap32(arr);
        }
        else if (arr.BYTES_PER_ELEMENT === 8) {
            swap64(arr);
        }
    }
    return [arr, shape];
}
exports.process_buffer = process_buffer;
function process_array(obj, buffers) {
    if (types_1.isObject(obj) && '__ndarray__' in obj)
        return decode_base64(obj);
    else if (types_1.isObject(obj) && '__buffer__' in obj)
        return process_buffer(obj, buffers);
    else if (types_1.isArray(obj) || types_1.isTypedArray(obj))
        return [obj, []];
    else
        return undefined;
}
exports.process_array = process_array;
function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    const chars = Array.from(bytes).map((b) => String.fromCharCode(b));
    return btoa(chars.join(""));
}
exports.arrayBufferToBase64 = arrayBufferToBase64;
function base64ToArrayBuffer(base64) {
    const binary_string = atob(base64);
    const len = binary_string.length;
    const bytes = new Uint8Array(len);
    for (let i = 0, end = len; i < end; i++) {
        bytes[i] = binary_string.charCodeAt(i);
    }
    return bytes.buffer;
}
exports.base64ToArrayBuffer = base64ToArrayBuffer;
function decode_base64(input) {
    const bytes = base64ToArrayBuffer(input.__ndarray__);
    const dtype = input.dtype;
    const shape = input.shape;
    let array;
    if (dtype in exports.ARRAY_TYPES)
        array = new (exports.ARRAY_TYPES[dtype])(bytes);
    else
        throw new Error(`unknown dtype: ${dtype}`);
    return [array, shape];
}
exports.decode_base64 = decode_base64;
function encode_base64(array, shape) {
    const b64 = arrayBufferToBase64(array.buffer);
    const name = arrayName(array);
    let dtype;
    if (name in exports.DTYPES)
        dtype = exports.DTYPES[name];
    else
        throw new Error(`unknown array type: ${name}`);
    const data = {
        __ndarray__: b64,
        shape,
        dtype,
    };
    return data;
}
exports.encode_base64 = encode_base64;
function decode_traverse_data(v, buffers) {
    // v is just a regular array of scalars
    if (v.length == 0 || !(types_1.isObject(v[0]) || types_1.isArray(v[0]))) {
        return [v, []];
    }
    const arrays = [];
    const shapes = [];
    for (const obj of v) {
        const [arr, shape] = types_1.isArray(obj) ? decode_traverse_data(obj, buffers)
            : process_array(obj, buffers);
        arrays.push(arr);
        shapes.push(shape);
    }
    // If there is a list of empty lists, reduce that to just a list
    const filtered_shapes = shapes.map((shape) => shape.filter((v) => v.length != 0));
    return [arrays, filtered_shapes];
}
function decode_column_data(data, buffers = []) {
    const new_data = {};
    const new_shapes = {};
    for (const k in data) {
        // might be array of scalars, or might be ragged array or arrays
        const v = data[k];
        if (types_1.isArray(v)) {
            // v is just a regular array of scalars
            if (v.length == 0 || !(types_1.isObject(v[0]) || types_1.isArray(v[0]))) {
                new_data[k] = v;
                continue;
            }
            // v is a ragged array of arrays
            const [arrays, shapes] = decode_traverse_data(v, buffers);
            new_data[k] = arrays;
            new_shapes[k] = shapes;
            // must be object or array (single array case)
        }
        else {
            const [arr, shape] = process_array(v, buffers);
            new_data[k] = arr;
            new_shapes[k] = shape;
        }
    }
    return [new_data, new_shapes];
}
exports.decode_column_data = decode_column_data;
function encode_traverse_data(v, shapes) {
    const new_array = [];
    for (let i = 0, end = v.length; i < end; i++) {
        const item = v[i];
        if (types_1.isTypedArray(item)) {
            const shape = shapes[i] ? shapes[i] : undefined;
            new_array.push(encode_base64(item, shape));
        }
        else if (types_1.isArray(item)) {
            new_array.push(encode_traverse_data(item, shapes ? shapes[i] : []));
        }
        else
            new_array.push(item);
    }
    return new_array;
}
function encode_column_data(data, shapes) {
    const new_data = {};
    for (const k in data) {
        const v = data[k];
        const shapes_k = shapes != null ? shapes[k] : undefined;
        let new_v;
        if (types_1.isTypedArray(v)) {
            new_v = encode_base64(v, shapes_k);
        }
        else if (types_1.isArray(v)) {
            new_v = encode_traverse_data(v, shapes_k || []);
        }
        else
            new_v = v;
        new_data[k] = new_v;
    }
    return new_data;
}
exports.encode_column_data = encode_column_data;
