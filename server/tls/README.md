# TLS/SSL Configuration

## Self-Signed Certificates (Development)

Generate self-signed certificates:

```bash
cd server/tls
./generate_certs.sh
```

## Production Certificates

### Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem tls/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem tls/key.pem
sudo chown remoteshell:remoteshell tls/*.pem
sudo chmod 600 tls/key.pem
```

### Custom CA Certificate

If using a custom CA:

```bash
# Set CA certificate path in config
TLS_CA_PATH=/path/to/ca-cert.pem
```

## Enable TLS

In `server/.env`:

```bash
USE_TLS=true
TLS_CERT_PATH=tls/cert.pem
TLS_KEY_PATH=tls/key.pem
```

## Client Configuration

In `client/config.yaml`:

```yaml
server:
  use_ssl: true
  
security:
  validate_ssl: true  # Set to false for self-signed certs (dev only)
```

## Verify TLS

Test connection:

```bash
openssl s_client -connect localhost:8000 -showcerts
```

## Certificate Renewal

### Let's Encrypt Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Set up auto-renewal (cron)
0 0 * * * certbot renew --post-hook "systemctl restart remoteshell-server"
```

### Manual Renewal

For self-signed certificates, regenerate before expiry:

```bash
./generate_certs.sh
sudo systemctl restart remoteshell-server
```

## Security Notes

- **Always use TLS in production** to encrypt WebSocket traffic
- **Validate SSL certificates** in client configuration
- **Use strong key sizes** (minimum 2048-bit, recommended 4096-bit)
- **Keep private keys secure** with 600 permissions
- **Rotate certificates** before expiry
- **Use trusted CAs** (Let's Encrypt, DigiCert, etc.) for production
