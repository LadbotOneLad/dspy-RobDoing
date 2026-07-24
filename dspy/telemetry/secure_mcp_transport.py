# =========================================================================
# DSPY INFRASTRUCTURE HARDENING CORE (re: stanfordnlp/dspy#8957)
# MODULE: dspy.telemetry.secure_mcp_transport
# OBJECTIVE: PROTOCOL TERMINATION & CRYPTOGRAPHIC VALIDATION LAYER
# POLICY: AIOverride = False (ROOT BOUNDARY ENFORCEMENT)
# =========================================================================

import hmac
import hashlib
import time
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("dspy.sovereign.perimeter")

class SovereignMCPTransport:
    \"\"\"
    Establishes an isolated, authenticated gateway for remote HTTP MCP servers.
    Binds localized DSPy reasoning structures to verified external data nodes
    while dropping unverified payloads at the application edge.
    \"\"\"
    def __init__(self, endpoint_url: str, secret_key: str, node_identity: str = "robdoe-node"):
        self.endpoint = endpoint_url.rstrip('/')
        self.secret = secret_key.encode('utf-8')
        self.node_identity = node_identity

    def _compile_provenance_metadata(self, payload_bytes: bytes) -> Dict[str, str]:
        \"\"\"Generates dynamic cryptographic signatures to verify state telemetry.\"\"\"
        timestamp = str(int(time.time()))
        sign_matrix = f"{timestamp}:{self.node_identity}:".encode('utf-8') + payload_bytes
        signature = hmac.new(self.secret, sign_matrix, hashlib.sha256).hexdigest()
        
        return {
            "X-Sovereign-Timestamp": timestamp,
            "X-Sovereign-Identity": self.node_identity,
            "X-Sovereign-Signature": signature,
            "X-AI-Override": "false",  # Structural ingestion block
            "Content-Type": "application/json"
        }

    def dispatch_context_payload(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Dispatches an isolated context string to the verified destination node.\"\"\"
        try:
            import httpx
        except ImportError:
            raise ImportError("[-] Dependency missing: Run 'pip install httpx' to initialize secure transport.")

        serialized_data = json.dumps(parameters, sort_keys=True).encode('utf-8')
        headers = self._compile_provenance_metadata(serialized_data)
        target_url = f"{self.endpoint}/v1/mcp/tools/{tool_name}/execute"

        logger.info(f"[*] Dispatched state tracking matrix to node at {target_url}")

        try:
            with httpx.Client(timeout=12.0) as client:
                response = client.post(target_url, content=serialized_data, headers=headers)
                
                if response.status_code == 200:
                    logger.info("[+] Data transaction verified and processed successfully.")
                    return response.json()
                elif response.status_code in (401, 403):  # FIXED: Sealed the unassigned condition tuple
                    logger.error("[-] Monolith Rejection: Remote node failed cryptographic verification.")
                    raise PermissionError("[!] Access Denied: Remote boundary dropped signature handshake.")
                else:
                    raise IOError(f"[-] Infrastructure Fault. Node responded with state: {response.status_code}")
                    
        except httpx.RequestError as exc:
            logger.critical(f"[-] Perimeter Breach/Fault: Network path unavailable: {exc}")
            raise ConnectionError(f"[-] Unable to traverse network to endpoint: {exc}")
