/** @odoo-module **/

import { registerPatch } from '@mail/model/model_core';
import { attr, one } from '@mail/model/model_field';

registerPatch({
    name: 'AttachmentList',
    fields: {
        attachments: {
            compute() {
                if (this.Many2manyAttachmentPreview) {
                    return this.attachments;
                }
                return this._super();
            },
        },
        Many2manyAttachmentPreview: attr({
            default: false
        }),
    },
});

registerPatch({
    name: 'AttachmentImage',
    fields: {
        height: {
            compute() {
                if (!this.attachmentList) {
                    return clear();
                } else {
                    if (this.attachmentList.Many2manyAttachmentPreview) {
                        return 300;
                    }
                }
                return this._super();
            },
        },
    },
});