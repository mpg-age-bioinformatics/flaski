"use strict";
// Based on https://github.com/phosphorjs/phosphor/blob/master/packages/signaling/src/index.ts
Object.defineProperty(exports, "__esModule", { value: true });
const data_structures_1 = require("./util/data_structures");
const callback_1 = require("./util/callback");
const array_1 = require("./util/array");
class Signal {
    constructor(sender, name) {
        this.sender = sender;
        this.name = name;
    }
    connect(slot, context = null) {
        if (!receiversForSender.has(this.sender)) {
            receiversForSender.set(this.sender, []);
        }
        const receivers = receiversForSender.get(this.sender);
        if (findConnection(receivers, this, slot, context) != null) {
            return false;
        }
        const receiver = context || slot;
        if (!sendersForReceiver.has(receiver)) {
            sendersForReceiver.set(receiver, []);
        }
        const senders = sendersForReceiver.get(receiver);
        const connection = { signal: this, slot, context };
        receivers.push(connection);
        senders.push(connection);
        return true;
    }
    disconnect(slot, context = null) {
        const receivers = receiversForSender.get(this.sender);
        if (receivers == null || receivers.length === 0) {
            return false;
        }
        const connection = findConnection(receivers, this, slot, context);
        if (connection == null) {
            return false;
        }
        const receiver = context || slot;
        const senders = sendersForReceiver.get(receiver);
        connection.signal = null;
        scheduleCleanup(receivers);
        scheduleCleanup(senders);
        return true;
    }
    emit(args) {
        const receivers = receiversForSender.get(this.sender) || [];
        for (const { signal, slot, context } of receivers) {
            if (signal === this) {
                slot.call(context, args, this.sender);
            }
        }
    }
}
exports.Signal = Signal;
Signal.__name__ = "Signal";
class Signal0 extends Signal {
    emit() {
        super.emit(undefined);
    }
}
exports.Signal0 = Signal0;
Signal0.__name__ = "Signal0";
(function (Signal) {
    function disconnectBetween(sender, receiver) {
        const receivers = receiversForSender.get(sender);
        if (receivers == null || receivers.length === 0)
            return;
        const senders = sendersForReceiver.get(receiver);
        if (senders == null || senders.length === 0)
            return;
        for (const connection of senders) {
            if (connection.signal == null)
                return;
            if (connection.signal.sender === sender)
                connection.signal = null;
        }
        scheduleCleanup(receivers);
        scheduleCleanup(senders);
    }
    Signal.disconnectBetween = disconnectBetween;
    function disconnectSender(sender) {
        const receivers = receiversForSender.get(sender);
        if (receivers == null || receivers.length === 0)
            return;
        for (const connection of receivers) {
            if (connection.signal == null)
                return;
            const receiver = connection.context || connection.slot;
            connection.signal = null;
            scheduleCleanup(sendersForReceiver.get(receiver));
        }
        scheduleCleanup(receivers);
    }
    Signal.disconnectSender = disconnectSender;
    function disconnectReceiver(receiver) {
        const senders = sendersForReceiver.get(receiver);
        if (senders == null || senders.length === 0)
            return;
        for (const connection of senders) {
            if (connection.signal == null)
                return;
            const sender = connection.signal.sender;
            connection.signal = null;
            scheduleCleanup(receiversForSender.get(sender));
        }
        scheduleCleanup(senders);
    }
    Signal.disconnectReceiver = disconnectReceiver;
    function disconnectAll(obj) {
        const receivers = receiversForSender.get(obj);
        if (receivers != null && receivers.length !== 0) {
            for (const connection of receivers) {
                connection.signal = null;
            }
            scheduleCleanup(receivers);
        }
        const senders = sendersForReceiver.get(obj);
        if (senders != null && senders.length !== 0) {
            for (const connection of senders) {
                connection.signal = null;
            }
            scheduleCleanup(senders);
        }
    }
    Signal.disconnectAll = disconnectAll;
})(Signal = exports.Signal || (exports.Signal = {}));
function Signalable(Base) {
    // XXX: `class Foo extends Signalable(Object)` doesn't work (compiles, but fails at runtime), so
    // we have to do this to allow signalable classes without an explict base class.
    if (Base != null) {
        return class extends Base {
            connect(signal, slot) {
                return signal.connect(slot, this);
            }
            disconnect(signal, slot) {
                return signal.disconnect(slot, this);
            }
        };
    }
    else {
        return class {
            connect(signal, slot) {
                return signal.connect(slot, this);
            }
            disconnect(signal, slot) {
                return signal.disconnect(slot, this);
            }
        };
    }
}
exports.Signalable = Signalable;
var _Signalable;
(function (_Signalable) {
    function connect(signal, slot) {
        return signal.connect(slot, this);
    }
    _Signalable.connect = connect;
    function disconnect(signal, slot) {
        return signal.disconnect(slot, this);
    }
    _Signalable.disconnect = disconnect;
})(_Signalable = exports._Signalable || (exports._Signalable = {}));
const receiversForSender = new WeakMap();
const sendersForReceiver = new WeakMap();
function findConnection(conns, signal, slot, context) {
    return array_1.find(conns, conn => conn.signal === signal && conn.slot === slot && conn.context === context);
}
const dirtySet = new data_structures_1.Set();
function scheduleCleanup(connections) {
    if (dirtySet.size === 0) {
        callback_1.defer(cleanupDirtySet);
    }
    dirtySet.add(connections);
}
function cleanupDirtySet() {
    dirtySet.forEach((connections) => {
        array_1.remove_by(connections, (connection) => connection.signal == null);
    });
    dirtySet.clear();
}
