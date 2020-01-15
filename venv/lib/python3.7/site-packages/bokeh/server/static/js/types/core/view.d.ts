import { HasProps } from "./has_props";
import { Property } from "./properties";
import { Signal0, Signal } from "./signaling";
export declare namespace View {
    type Options = {
        id?: string;
        model: HasProps;
        parent: View | null;
        connect_signals?: boolean;
    };
}
declare const View_base: {
    new (): {
        connect<Args, Sender extends object>(signal: Signal<Args, Sender>, slot: import("./signaling").Slot<Args, Sender>): boolean;
        disconnect<Args_1, Sender_1 extends object>(signal: Signal<Args_1, Sender_1>, slot: import("./signaling").Slot<Args_1, Sender_1>): boolean;
    };
};
export declare class View extends View_base {
    readonly removed: Signal0<this>;
    readonly id: string;
    readonly model: HasProps;
    private _parent;
    constructor(options: View.Options);
    initialize(): void;
    remove(): void;
    toString(): string;
    serializable_state(): {
        [key: string]: unknown;
    };
    readonly parent: View | null;
    readonly is_root: boolean;
    readonly root: View;
    assert_root(): void;
    connect_signals(): void;
    disconnect_signals(): void;
    on_change(property: Property<unknown>, fn: () => void): void;
    on_change(properties: Property<unknown>[], fn: () => void): void;
}
export {};
