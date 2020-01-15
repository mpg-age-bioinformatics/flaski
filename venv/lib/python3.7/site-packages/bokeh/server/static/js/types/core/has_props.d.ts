import { View } from "./view";
import { Class } from "./class";
import { Attrs } from "./types";
import { Signal0, Signal } from "./signaling";
import { Ref } from "./util/refs";
import * as p from "./properties";
import { Property } from "./properties";
import { ColumnarDataSource } from "../models/sources/columnar_data_source";
import { Document } from "../document";
export declare module HasProps {
    type Attrs = p.AttrsOf<Props>;
    type Props = {
        id: p.Property<string>;
    };
    interface SetOptions {
        check_eq?: boolean;
        silent?: boolean;
        no_change?: boolean;
        defaults?: boolean;
        setter_id?: string;
    }
}
export interface HasProps extends HasProps.Attrs {
    constructor: Function & {
        __name__: string;
        __module__?: string;
        __qualified__: string;
    };
    id: string;
}
declare const HasProps_base: {
    new (): {
        connect<Args, Sender extends object>(signal: Signal<Args, Sender>, slot: import("./signaling").Slot<Args, Sender>): boolean;
        disconnect<Args_1, Sender_1 extends object>(signal: Signal<Args_1, Sender_1>, slot: import("./signaling").Slot<Args_1, Sender_1>): boolean;
    };
};
export declare abstract class HasProps extends HasProps_base {
    type: string;
    static __name__: string;
    static __module__?: string;
    static readonly __qualified__: string;
    static init_HasProps(): void;
    default_view: Class<View, [View.Options]>;
    props: {
        [key: string]: {
            type: Class<Property<any>>;
            default_value: any;
            internal: boolean;
        };
    };
    mixins: string[];
    private static _fix_default;
    static define<T>(obj: Partial<p.DefineOf<T>>): void;
    static internal(obj: any): void;
    static mixin(...names: string[]): void;
    static mixins(names: string[]): void;
    static override(obj: any): void;
    toString(): string;
    _subtype: string | undefined;
    document: Document | null;
    readonly destroyed: Signal0<this>;
    readonly change: Signal0<this>;
    readonly transformchange: Signal0<this>;
    readonly attributes: {
        [key: string]: any;
    };
    readonly properties: {
        [key: string]: any;
    };
    protected readonly _set_after_defaults: {
        [key: string]: boolean;
    };
    constructor(attrs?: Attrs);
    finalize(): void;
    initialize(): void;
    connect_signals(): void;
    disconnect_signals(): void;
    destroy(): void;
    clone(): this;
    private _pending;
    private _changing;
    private _setv;
    setv(attrs: Attrs, options?: HasProps.SetOptions): void;
    getv(prop_name: string): any;
    ref(): Ref;
    set_subtype(subtype: string): void;
    attribute_is_serializable(attr: string): boolean;
    serializable_attributes(): Attrs;
    static _value_to_json(_key: string, value: any, _optional_parent_object: any): any;
    attributes_as_json(include_defaults?: boolean, value_to_json?: typeof HasProps._value_to_json): any;
    static _json_record_references(doc: Document, v: any, result: {
        [key: string]: HasProps;
    }, recurse: boolean): void;
    static _value_record_references(v: any, result: Attrs, recurse: boolean): void;
    protected _immediate_references(): HasProps[];
    references(): HasProps[];
    protected _doc_attached(): void;
    attach_document(doc: Document): void;
    detach_document(): void;
    protected _tell_document_about_change(attr: string, old: any, new_: any, options: {
        setter_id?: string;
    }): void;
    materialize_dataspecs(source: ColumnarDataSource): {
        [key: string]: unknown[] | number;
    };
}
export {};
