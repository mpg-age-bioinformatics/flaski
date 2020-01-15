import { Document, EventManager, DocumentChangedEvent } from "../document";
import { Message } from "../protocol/message";
import { ClientConnection } from "./connection";
import { BokehEvent } from "../core/bokeh_events";
export declare class ClientSession {
    protected readonly _connection: ClientConnection;
    readonly document: Document;
    readonly id: string;
    protected _document_listener: (event: DocumentChangedEvent) => void;
    readonly event_manager: EventManager;
    constructor(_connection: ClientConnection, document: Document, id: string);
    handle(message: Message): void;
    close(): void;
    send_event(event: BokehEvent): void;
    _connection_closed(): void;
    request_server_info(): Promise<unknown>;
    force_roundtrip(): Promise<void>;
    protected _document_changed(event: DocumentChangedEvent): void;
    protected _handle_patch(message: Message): void;
    protected _handle_ok(message: Message): void;
    protected _handle_error(message: Message): void;
}
