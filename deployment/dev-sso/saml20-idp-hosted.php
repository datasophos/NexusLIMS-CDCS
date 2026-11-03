<?php
/** Local test IdP. The checked-in certificate and key are for development only. */
$metadata[rtrim(getenv('SSP_BASE_URL_PATH'), '/') . '/saml2/idp/metadata.php'] = [
    'host' => '__DEFAULT__',
    'privatekey' => 'ca.key',
    'certificate' => 'ca.crt',
    'auth' => 'example-userpass',
];
