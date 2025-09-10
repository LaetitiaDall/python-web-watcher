<?php
/**
 * Plugin Name: Sync Meta Tag
 * Description: Injects <meta name="sync"> with the port from WATCHER_PORT.
 */
add_action('wp_head', function () {
    $wsurl  = '#WSURL#';
    $allow = "true";

    echo '<meta name="sync" data-wsurl="' . esc_attr($wsurl) . '" data-allow="' . esc_attr($allow) . "\" />\n";
}, 999);
