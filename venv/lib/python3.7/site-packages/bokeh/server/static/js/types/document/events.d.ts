import { Document, References } from "./document";
import { Data } from "../core/types";
import { HasProps } from "../core/has_props";
import { Ref } from "../core/util/refs";
import { PatchSet } from "../models/sources/column_data_source";
export interface ModelChanged {
    kind: "ModelChanged";
    model: Ref;
    attr: string;
    new: any;
    hint?: any;
}
export interface TitleChanged {
    kind: "TitleChanged";
    title: string;
}
export interface RootAdded {
    kind: "RootAdded";
    model: Ref;
}
export interface RootRemoved {
    kind: "RootRemoved";
    model: Ref;
}
export interface ColumnDataChanged {
    kind: "ColumnDataChanged";
    column_source: Ref;
    cols?: any;
    new: any;
}
export interface ColumnsStreamed {
    kind: "ColumnsStreamed";
    column_source: Ref;
    data: Data;
    rollover?: number;
}
export interface ColumnsPatched {
    kind: "ColumnsPatched";
    column_source: Ref;
    patches: PatchSet;
}
export declare type DocumentChanged = ModelChanged | TitleChanged | RootAdded | RootRemoved | ColumnDataChanged | ColumnsStreamed | ColumnsPatched;
export declare abstract class DocumentChangedEvent {
    readonly document: Document;
    constructor(document: Document);
    abstract json(references: References): DocumentChanged;
}
export declare class ModelChangedEvent extends DocumentChangedEvent {
    readonly model: HasProps;
    readonly attr: string;
    readonly old: any;
    readonly new_: any;
    readonly setter_id?: string | undefined;
    readonly hint?: any;
    constructor(document: Document, model: HasProps, attr: string, old: any, new_: any, setter_id?: string | undefined, hint?: any);
    json(references: References): DocumentChanged;
}
export declare class ColumnsPatchedEvent extends DocumentChangedEvent {
    readonly column_source: Ref;
    readonly patches: PatchSet;
    constructor(document: Document, column_source: Ref, patches: PatchSet);
    json(_references: References): ColumnsPatched;
}
export declare class ColumnsStreamedEvent extends DocumentChangedEvent {
    readonly column_source: Ref;
    readonly data: Data;
    readonly rollover?: number | undefined;
    constructor(document: Document, column_source: Ref, data: Data, rollover?: number | undefined);
    json(_references: References): ColumnsStreamed;
}
export declare class TitleChangedEvent extends DocumentChangedEvent {
    readonly title: string;
    readonly setter_id?: string | undefined;
    constructor(document: Document, title: string, setter_id?: string | undefined);
    json(_references: References): TitleChanged;
}
export declare class RootAddedEvent extends DocumentChangedEvent {
    readonly model: HasProps;
    readonly setter_id?: string | undefined;
    constructor(document: Document, model: HasProps, setter_id?: string | undefined);
    json(references: References): RootAdded;
}
export declare class RootRemovedEvent extends DocumentChangedEvent {
    readonly model: HasProps;
    readonly setter_id?: string | undefined;
    constructor(document: Document, model: HasProps, setter_id?: string | undefined);
    json(_references: References): RootRemoved;
}
