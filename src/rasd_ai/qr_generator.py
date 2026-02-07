"""
QR Code generator module for RASD demo.

Generates a QR code linking to the project repository.
"""

import qrcode

from rasd_ai.config.paths import PATHS

DEMO_URL = "https://github.com/404AliOnFire/RASD-NYUAD2026"


def generate_qr_code(url: str = DEMO_URL) -> None:
    """
    Generate a QR code image for the given URL.

    Args:
        url: The URL to encode in the QR code.
    """
    img = qrcode.make(url)
    output_path = PATHS.outputs / "RASD_DEMO_QR.png"
    img.save(output_path)
    print(f"✅ QR saved as {output_path}")


if __name__ == "__main__":
    generate_qr_code()
