#!/bin/bash
# Generate self-signed certificates for local development
# Run this once to create persistent certificates that won't regenerate

set -e

CERT_DIR="./certs"
mkdir -p "$CERT_DIR"

# Check if certs already exist
if [ -f "$CERT_DIR/ca.crt" ] && [ -f "$CERT_DIR/server.key" ]; then
    echo "Certificates already exist in $CERT_DIR"
    exit 0
fi

echo "Generating self-signed CA certificate..."

# Generate CA private key
openssl genrsa -out "$CERT_DIR/ca.key" 2048

# Generate CA certificate (valid for 10 years)
openssl req -new -x509 -days 3650 -key "$CERT_DIR/ca.key" -out "$CERT_DIR/ca.crt" \
    -subj "/C=US/ST=State/L=City/O=NexusLIMS/CN=NexusLIMS-Dev-CA"

echo "Generating server certificate signed by CA..."

# Generate server private key
openssl genrsa -out "$CERT_DIR/server.key" 2048

# Generate certificate signing request
openssl req -new -key "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" \
    -subj "/C=US/ST=State/L=City/O=NexusLIMS/CN=nexuslims-dev.localhost"

# Create extensions file for SAN (Subject Alternative Name)
cat > "$CERT_DIR/extensions.txt" << EOF
[v3_req]
subjectAltName = DNS:nexuslims-dev.localhost,DNS:localhost,IP:127.0.0.1
EOF

# Sign the certificate with CA (valid for 10 years)
openssl x509 -req -days 3650 -in "$CERT_DIR/server.csr" \
    -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" -CAcreateserial \
    -out "$CERT_DIR/server.crt" -extensions v3_req -extfile "$CERT_DIR/extensions.txt" -copy_extensions copyall

# Clean up
rm "$CERT_DIR/server.csr" "$CERT_DIR/extensions.txt"

echo ""
echo "✅ Certificates generated successfully!"
echo ""
echo "📍 CA Certificate location: $CERT_DIR/ca.crt"
echo ""
echo "📋 To trust these certificates:"
echo ""
echo "macOS:"
echo "  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain $CERT_DIR/ca.crt"
echo ""
echo "Or import manually:"
echo "  1. Open Keychain Access"
echo "  2. File > Import Items"
echo "  3. Select $CERT_DIR/ca.crt"
echo "  4. Double-click the imported cert and set 'When using this certificate' to 'Always Trust'"
echo ""
