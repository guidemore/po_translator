function setQueryVariable(query, keyString, replaceString) {
    var vars = [];
    var new_vars = [];
    if (query)
        vars = query.split("&");
    var found = false;
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == keyString) {
            vars[i] = pair[0] + "=" + encodeURIComponent(replaceString);
            found = true;
        }
        if ((keyString == 'cur_section') && (pair[0] == 'cur_subsection')) {
            vars[i] = pair[0] + "=" + "";
        }
    }
    if (!found) {
        vars.push(keyString + "=" + encodeURIComponent(replaceString));
    }
    return vars.join("&")
}

function Truncate(str, maxLength) {
    if (str.length > maxLength) {
        str = str.substring(0, maxLength + 1);
        str = str.substring(0, Math.min(str.length, str.lastIndexOf(" ")));
        str = str + '...';
    }
    return str;
}

$(function () {
    $('<div id="ajax-busy"/>').hide().appendTo('body');
    $('#translateModal').modal('hide');

    $(".clickable").click(function () {
        $(".collapse_div.row").hide();
        $(".clickable, .show_prev").show();
        $('.old_values').remove();
        $(this).next().show();
        $(this).hide()
    });

    $(".target_clickable").click(function () {
        var selected_row = $(this).closest("tr");
        var source = selected_row.find('input[name="msg_source"]').attr('value');
        var target = selected_row.find('input[name="msg_target"]').attr('value');
        var id_to_modify = selected_row.find('input[name="id_of_message"]').attr('value');
        var form = $("#translateModal");
        var message_textarea = form.find('textarea[name="msg_str"]');

        form.find('textarea[name="source"]').text(source);
        form.find('select[name="is_translated"]').val('true');
        form.find('input[name="id_of_message"]').attr('value', id_to_modify);
        form.find('.old_values').remove();
        form.find('.show_prev').show();

        $('#translateModal').modal("show");

        // set focus to the end of textarea
        message_textarea.focus();
        message_textarea.text(target);
    });

    $(".permis").click(function () {
        $(".collapse_perm").show();
        $(".permis").hide();

    });

    $(".perm_cancel").click(function () {
        $(".collapse_perm").hide();
        $(".permis").show();

    });

    $('#file').closest('form').hide();
    $(".immediate-upload").click(function () {
        $('#file').change(function () {
            var self = $(this);
            self.closest('form').show();
            self.closest('form').submit();
        });
        $('#file').click();
    });

    $(".show_prev").click(function (event) {
        event.preventDefault();
        var form = $(this).closest("form");
        var url = form.attr('action');
        var token = form.find('input[name="csrfmiddlewaretoken"]').attr('value');
        var id_to_modify = form.find('input[name="id_of_message"]').attr('value');
        var new_text = form.find('textarea[name="msg_str"]').text();

        $.ajax({
            type: "POST",
            url: url,
            contenttype: "application/json; charset=utf-8",
            data: {
                id_of_message: id_to_modify,
                msg_str: new_text,
                action: 'show_prev',
                csrfmiddlewaretoken: token
            },
            beforeSend: function () {
                $('#ajax-busy').show()
            },
            success: function (data) {
                $('#ajax-busy').hide();
                form.find('.old_values').remove();
                result = jQuery.parseJSON(data);
                var previous_values = form.children('div').clone().appendTo(form);
                previous_values.addClass('old_values muted');
                previous_values.find('.source').text(result.prev_source);
                previous_values.find('.target').text(result.prev_target).attr('disabled', 'disabled');
                form.find('.show_prev').hide()
            },
            error: function () {
                $('#ajax-busy').hide();
                alert('some wrong');
            }
        });
    });

    $(".same_target").click(function (event) {
        event.preventDefault();
        var form = $('.popup_form');
        var url = form.find('form').attr('action');
        var token = form.find('input[name="csrfmiddlewaretoken"]').attr('value');
        var id_to_modify = form.find('input[name="id_of_message"]').attr('value');
        var is_trans = $('#is_translated').val();
        var new_text = form.find('textarea[name="msg_str"]').val();
        var selected_row = $('tr').find('input[value=' + id_to_modify + ']').closest("tr");

        $.ajax({
            type: "POST",
            url: url,
            contenttype: "application/json; charset=utf-8",
            data: {
                id_of_message: id_to_modify,
                msg_str: new_text,
                action: 'same_target',
                is_translated: is_trans,
                csrfmiddlewaretoken: token
            },
            beforeSend: function () {
                $("#translateModal").modal("hide");
                $('#ajax-busy').show()
            },
            success: function (data) {
                $('#ajax-busy').hide();
                var result = jQuery.parseJSON(data);
                if (result['saved']) {
                    // hide collapse and show with new value
                    selected_row.find('input[name="is_trans"]').attr('disabled', false);
                    selected_row.find('div[name="is_trans"]').children().remove();
                    if (is_trans == "True") {
                        selected_row.find('div[name="is_trans"]').append('<i class="icon-check"></i>');
                    }
                    selected_row.find('input[name="is_trans"]').attr('disabled', true);
                    selected_row.find('div[name="msg_target"]').text(Truncate(new_text, 45));
                    selected_row.find('input[name="msg_target"]').attr('value', new_text);
                    selected_row.find('input[name="msg_target"]').text(new_text);
                }
                else {
                    alert(result['message']);
                }
            },
            error: function () {
                $('#ajax-busy').hide();
                alert('some wrong');
            }
        });
    });

    $(".inline_cancel").click(function (event) {
        event.preventDefault();
        $("#translateModal").dialog("hide");

    });

    $(".source_cancel").click(function (event) {
        event.preventDefault();
        $(".collapse_div").hide();
        $(".clickable").show()

    });

    $(".new").click(function (event) {
        event.preventDefault();
        var form = $(this).closest("form");
        var prev_tr = $(this).closest("tr");
        var collapse_div = prev_tr.find('div[name="collapse_div"]');
        var clickable_div = prev_tr.find('div[name="clickable"]');
        var url = form.attr('action');
        var token = form.find('input[name="csrfmiddlewaretoken"]').attr('value');
        var id_to_modify = form.find('input[name="id_of_message"]').attr('value');
        var new_text = form.find('textarea[name="msg_str"]').val();

        $.ajax({
            type: "POST",
            url: url,
            contenttype: "application/json; charset=utf-8",
            data: {
                id_of_message: id_to_modify,
                msg_str: new_text,
                action: 'new',
                csrfmiddlewaretoken: token
            },
            beforeSend: function () {
                $('#ajax-busy').show()
            },
            success: function (data) {
                $('#ajax-busy').hide();
                var result = jQuery.parseJSON(data);
                if (result['saved']) {
                    prev_tr.find('div[name="msg_source"]').text(Truncate(new_text, 60));
                    form.find('textarea[name="msg_str"]').text(new_text);
                    clickable_div.show();
                    collapse_div.hide();
                }
                else {
                    alert(result['message']);
                }
            },
            error: function () {
                $('#ajax-busy').hide();
                alert('some wrong');
            }
        });
    });

    $(".same").click(function (event) {
        event.preventDefault();
        var form = $(this).closest("form");
        var prev_tr = $(this).closest("tr");
        var url = form.attr('action');
        var token = form.find('input[name="csrfmiddlewaretoken"]').attr('value');
        var id_to_modify = form.find('input[name="id_of_message"]').attr('value');
        var new_text = form.find('textarea[name="msg_str"]').val();
        var collapse_div = prev_tr.find('div[name="collapse_div"]');
        var clickable_div = prev_tr.find('div[name="clickable"]');

        $.ajax({
            type: "POST",
            url: url,
            contenttype: "application/json; charset=utf-8",
            data: {
                id_of_message: id_to_modify,
                msg_str: new_text,
                action: 'same',
                csrfmiddlewaretoken: token
            },
            beforeSend: function () {
                $('#ajax-busy').show()
            },
            success: function (data) {
                $('#ajax-busy').hide();
                var result = jQuery.parseJSON(data);
                if (result['saved']) {
                    prev_tr.find('div[name="msg_source"]').text(Truncate(new_text, 60));
                    form.find('textarea[name="msg_str"]').text(new_text);

                    clickable_div.show();
                    collapse_div.hide();
                }
                else {
                    alert(result['message']);
                }
            },
            error: function () {
                $('#ajax-busy').hide();
                alert('some wrong');
            }
        });
    });

    if ($(".sel_subsection").find('option').length < 2)
        $(".sel_subsection").hide();

    $(".section").change(function (event) {
        var newValue_section = $(".section").val();
        var url = document.location.pathname + 'get_subsection';
        $.ajax({
            url: url,
            data: {
                cur_section: newValue_section
            },
            beforeSend: function () {
                $('#ajax-busy').show()
            },
            success: function (data) {
                $('#ajax-busy').hide();
                $('option', $(".sel_subsection")).remove();
                var newOption = document.createElement("OPTION");
                newOption.text = "Show all";
                newOption.value = "";
                $(".sel_subsection").append(newOption);
                var result = jQuery.parseJSON(data);
                for (var i = 0; i < result.length; i++) {
                    newOption = document.createElement("OPTION");
                    newOption.text = result[i];
                    newOption.value = result[i];
                    $(".sel_subsection").append(newOption)
                }
                if (result.length) {
                    $(".sel_subsection").show();
                } else {
                    $(".sel_subsection").hide();
                }
            },
            error: function () {
                $('#ajax-busy').hide();
                alert('some wrong');
            }
        });
    });
});
