<?php
/**
 * SimpleSAMLphp auth sources for NexusLIMS dev SSO.
 *
 * Two test users mirror the default CDCS dev accounts created by
 * init_environment.py. SAML_CREATE_UNKNOWN_USER must remain False
 * (the default) so these users must already exist in CDCS.
 *
 * Credentials:
 *   user  / user   -> maps to CDCS 'user' account
 *   admin / admin  -> maps to CDCS 'admin' superuser account
 */
$config = [
    'admin' => [
        'core:AdminPassword',
    ],

    'example-userpass' => [
        'exampleauth:UserPass',

        'user:user' => [
            'uid'       => ['user'],
            'mail'      => ['user@nexuslims-dev.localhost'],
            'givenName' => ['Test'],
            'sn'        => ['User'],
        ],

        'admin:admin' => [
            'uid'       => ['admin'],
            'mail'      => ['admin@nexuslims-dev.localhost'],
            'givenName' => ['Admin'],
            'sn'        => ['User'],
        ],
    ],
];
