"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const logging_1 = require("../logging");
class ImageLoader {
    constructor(url, options = {}) {
        this._image = new Image();
        this._finished = false;
        const { attempts = 1, timeout = 1 } = options;
        this.promise = new Promise((resolve, _reject) => {
            this._image.crossOrigin = "anonymous";
            let retries = 0;
            this._image.onerror = () => {
                if (++retries == attempts) {
                    const message = `unable to load ${url} image after ${attempts} attempts`;
                    logging_1.logger.warn(message);
                    if (this._image.crossOrigin != null) {
                        logging_1.logger.warn(`attempting to load ${url} without a cross origin policy`);
                        this._image.crossOrigin = null;
                        retries = 0;
                    }
                    else {
                        if (options.failed != null)
                            options.failed();
                        // reject(new Error(message))
                    }
                }
                setTimeout(() => this._image.src = url, timeout);
            };
            this._image.onload = () => {
                this._finished = true;
                if (options.loaded != null)
                    options.loaded(this._image);
                resolve(this._image);
            };
            this._image.src = url;
        });
    }
    get finished() {
        return this._finished;
    }
    get image() {
        return this._image;
    }
}
exports.ImageLoader = ImageLoader;
ImageLoader.__name__ = "ImageLoader";
