<?php
/**
 * CDCS SP metadata for the NexusLIMS dev SimpleSAMLphp IdP.
 *
 * Entity ID = the SP metadata URL published by djangosaml2.
 * ACS = assertion consumer service (where SimpleSAMLphp POSTs the assertion).
 * SLS = single logout service.
 */
$metadata['https://nexuslims-dev.localhost/saml2/metadata/'] = [
    'AssertionConsumerService' => [
        [
            'Binding'  => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
            'Location' => 'https://nexuslims-dev.localhost/saml2/acs/',
            'index'    => 1,
        ],
    ],
    'SingleLogoutService' => [
        [
            'Binding'  => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            'Location' => 'https://nexuslims-dev.localhost/saml2/ls/',
        ],
        [
            'Binding'  => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
            'Location' => 'https://nexuslims-dev.localhost/saml2/ls/post/',
        ],
    ],
];
