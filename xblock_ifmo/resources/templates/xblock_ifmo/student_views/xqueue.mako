## -*- coding: utf-8 -*-

<%inherit file="ifmo_xblock_base"/>

<%block name="block_modals">
    ${parent.block_modals()}
    <%include file="xblock_ifmo/modals/_queue_modal.mako" args="**context"/>
</%block>

<%block name="instructor_actions">
    ${parent.instructor_actions()}
    <a class="instructor-info-action" href="#${meta['id']}-queue-info-modal" id="${meta['id']}-queue-info-button">Состояние очереди</a>
</%block>
