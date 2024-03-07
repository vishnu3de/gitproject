/**@odoo-module */
import core from 'web.core';
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
const { Component, onMounted, useState } = owl;
import { registry } from "@web/core/registry";
const actionRegistry = registry.category("actions");
const rpc = require('web.rpc');
var qweb = core.qweb;

const SystrayWidget = Widget.extend({
    template: 'IconSystrayDropdown',
    events: {
        'click .o-dropdown': '_onClick',
        "click .search-button": "searchModule",
    },

    _onClick: function (ev) {
        let dropBox = $(ev.currentTarget.parentElement).find('#systray_notif');
        if (dropBox[0].style.display == 'block') {
            dropBox[0].style.display = 'none';
        } else {
            dropBox[0].style.display = 'block';
            this.fetchModules();
        }
        $('.systray_notification').html((qweb.render("SystrayDetails")));
    },

    searchModule: function () {
        var moduleName = $('#moduleSelect').val();
        this.handleModuleName(moduleName);
    },

    handleModuleName: function (moduleName) {
        var domain = ['name','=',moduleName];

        this._rpc({
            model: 'ir.module.module',
            method: 'search',
            args: [[domain]],
        }).then(function(result){
            if (result.length > 0) {
                var moduleId = result;
                window.location.href = '/web#id=' + moduleId + '&model=ir.module.module&view_type=form';
            } else {
                alert('Module not found: ' + moduleName);
            }
        });
    },

    fetchModules: function () {
        var self = this;
        this._rpc({
            model: 'ir.module.module',
            method: 'search_read',
            fields: ['name'],
        }).then(function(result){
            var moduleSelect = $('#moduleSelect');
            moduleSelect.empty();
            result.forEach(function(module) {
                moduleSelect.append($('<option>', {
                    value: module.name,
                    text: module.name
                }));
            });

            moduleSelect.select2();

            moduleSelect.on('change', function (e) {
                var selectedModuleName = $(this).val();
                self.handleModuleName(selectedModuleName);
            });
        });
    }
});

$(document).mousedown(function (e) {
    if ($(e.target).closest("#systray_notif").length === 0) {
        $("#systray_notif").hide();
    }
});

SystrayMenu.Items.push(SystrayWidget);
export default SystrayWidget;
