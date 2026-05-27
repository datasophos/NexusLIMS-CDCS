<?php
/**
 * CDCS SP metadata for the NexusLIMS dev SimpleSAMLphp IdP.
 *
 * Entity ID, ACS, and SLO are read from env vars set in docker-compose.dev.yml
 * so they automatically follow DOMAIN/SSO_DOMAIN without hardcoding.
 *
 * The 'attributes' block is required to make SimpleSAMLphp release attributes
 * to the SP; without it the SAML assertion arrives with an empty ava: {}.
 */
$metadata[getenv('SIMPLESAMLPHP_SP_ENTITY_ID')] = [
    'attributes' => ['uid', 'mail', 'givenName', 'sn'],
    'attributes.NameFormat' => 'urn:oasis:names:tc:SAML:2.0:attrname-format:basic',
    'attributes.required' => ['uid'],
    'AssertionConsumerService' => [
        [
            'Binding'  => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
            'Location' => getenv('SIMPLESAMLPHP_SP_ASSERTION_CONSUMER_SERVICE'),
            'index'    => 1,
        ],
    ],
    'SingleLogoutService' => [
        [
            'Binding'  => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            'Location' => getenv('SIMPLESAMLPHP_SP_SINGLE_LOGOUT_SERVICE'),
        ],
        [
            'Binding'  => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
            'Location' => getenv('SIMPLESAMLPHP_SP_SINGLE_LOGOUT_SERVICE'),
        ],
    ],
];
