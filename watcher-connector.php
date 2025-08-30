<?php
/**
 * Plugin Name: Sync Meta Tag
 * Description: Injects <meta name="sync"> with the port from WATCHER_PORT.
 */
add_action('wp_head', function () {
    $port  = '#PORT#';
    $allow = "true";

    echo '<meta name="sync" data-port="' . esc_attr($port) . '" data-allow="' . esc_attr($allow) . "\" />\n";
}, 999);
