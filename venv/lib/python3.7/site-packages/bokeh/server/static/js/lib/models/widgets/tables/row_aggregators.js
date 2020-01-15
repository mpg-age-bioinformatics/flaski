"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const slickgrid_1 = require("slickgrid");
const { Avg, Min, Max, Sum } = slickgrid_1.Data.Aggregators;
const p = require("../../../core/properties");
const model_1 = require("../../../model");
class RowAggregator extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_RowAggregator() {
        this.define({
            field_: [p.String, ''],
        });
    }
}
exports.RowAggregator = RowAggregator;
RowAggregator.__name__ = "RowAggregator";
RowAggregator.init_RowAggregator();
const avg = new Avg();
class AvgAggregator extends RowAggregator {
    constructor() {
        super(...arguments);
        this.key = 'avg';
        this.init = avg.init;
        this.accumulate = avg.accumulate;
        this.storeResult = avg.storeResult;
    }
}
exports.AvgAggregator = AvgAggregator;
AvgAggregator.__name__ = "AvgAggregator";
const min = new Min();
class MinAggregator extends RowAggregator {
    constructor() {
        super(...arguments);
        this.key = 'min';
        this.init = min.init;
        this.accumulate = min.accumulate;
        this.storeResult = min.storeResult;
    }
}
exports.MinAggregator = MinAggregator;
MinAggregator.__name__ = "MinAggregator";
const max = new Max();
class MaxAggregator extends RowAggregator {
    constructor() {
        super(...arguments);
        this.key = 'max';
        this.init = max.init;
        this.accumulate = max.accumulate;
        this.storeResult = max.storeResult;
    }
}
exports.MaxAggregator = MaxAggregator;
MaxAggregator.__name__ = "MaxAggregator";
const sum = new Sum();
class SumAggregator extends RowAggregator {
    constructor() {
        super(...arguments);
        this.key = 'sum';
        this.init = sum.init;
        this.accumulate = sum.accumulate;
        this.storeResult = sum.storeResult;
    }
}
exports.SumAggregator = SumAggregator;
SumAggregator.__name__ = "SumAggregator";
