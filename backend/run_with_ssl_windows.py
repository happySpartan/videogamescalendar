#!/usr/bin/env python
"""
Script to run the backend with SSL support on Windows.
This version uses Flask's built-in SSL capabilities instead of Gunicorn.
"""
import os
import sys
import logging
import ssl
import certifi
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('ssl_setup')

# Constants
ZSCALER_CERT_PATH = str(Path.home() / "Downloads" / "Root.pem")
PORT = 5050
HOST = '0.0.0.0'

def setup_ssl_certificates():
    """Set up SSL certificates for Flask."""
    # First check if ZScaler certificate exists and prepare environment
    if os.path.exists(ZSCALER_CERT_PATH):
        logger.info(f"Found ZScaler certificate at {ZSCALER_CERT_PATH}")
        
        # Set SSL_CERT_FILE environment variable to point to ZScaler cert
        os.environ['SSL_CERT_FILE'] = ZSCALER_CERT_PATH
        logger.info(f"Set SSL_CERT_FILE to {ZSCALER_CERT_PATH}")
        
        # For Python requests library
        os.environ['REQUESTS_CA_BUNDLE'] = ZSCALER_CERT_PATH
        logger.info(f"Set REQUESTS_CA_BUNDLE to {ZSCALER_CERT_PATH}")
        
        # Create a self-signed certificate for Flask
        return create_self_signed_cert()
    else:
        logger.info("ZScaler certificate not found. Using default certificates.")
        # Create a self-signed certificate using default CA bundle
        return create_self_signed_cert()

def create_self_signed_cert():
    """Create a self-signed certificate for Flask to use."""
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    import datetime
    import tempfile
    
    # Create temp directory for certificates
    cert_dir = tempfile.mkdtemp(prefix="ssl_certs_")
    cert_file = os.path.join(cert_dir, "server.crt")
    key_file = os.path.join(cert_dir, "server.key")
    
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
        datetime.datetime.now(tz=datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("localhost")]),
        critical=False
    ).sign(private_key, hashes.SHA256())
    
    # Write private key to file
    logger.info(f"Writing private key to {key_file}...")
    with open(key_file, "wb") as key_file_obj:
        key_file_obj.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Write certificate to file
    logger.info(f"Writing certificate to {cert_file}...")
    with open(cert_file, "wb") as cert_file_obj:
        cert_file_obj.write(cert.public_bytes(serialization.Encoding.PEM))
    
    return {
        'cert_dir': cert_dir,
        'cert_file': cert_file,
        'key_file': key_file
    }

def run_flask_with_ssl(ssl_context):
    """Run Flask with SSL support."""
    try:
        # Add the current directory to the path so we can import app modules correctly
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
        
        from app import app
        
        logger.info(f"Starting Flask with SSL on {HOST}:{PORT}")
        app.run(
            host=HOST,
            port=PORT,
            ssl_context=(ssl_context['cert_file'], ssl_context['key_file']),
            debug=False
        )
    except Exception as e:
        logger.error(f"Error running Flask with SSL: {e}")
        sys.exit(1)
    finally:
        # Cleanup temp files when done
        try:
            import shutil
            logger.info(f"Cleaning up temporary files in {ssl_context['cert_dir']}")
            shutil.rmtree(ssl_context['cert_dir'])
        except Exception as e:
            logger.error(f"Error cleaning up: {e}")

if __name__ == "__main__":
    try:
        # Try to import cryptography - needed for certificate generation
        import cryptography
    except ImportError:
        logger.error("Cryptography package not installed. Installing required packages...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "cryptography"])
    
    # Setup certificates and run Flask
    ssl_context = setup_ssl_certificates()
    if ssl_context:
        run_flask_with_ssl(ssl_context)
    else:
        logger.error("Failed to set up SSL certificates.")
        sys.exit(1)
