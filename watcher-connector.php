<?php
/**
 * Plugin Name: Sync Meta Tag
 * Description: Injects <meta name="sync"> with the port from WATCHER_PORT.
 */
add_action('wp_head', function () {
    $port  = getenv('WATCHER_PORT') ?: getenv('WS_PORT') ?: '12345';
    $allow = getenv('WATCHER_ALLOW') ?: 'true';

    // sanitize
    $p = (int) $port;
    if ($p < 1 || $p > 65535) { $p = 12345; }

    echo '<meta name="sync" data-port="' . esc_attr((string)$p) . '" data-allow="' . esc_attr($allow) . "\" />\n";
}, 999);
