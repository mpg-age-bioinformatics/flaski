import { HasProps } from "../has_props";
import { Attrs } from "../types";
export interface Ref {
    id: string;
    type: string;
    subtype?: string;
    attributes?: Attrs;
}
export declare function create_ref(obj: HasProps): Ref;
export declare function is_ref(arg: unknown): arg is Ref;
