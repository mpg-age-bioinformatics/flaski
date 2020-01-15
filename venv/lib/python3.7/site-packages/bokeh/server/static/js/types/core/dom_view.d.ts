import { View } from "./view";
export declare namespace DOMView {
    type Options = View.Options;
}
export declare class DOMView extends View {
    tagName: keyof HTMLElementTagNameMap;
    protected _has_finished: boolean;
    el: HTMLElement;
    initialize(): void;
    remove(): void;
    css_classes(): string[];
    cursor(_sx: number, _sy: number): string | null;
    render(): void;
    renderTo(element: HTMLElement): void;
    on_hit?(sx: number, sy: number): boolean;
    has_finished(): boolean;
    protected readonly _root_element: HTMLElement;
    readonly is_idle: boolean;
    protected _createElement(): HTMLElement;
}
