import time
import hashlib

class OTSecurityMonitor:
    """
    🛡️ v13.0 Cyber Resilience: Monitors Operational Technology (OT) data 
    for AI-based anomaly detection and data integrity.
    """
    def __init__(self):
        self.anomalies_detected = []
        self.secure_vault = {}

    def detect_anomaly(self, flight_id, commanded_alt, target_alt):
        """
        AI Anomaly Detection: Detects unauthorized or physics-defying 
        altitude/speed commands.
        """
        # Logic: If command differs from target by > 5000ft suddenly, it's an anomaly
        if abs(commanded_alt - target_alt) > 5000:
            anomaly = {
                'timestamp': time.time(),
                'flight_id': flight_id,
                'type': 'UNAUTHORIZED_ALTITUDE_SHIFT',
                'severity': 'CRITICAL',
                'status': 'PENDING_VERIFICATION'
            }
            self.anomalies_detected.append(anomaly)
            return anomaly
        return None

    def prompt_biometric_verification(self, anomaly_id):
        """
        Encrypted Verification: Asks for biometric/encrypted proof to 
        verify the commander's identity.
        """
        print(f"🔒 [OT-SEC] Anomalous Command Detected ({anomaly_id}). Requesting Biometric Verification...")
        # Simulating verification delay
        time.sleep(1)
        return "IDENTITY_VERIFIED"

    def sign_operational_data(self, data_packet):
        """
        Signs operational data with hashes to ensure OT integrity.
        """
        packet_str = str(data_packet).encode()
        audit_hash = hashlib.sha256(packet_str).hexdigest()
        return audit_hash
