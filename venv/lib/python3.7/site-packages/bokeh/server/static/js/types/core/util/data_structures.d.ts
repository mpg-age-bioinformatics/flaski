export declare class MultiDict<T> {
    _dict: {
        [key: string]: T | T[];
    };
    _existing(key: string): T | T[] | null;
    add_value(key: string, value: T): void;
    remove_value(key: string, value: T): void;
    get_one(key: string, duplicate_error: string): T | null;
}
export declare class Set<T> {
    private _values;
    readonly values: T[];
    constructor(obj?: T[] | Set<T>);
    toString(): string;
    readonly size: number;
    has(item: T): boolean;
    add(item: T): void;
    remove(item: T): void;
    toggle(item: T): void;
    clear(): void;
    union(input: T[] | Set<T>): Set<T>;
    intersect(input: T[] | Set<T>): Set<T>;
    diff(input: T[] | Set<T>): Set<T>;
    forEach(fn: (value: T, value2: T, set: Set<T>) => void, thisArg?: any): void;
}
export declare namespace Matrix {
    type MapFn<T, U> = (value: T, row: number, col: number) => U;
}
export declare class Matrix<T> {
    readonly nrows: number;
    readonly ncols: number;
    private _matrix;
    constructor(nrows: number, ncols: number, init: (row: number, col: number) => T);
    at(row: number, col: number): T;
    map<U>(fn: Matrix.MapFn<T, U>): Matrix<U>;
    apply<U>(obj: Matrix<Matrix.MapFn<T, U>> | Matrix.MapFn<T, U>[][]): Matrix<U>;
    to_sparse(): [T, number, number][];
    static from<U>(obj: Matrix<U> | U[][]): Matrix<U>;
}
