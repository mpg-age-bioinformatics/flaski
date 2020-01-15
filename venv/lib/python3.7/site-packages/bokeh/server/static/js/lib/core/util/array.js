"use strict";
//     Underscore.js 1.8.3
//     http://underscorejs.org
//     (c) 2009-2015 Jeremy Ashkenas, DocumentCloud and Investigative Reporters & Editors
//     Underscore may be freely distributed under the MIT license.
Object.defineProperty(exports, "__esModule", { value: true });
const math_1 = require("./math");
const assert_1 = require("./assert");
const arrayable_1 = require("./arrayable");
exports.map = arrayable_1.map;
exports.reduce = arrayable_1.reduce;
exports.min = arrayable_1.min;
exports.min_by = arrayable_1.min_by;
exports.max = arrayable_1.max;
exports.max_by = arrayable_1.max_by;
exports.sum = arrayable_1.sum;
exports.cumsum = arrayable_1.cumsum;
exports.every = arrayable_1.every;
exports.some = arrayable_1.some;
exports.find = arrayable_1.find;
exports.find_last = arrayable_1.find_last;
exports.find_index = arrayable_1.find_index;
exports.find_last_index = arrayable_1.find_last_index;
exports.sorted_index = arrayable_1.sorted_index;
const slice = Array.prototype.slice;
function head(array) {
    return array[0];
}
exports.head = head;
function tail(array) {
    return array[array.length - 1];
}
exports.tail = tail;
function last(array) {
    return array[array.length - 1];
}
exports.last = last;
function copy(array) {
    return slice.call(array);
}
exports.copy = copy;
function concat(arrays) {
    return [].concat(...arrays);
}
exports.concat = concat;
function includes(array, value) {
    return array.indexOf(value) !== -1;
}
exports.includes = includes;
exports.contains = includes;
function nth(array, index) {
    return array[index >= 0 ? index : array.length + index];
}
exports.nth = nth;
function zip(...arrays) {
    if (arrays.length == 0)
        return [];
    const n = arrayable_1.min(arrays.map((a) => a.length));
    const k = arrays.length;
    const result = new Array(n);
    for (let i = 0; i < n; i++) {
        result[i] = new Array(k);
        for (let j = 0; j < k; j++)
            result[i][j] = arrays[j][i];
    }
    return result;
}
exports.zip = zip;
function unzip(array) {
    const n = array.length;
    const k = arrayable_1.min(array.map((a) => a.length));
    const results = Array(k);
    for (let j = 0; j < k; j++)
        results[j] = new Array(n);
    for (let i = 0; i < n; i++) {
        for (let j = 0; j < k; j++)
            results[j][i] = array[i][j];
    }
    return results;
}
exports.unzip = unzip;
function range(start, stop, step = 1) {
    assert_1.assert(step > 0, "'step' must be a positive number");
    if (stop == null) {
        stop = start;
        start = 0;
    }
    const { max, ceil, abs } = Math;
    const delta = start <= stop ? step : -step;
    const length = max(ceil(abs(stop - start) / step), 0);
    const range = Array(length);
    for (let i = 0; i < length; i++, start += delta) {
        range[i] = start;
    }
    return range;
}
exports.range = range;
function linspace(start, stop, num = 100) {
    const step = (stop - start) / (num - 1);
    const array = new Array(num);
    for (let i = 0; i < num; i++) {
        array[i] = start + step * i;
    }
    return array;
}
exports.linspace = linspace;
function transpose(array) {
    const rows = array.length;
    const cols = array[0].length;
    const transposed = [];
    for (let j = 0; j < cols; j++) {
        transposed[j] = [];
        for (let i = 0; i < rows; i++) {
            transposed[j][i] = array[i][j];
        }
    }
    return transposed;
}
exports.transpose = transpose;
function argmin(array) {
    return arrayable_1.min_by(range(array.length), (i) => array[i]);
}
exports.argmin = argmin;
function argmax(array) {
    return arrayable_1.max_by(range(array.length), (i) => array[i]);
}
exports.argmax = argmax;
function sort_by(array, key) {
    const tmp = array.map((value, index) => {
        return { value, index, key: key(value) };
    });
    tmp.sort((left, right) => {
        const a = left.key;
        const b = right.key;
        if (a !== b) {
            if (a > b || a === undefined)
                return 1;
            if (a < b || b === undefined)
                return -1;
        }
        return left.index - right.index;
    });
    return tmp.map((item) => item.value);
}
exports.sort_by = sort_by;
function uniq(array) {
    const result = [];
    for (const value of array) {
        if (!includes(result, value)) {
            result.push(value);
        }
    }
    return result;
}
exports.uniq = uniq;
function uniq_by(array, key) {
    const result = [];
    const seen = [];
    for (const value of array) {
        const computed = key(value);
        if (!includes(seen, computed)) {
            seen.push(computed);
            result.push(value);
        }
    }
    return result;
}
exports.uniq_by = uniq_by;
function union(...arrays) {
    return uniq(concat(arrays));
}
exports.union = union;
function intersection(array, ...arrays) {
    const result = [];
    top: for (const item of array) {
        if (includes(result, item))
            continue;
        for (const other of arrays) {
            if (!includes(other, item))
                continue top;
        }
        result.push(item);
    }
    return result;
}
exports.intersection = intersection;
function difference(array, ...arrays) {
    const rest = concat(arrays);
    return array.filter((value) => !includes(rest, value));
}
exports.difference = difference;
function remove_at(array, i) {
    const result = copy(array);
    result.splice(i, 1);
    return result;
}
exports.remove_at = remove_at;
function remove_by(array, key) {
    for (let i = 0; i < array.length;) {
        if (key(array[i]))
            array.splice(i, 1);
        else
            i++;
    }
}
exports.remove_by = remove_by;
// Shuffle a collection, using the modern version of the
// [Fisher-Yates shuffle](http://en.wikipedia.org/wiki/Fisher–Yates_shuffle).
function shuffle(array) {
    const length = array.length;
    const shuffled = new Array(length);
    for (let i = 0; i < length; i++) {
        const rand = math_1.randomIn(0, i);
        if (rand !== i)
            shuffled[i] = shuffled[rand];
        shuffled[rand] = array[i];
    }
    return shuffled;
}
exports.shuffle = shuffle;
function pairwise(array, fn) {
    const n = array.length;
    const result = new Array(n - 1);
    for (let i = 0; i < n - 1; i++) {
        result[i] = fn(array[i], array[i + 1]);
    }
    return result;
}
exports.pairwise = pairwise;
function reversed(array) {
    const n = array.length;
    const result = new Array(n);
    for (let i = 0; i < n; i++) {
        result[n - i - 1] = array[i];
    }
    return result;
}
exports.reversed = reversed;
function repeat(value, n) {
    const result = new Array(n);
    for (let i = 0; i < n; i++) {
        result[i] = value;
    }
    return result;
}
exports.repeat = repeat;
