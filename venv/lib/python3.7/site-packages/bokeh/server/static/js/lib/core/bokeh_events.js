"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
function event(event_name) {
    return function (cls) {
        cls.prototype.event_name = event_name;
    };
}
class BokehEvent {
    to_json() {
        const { event_name } = this;
        return { event_name, event_values: this._to_json() };
    }
    _to_json() {
        const { origin } = this;
        return { model_id: origin != null ? origin.id : null };
    }
}
exports.BokehEvent = BokehEvent;
BokehEvent.__name__ = "BokehEvent";
let ButtonClick = class ButtonClick extends BokehEvent {
};
ButtonClick.__name__ = "ButtonClick";
ButtonClick = __decorate([
    event("button_click")
], ButtonClick);
exports.ButtonClick = ButtonClick;
let MenuItemClick = class MenuItemClick extends BokehEvent {
    constructor(item) {
        super();
        this.item = item;
    }
    _to_json() {
        const { item } = this;
        return Object.assign(Object.assign({}, super._to_json()), { item });
    }
};
MenuItemClick.__name__ = "MenuItemClick";
MenuItemClick = __decorate([
    event("menu_item_click")
], MenuItemClick);
exports.MenuItemClick = MenuItemClick;
// A UIEvent is an event originating on a canvas this includes.
// DOM events such as keystrokes as well as hammer events and LOD events.
class UIEvent extends BokehEvent {
}
exports.UIEvent = UIEvent;
UIEvent.__name__ = "UIEvent";
let LODStart = class LODStart extends UIEvent {
};
LODStart.__name__ = "LODStart";
LODStart = __decorate([
    event("lodstart")
], LODStart);
exports.LODStart = LODStart;
let LODEnd = class LODEnd extends UIEvent {
};
LODEnd.__name__ = "LODEnd";
LODEnd = __decorate([
    event("lodend")
], LODEnd);
exports.LODEnd = LODEnd;
let SelectionGeometry = class SelectionGeometry extends UIEvent {
    constructor(geometry, final) {
        super();
        this.geometry = geometry;
        this.final = final;
    }
    _to_json() {
        const { geometry, final } = this;
        return Object.assign(Object.assign({}, super._to_json()), { geometry, final });
    }
};
SelectionGeometry.__name__ = "SelectionGeometry";
SelectionGeometry = __decorate([
    event("selectiongeometry")
], SelectionGeometry);
exports.SelectionGeometry = SelectionGeometry;
let Reset = class Reset extends UIEvent {
};
Reset.__name__ = "Reset";
Reset = __decorate([
    event("reset")
], Reset);
exports.Reset = Reset;
class PointEvent extends UIEvent {
    constructor(sx, sy, x, y) {
        super();
        this.sx = sx;
        this.sy = sy;
        this.x = x;
        this.y = y;
    }
    _to_json() {
        const { sx, sy, x, y } = this;
        return Object.assign(Object.assign({}, super._to_json()), { sx, sy, x, y });
    }
}
exports.PointEvent = PointEvent;
PointEvent.__name__ = "PointEvent";
let Pan = class Pan extends PointEvent {
    /* TODO: direction: -1 | 1 */
    constructor(sx, sy, x, y, delta_x, delta_y) {
        super(sx, sy, x, y);
        this.sx = sx;
        this.sy = sy;
        this.x = x;
        this.y = y;
        this.delta_x = delta_x;
        this.delta_y = delta_y;
    }
    _to_json() {
        const { delta_x, delta_y /*, direction*/ } = this;
        return Object.assign(Object.assign({}, super._to_json()), { delta_x, delta_y /*, direction*/ });
    }
};
Pan.__name__ = "Pan";
Pan = __decorate([
    event("pan")
], Pan);
exports.Pan = Pan;
let Pinch = class Pinch extends PointEvent {
    constructor(sx, sy, x, y, scale) {
        super(sx, sy, x, y);
        this.sx = sx;
        this.sy = sy;
        this.x = x;
        this.y = y;
        this.scale = scale;
    }
    _to_json() {
        const { scale } = this;
        return Object.assign(Object.assign({}, super._to_json()), { scale });
    }
};
Pinch.__name__ = "Pinch";
Pinch = __decorate([
    event("pinch")
], Pinch);
exports.Pinch = Pinch;
let Rotate = class Rotate extends PointEvent {
    constructor(sx, sy, x, y, rotation) {
        super(sx, sy, x, y);
        this.sx = sx;
        this.sy = sy;
        this.x = x;
        this.y = y;
        this.rotation = rotation;
    }
    _to_json() {
        const { rotation } = this;
        return Object.assign(Object.assign({}, super._to_json()), { rotation });
    }
};
Rotate.__name__ = "Rotate";
Rotate = __decorate([
    event("rotate")
], Rotate);
exports.Rotate = Rotate;
let MouseWheel = class MouseWheel extends PointEvent {
    constructor(sx, sy, x, y, delta) {
        super(sx, sy, x, y);
        this.sx = sx;
        this.sy = sy;
        this.x = x;
        this.y = y;
        this.delta = delta;
    }
    _to_json() {
        const { delta } = this;
        return Object.assign(Object.assign({}, super._to_json()), { delta });
    }
};
MouseWheel.__name__ = "MouseWheel";
MouseWheel = __decorate([
    event("wheel")
], MouseWheel);
exports.MouseWheel = MouseWheel;
let MouseMove = class MouseMove extends PointEvent {
};
MouseMove.__name__ = "MouseMove";
MouseMove = __decorate([
    event("mousemove")
], MouseMove);
exports.MouseMove = MouseMove;
let MouseEnter = class MouseEnter extends PointEvent {
};
MouseEnter.__name__ = "MouseEnter";
MouseEnter = __decorate([
    event("mouseenter")
], MouseEnter);
exports.MouseEnter = MouseEnter;
let MouseLeave = class MouseLeave extends PointEvent {
};
MouseLeave.__name__ = "MouseLeave";
MouseLeave = __decorate([
    event("mouseleave")
], MouseLeave);
exports.MouseLeave = MouseLeave;
let Tap = class Tap extends PointEvent {
};
Tap.__name__ = "Tap";
Tap = __decorate([
    event("tap")
], Tap);
exports.Tap = Tap;
let DoubleTap = class DoubleTap extends PointEvent {
};
DoubleTap.__name__ = "DoubleTap";
DoubleTap = __decorate([
    event("doubletap")
], DoubleTap);
exports.DoubleTap = DoubleTap;
let Press = class Press extends PointEvent {
};
Press.__name__ = "Press";
Press = __decorate([
    event("press")
], Press);
exports.Press = Press;
let PressUp = class PressUp extends PointEvent {
};
PressUp.__name__ = "PressUp";
PressUp = __decorate([
    event("pressup")
], PressUp);
exports.PressUp = PressUp;
let PanStart = class PanStart extends PointEvent {
};
PanStart.__name__ = "PanStart";
PanStart = __decorate([
    event("panstart")
], PanStart);
exports.PanStart = PanStart;
let PanEnd = class PanEnd extends PointEvent {
};
PanEnd.__name__ = "PanEnd";
PanEnd = __decorate([
    event("panend")
], PanEnd);
exports.PanEnd = PanEnd;
let PinchStart = class PinchStart extends PointEvent {
};
PinchStart.__name__ = "PinchStart";
PinchStart = __decorate([
    event("pinchstart")
], PinchStart);
exports.PinchStart = PinchStart;
let PinchEnd = class PinchEnd extends PointEvent {
};
PinchEnd.__name__ = "PinchEnd";
PinchEnd = __decorate([
    event("pinchend")
], PinchEnd);
exports.PinchEnd = PinchEnd;
let RotateStart = class RotateStart extends PointEvent {
};
RotateStart.__name__ = "RotateStart";
RotateStart = __decorate([
    event("rotatestart")
], RotateStart);
exports.RotateStart = RotateStart;
let RotateEnd = class RotateEnd extends PointEvent {
};
RotateEnd.__name__ = "RotateEnd";
RotateEnd = __decorate([
    event("rotateend")
], RotateEnd);
exports.RotateEnd = RotateEnd;
