#!/usr/bin/env python
"""
Script to run the backend with Gunicorn and SSL certificates.
This script checks for available certificates and uses either:
1. An existing certificate from the trusted root store, or
2. The Root.pem certificate from the Downloads folder
"""
import os
import sys
import logging
import subprocess
import ssl
import certifi
import shutil
from pathlib import Path
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('ssl_setup')

# Constants
ZSCALER_CERT_PATH = str(Path.home() / "Downloads" / "Root.pem")
TEMP_CERT_DIR = tempfile.mkdtemp(prefix="ssl_certs_")
TEMP_CERT_FILE = os.path.join(TEMP_CERT_DIR, "server.crt")
TEMP_KEY_FILE = os.path.join(TEMP_CERT_DIR, "server.key")
PORT = 5050
HOST = '0.0.0.0'

def setup_ssl_certificates():
    """Set up SSL certificates for Gunicorn."""
    # First check if ZScaler certificate exists and prepare environment
    if os.path.exists(ZSCALER_CERT_PATH):
        logger.info(f"Found ZScaler certificate at {ZSCALER_CERT_PATH}")
        
        # Set SSL_CERT_FILE environment variable to point to ZScaler cert
        os.environ['SSL_CERT_FILE'] = ZSCALER_CERT_PATH
        logger.info(f"Set SSL_CERT_FILE to {ZSCALER_CERT_PATH}")
        
        # For Python requests library
        os.environ['REQUESTS_CA_BUNDLE'] = ZSCALER_CERT_PATH
        logger.info(f"Set REQUESTS_CA_BUNDLE to {ZSCALER_CERT_PATH}")
        
        # Create a self-signed certificate for Gunicorn
        create_self_signed_cert()
        return True
    else:
        logger.info("ZScaler certificate not found. Using default certificates.")
        # Create a self-signed certificate using default CA bundle
        create_self_signed_cert()
        return True

def create_self_signed_cert():
    """Create a self-signed certificate for Gunicorn to use."""
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    import datetime
    
    # Generate a private key
    logger.info("Generating private key...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Generate a self-signed certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost")
    ])
    
    logger.info("Creating self-signed certificate...")
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("localhost")]),
        critical=False
    ).sign(private_key, hashes.SHA256())
    
    # Write private key to file
    logger.info(f"Writing private key to {TEMP_KEY_FILE}...")
    with open(TEMP_KEY_FILE, "wb") as key_file:
        key_file.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Write certificate to file
    logger.info(f"Writing certificate to {TEMP_CERT_FILE}...")
    with open(TEMP_CERT_FILE, "wb") as cert_file:
        cert_file.write(cert.public_bytes(serialization.Encoding.PEM))

def run_gunicorn_with_ssl():
    """Run Gunicorn with SSL certificate."""
    try:
        # Gunicorn command with SSL configuration
        cmd = [
            "gunicorn",
            "--certfile", TEMP_CERT_FILE,
            "--keyfile", TEMP_KEY_FILE,
            "--bind", f"{HOST}:{PORT}",
            "--workers", "4",
            "--access-logfile", "-",
            "--error-logfile", "-",
            "wsgi:app"
        ]
        
        logger.info(f"Starting Gunicorn with command: {' '.join(cmd)}")
        subprocess.run(cmd)
    except Exception as e:
        logger.error(f"Error running Gunicorn: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Setup certificates and run Gunicorn
    try:
        # Try to import cryptography - needed for certificate generation
        import cryptography
    except ImportError:
        logger.error("Cryptography package not installed. Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "cryptography"])
    
    success = setup_ssl_certificates()
    if success:
        run_gunicorn_with_ssl()
    else:
        logger.error("Failed to set up SSL certificates.")
        sys.exit(1)
    
    # Cleanup temp files when done
    try:
        logger.info(f"Cleaning up temporary files in {TEMP_CERT_DIR}")
        shutil.rmtree(TEMP_CERT_DIR)
    except Exception as e:
        logger.error(f"Error cleaning up: {e}")
