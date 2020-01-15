"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const MAX_INT32 = 2147483647;
// Park-Miller LCG
class Random {
    constructor(seed) {
        this.seed = seed % MAX_INT32;
        if (this.seed <= 0)
            this.seed += MAX_INT32 - 1;
    }
    integer() {
        this.seed = (48271 * this.seed) % MAX_INT32;
        return this.seed;
    }
    float() {
        return (this.integer() - 1) / (MAX_INT32 - 1);
    }
}
exports.Random = Random;
Random.__name__ = "Random";
exports.random = new Random(Date.now());
