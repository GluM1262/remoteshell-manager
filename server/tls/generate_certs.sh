#!/bin/bash
#
# Generate self-signed TLS certificates for RemoteShell
# For production, use certificates from a trusted CA
#

set -e

CERT_DIR="$(dirname "$0")"
DAYS_VALID=365
KEY_SIZE=4096

echo "Generating TLS certificates..."

# Generate private key
openssl genrsa -out "$CERT_DIR/key.pem" $KEY_SIZE

# Generate self-signed certificate
openssl req -new -x509 \
    -key "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -days $DAYS_VALID \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Set permissions
chmod 600 "$CERT_DIR/key.pem"
chmod 644 "$CERT_DIR/cert.pem"

echo "Certificates generated successfully:"
echo "  Certificate: $CERT_DIR/cert.pem"
echo "  Private key: $CERT_DIR/key.pem"
echo
echo "⚠️  These are self-signed certificates for development/testing."
echo "⚠️  For production, obtain certificates from a trusted CA (Let's Encrypt, etc.)"
