/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2ManyBinaryField } from '@web/views/fields/many2many_binary/many2many_binary_field';
import { useService } from "@web/core/utils/hooks";

patch(Many2ManyBinaryField.prototype, 'web_many2many_attachment_preview_knk', {
    setup() {
        this._super(...arguments);
        this.messaging = useService("messaging");
        this.dialog = useService("dialog");
    },
    onClickAttachmentPreview(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var self = this;
        var activeAttachmentID = $(ev.currentTarget).find('.o_image_box').data('id');
        var currentTarget = $(ev.currentTarget);
        var $el = $(ev.currentTarget).parents('.o_attachments').find('.o_attachment');
        var allAttachments = [];
        if (activeAttachmentID) {
            $.each($el, function() {
                allAttachments.push(self.messaging.modelManager.models["Attachment"].insert({
                    "filename": $(this).attr('title'),
                    "id": $(this).find('.o_image_box').data('id'),
                    "mimetype": $(this).find('.o_image_box a span').attr('data-mimetype'),
                    "name": $(this).find('.o_image_box').attr('data-tooltip'),
                    "isViewable": true,
                }));
            });
            this.messaging.get().then((messaging) => {
                const attachmentList = messaging.models["AttachmentList"].insert({
                    isInChatter: true,
                    Many2manyAttachmentPreview: true,
                    attachmentListViewDialog: {},
                    attachments: allAttachments,
                    selectedAttachment: messaging.models["Attachment"].insert({
                        id: activeAttachmentID,
                        filename: currentTarget.attr('title'),
                        name: currentTarget.find('.o_image_box').attr('data-tooltip'),
                        mimetype: currentTarget.find('.o_image_box a span').attr('data-mimetype'),
                    }),
                });
                this.dialog = messaging.models["Dialog"].insert({
                    attachmentListOwnerAsAttachmentView: attachmentList,
                });
            });
        }
    }
});