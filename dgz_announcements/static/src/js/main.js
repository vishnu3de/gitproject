odoo.define('dgz_announcements.custom_script', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var rpc = require('web.rpc');
    var session = require('web.session');

    $(document).ready(function() {
        window.addAnnouncementToUser = function(announcementId) {
            rpc.query({
                model: 'dgz.announcements',
                method: 'write',
                args: [[announcementId], {
                    'announcement_ids': [[4, session.uid]]
                }],
            }).then(function () {
            });
        };

        var addAnnouncementsDiv = function () {
        var newDiv = $('<div/>', {
                'id': 'customDiv',
                'css': {
                    'color': 'white',
                    'margin-bottom': '0px',
                },
                'class': 'alert'
            });

            var customCSS = '<style>' +
                '.closebtn {' +
                '   margin-left: 15px;' +
                '   color: white;' +
                '   -webkit-text-stroke: 2px black;' +
                '   text-stroke: 2px black;'+
                '   font-weight: bold;' +
                '   float: right;' +
                '   font-size: 22px;' +
                '   line-height: 20px;' +
                '   cursor: pointer;' +
                '   transition: 0.3s;' +
                '}' +
                '.closebtn:hover {' +
                '   color: black;' +
                '}' +
                '</style>';

            $('head').append(customCSS);
            var existingAnnouncementIds = [];

            var refreshAnnouncements = function() {
                rpc.query({
                    model: 'dgz.announcements',
                    method: 'search_read',
                    args: [[['active_state', '=', true],['scheduled_date', '<=', new Date()]]],
                }).then(function (announcementResult) {
                    if (announcementResult && announcementResult.length > 0) {
                        for (var i = 0; i < announcementResult.length; i++) {
                            var announcement = announcementResult[i];
                            var announcementId = announcement.id;

                            // Check if announcement has already been displayed
                            if (existingAnnouncementIds.includes(announcementId)) {
                                continue;
                            }

                            var dgzAnnouncement = announcement.announcement;
                            var userAnnouncements = announcement.announcement_ids;
                            var color = announcement.bg_color;
                            var fontcolor = announcement.font_color;
                            var url = announcement.url_link;

                            var announcementExists = userAnnouncements.includes(session.uid);

                            if (!announcementExists) {
                                var newDiv = $('<div></div>');
                                var htmlString = '<strong>' + dgzAnnouncement + '</strong>';

                                if (url) {
                                    htmlString += ' <a href="' + url + '" target="_blank">Link!!</a>';
                                }

                                htmlString += '<span class="closebtn" onclick="this.parentElement.style.display=\'none\'; addAnnouncementToUser(' + announcementId + ');">&times;</span>';

                                newDiv.html(htmlString);
                                newDiv.css('background-color', color);
                                newDiv.css('color', fontcolor);
                                newDiv.css('padding', '10px');
                                newDiv.css('text-align', 'center');
                                var man = $('.o_action_manager');
                                man.before(newDiv);

                                existingAnnouncementIds.push(announcementId);
                            }
                        }
                    }
                });
            };

            setInterval(refreshAnnouncements, 5000);

            refreshAnnouncements();
        };

        var checkIfContentLoaded = function () {
            var oActionManager = $('.o_action_manager');
            if (oActionManager.length > 0) {
                addAnnouncementsDiv();
            } else {
                setTimeout(checkIfContentLoaded, 500);
            }
        };

        checkIfContentLoaded();
    });
});
