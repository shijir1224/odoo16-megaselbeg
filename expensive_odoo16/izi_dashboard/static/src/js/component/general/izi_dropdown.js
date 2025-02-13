// Dropdown, Datepicker and Collapse are not working in Odoo Version 16
// So this is the manual event listener
$(function() {
    $('body').on('click', function(ev) {
        $('.dropdown-menu').hide();
    });
    $('body').on('click', '.dropdown .dropdown-toggle', function(ev) {
        ev.stopPropagation();
        $(ev.currentTarget).parent().find('.dropdown-menu').show();
    });
    $('body').on('click', '.o_datepicker', function(ev) {
        ev.stopPropagation();
        $('.bootstrap-datetime-picker').show();
    });
    $('body').on('click', '[data-toggle="collapse"]', function(ev) {
        ev.stopPropagation();
        elmId = $(ev.currentTarget).data('target');
        if ($(elmId).hasClass('show')) {
            $(elmId).removeClass('show');
        } else {
            $(elmId).addClass('show');
        }
    });
});