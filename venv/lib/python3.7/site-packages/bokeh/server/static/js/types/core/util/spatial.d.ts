import { Rect } from "../types";
export declare type IndexedRect = Rect & {
    i: number;
};
export declare class SpatialIndex {
    private readonly points;
    private readonly index;
    constructor(points: IndexedRect[]);
    protected _normalize(rect: Rect): Rect;
    readonly bbox: Rect;
    search(rect: Rect): IndexedRect[];
    indices(rect: Rect): number[];
}
