## -*- coding: utf-8 -*-

<%inherit file="ifmo_xblock_base"/>

<%block name="extra_settings">

    ${parent.extra_settings()}

    <li class="field comp-setting-entry">
        <div class="wrapper-comp-setting">
            <label for="input_${id}_queue_name" class="label setting-label">Имя очереди</label>
            <input id="input_${id}_queue_name" class="input setting-input" type="text" name="queue_name" value="<%text><%= queue_name %></%text>" />
        </div>
    </li>

</%block>