"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const layoutable_1 = require("./layoutable");
const bbox_1 = require("../util/bbox");
class Stack extends layoutable_1.Layoutable {
    constructor() {
        super(...arguments);
        this.children = [];
    }
}
exports.Stack = Stack;
Stack.__name__ = "Stack";
class HStack extends Stack {
    _measure(_viewport) {
        let width = 0;
        let height = 0;
        for (const child of this.children) {
            const size_hint = child.measure({ width: 0, height: 0 });
            width += size_hint.width;
            height = Math.max(height, size_hint.height);
        }
        return { width, height };
    }
    _set_geometry(outer, inner) {
        super._set_geometry(outer, inner);
        const { top, bottom } = outer;
        let { left } = outer;
        for (const child of this.children) {
            const { width } = child.measure({ width: 0, height: 0 });
            child.set_geometry(new bbox_1.BBox({ left, width, top, bottom }));
            left += width;
        }
    }
}
exports.HStack = HStack;
HStack.__name__ = "HStack";
class VStack extends Stack {
    _measure(_viewport) {
        let width = 0;
        let height = 0;
        for (const child of this.children) {
            const size_hint = child.measure({ width: 0, height: 0 });
            width = Math.max(width, size_hint.width);
            height += size_hint.height;
        }
        return { width, height };
    }
    _set_geometry(outer, inner) {
        super._set_geometry(outer, inner);
        const { left, right } = outer;
        let { top } = outer;
        for (const child of this.children) {
            const { height } = child.measure({ width: 0, height: 0 });
            child.set_geometry(new bbox_1.BBox({ top, height, left, right }));
            top += height;
        }
    }
}
exports.VStack = VStack;
VStack.__name__ = "VStack";
class AnchorLayout extends layoutable_1.Layoutable {
    constructor() {
        super(...arguments);
        this.children = [];
    }
    _measure(viewport) {
        let width = 0;
        let height = 0;
        for (const { layout } of this.children) {
            const size_hint = layout.measure(viewport);
            width = Math.max(width, size_hint.width);
            height = Math.max(height, size_hint.height);
        }
        return { width, height };
    }
    _set_geometry(outer, inner) {
        super._set_geometry(outer, inner);
        for (const { layout, anchor, margin } of this.children) {
            const { left, right, top, bottom, hcenter, vcenter } = outer;
            const { width, height } = layout.measure(outer);
            let bbox;
            switch (anchor) {
                case 'top_left':
                    bbox = new bbox_1.BBox({ left: left + margin, top: top + margin, width, height });
                    break;
                case 'top_center':
                    bbox = new bbox_1.BBox({ hcenter, top: top + margin, width, height });
                    break;
                case 'top_right':
                    bbox = new bbox_1.BBox({ right: right - margin, top: top + margin, width, height });
                    break;
                case 'bottom_right':
                    bbox = new bbox_1.BBox({ right: right - margin, bottom: bottom - margin, width, height });
                    break;
                case 'bottom_center':
                    bbox = new bbox_1.BBox({ hcenter, bottom: bottom - margin, width, height });
                    break;
                case 'bottom_left':
                    bbox = new bbox_1.BBox({ left: left + margin, bottom: bottom - margin, width, height });
                    break;
                case 'center_left':
                    bbox = new bbox_1.BBox({ left: left + margin, vcenter, width, height });
                    break;
                case 'center':
                    bbox = new bbox_1.BBox({ hcenter, vcenter, width, height });
                    break;
                case 'center_right':
                    bbox = new bbox_1.BBox({ right: right - margin, vcenter, width, height });
                    break;
                default:
                    throw new Error("unreachable");
            }
            layout.set_geometry(bbox);
        }
    }
}
exports.AnchorLayout = AnchorLayout;
AnchorLayout.__name__ = "AnchorLayout";
