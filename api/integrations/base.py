"""
Integration Framework for TAZARA AI System
Provides base classes and implementations for external system integrations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IntegrationConfig:
    """Configuration for external integrations"""
    name: str
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3
    enabled: bool = True

class BaseIntegration(ABC):
    """Base class for all external system integrations"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_connected = False
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
        
    async def connect(self) -> bool:
        """Establish connection to external system"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        
        try:
            # Test connection
            async with self.session.get(f"{self.config.base_url}/health") as response:
                if response.status == 200:
                    self.is_connected = True
                    logger.info(f"✅ Connected to {self.config.name}")
                    return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to {self.config.name}: {e}")
            
        return False
    
    async def disconnect(self):
        """Close connection to external system"""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_connected = False
        logger.info(f"🔌 Disconnected from {self.config.name}")
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to external system"""
        if not self.is_connected:
            raise ConnectionError(f"Not connected to {self.config.name}")
        
        url = f"{self.config.base_url}{endpoint}"
        headers = {}
        
        if self.config.api_key:
            headers['Authorization'] = f"Bearer {self.config.api_key}"
        
        for attempt in range(self.config.retry_attempts):
            try:
                async with self.session.request(method, url, json=data, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Attempt {attempt + 1} failed: {response.status}")
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} error: {e}")
                if attempt == self.config.retry_attempts - 1:
                    raise
        
        raise Exception(f"Failed to complete request after {self.config.retry_attempts} attempts")
    
    @abstractmethod
    async def send_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data to external system"""
        pass
    
    @abstractmethod
    async def receive_data(self) -> Dict[str, Any]:
        """Receive data from external system"""
        pass

class ERPIntegration(BaseIntegration):
    """Integration with ERP systems (SAP, Oracle, etc.)"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.erp_type = config.name.lower()
    
    async def send_schedule_data(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send schedule data to ERP system"""
        endpoint = "/api/schedules"
        try:
            result = await self._make_request("POST", endpoint, schedule_data)
            logger.info(f"📤 Schedule data sent to {self.config.name}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to send schedule data: {e}")
            raise
    
    async def get_inventory_levels(self) -> Dict[str, Any]:
        """Get current inventory levels from ERP"""
        endpoint = "/api/inventory"
        try:
            result = await self._make_request("GET", endpoint)
            logger.info(f"📥 Inventory data received from {self.config.name}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to get inventory data: {e}")
            raise
    
    async def update_cargo_status(self, cargo_id: str, status: str) -> Dict[str, Any]:
        """Update cargo status in ERP system"""
        endpoint = f"/api/cargo/{cargo_id}/status"
        data = {"status": status, "updated_at": datetime.now().isoformat()}
        try:
            result = await self._make_request("PUT", endpoint, data)
            logger.info(f"🔄 Cargo status updated in {self.config.name}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to update cargo status: {e}")
            raise
    
    async def send_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send general data to ERP"""
        return await self.send_schedule_data(data)
    
    async def receive_data(self) -> Dict[str, Any]:
        """Receive data from ERP"""
        return await self.get_inventory_levels()

class IoTIntegration(BaseIntegration):
    """Integration with IoT sensors and monitoring systems"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.sensor_data_cache = {}
    
    async def get_train_location(self, train_id: str) -> Dict[str, Any]:
        """Get real-time train location from IoT sensors"""
        endpoint = f"/api/trains/{train_id}/location"
        try:
            result = await self._make_request("GET", endpoint)
            logger.info(f"📍 Location data received for train {train_id}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to get train location: {e}")
            raise
    
    async def get_sensor_readings(self, sensor_type: str) -> Dict[str, Any]:
        """Get sensor readings (temperature, weight, etc.)"""
        endpoint = f"/api/sensors/{sensor_type}"
        try:
            result = await self._make_request("GET", endpoint)
            logger.info(f"🌡️ Sensor data received for {sensor_type}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to get sensor readings: {e}")
            raise
    
    async def send_maintenance_alert(self, train_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send maintenance alert to IoT system"""
        endpoint = f"/api/trains/{train_id}/alerts"
        try:
            result = await self._make_request("POST", endpoint, alert_data)
            logger.info(f"🚨 Maintenance alert sent for train {train_id}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to send maintenance alert: {e}")
            raise
    
    async def send_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data to IoT system"""
        return await self.send_maintenance_alert(data.get('train_id', ''), data)
    
    async def receive_data(self) -> Dict[str, Any]:
        """Receive data from IoT sensors"""
        return await self.get_sensor_readings('all')

class PaymentIntegration(BaseIntegration):
    """Integration with payment gateways and financial systems"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.payment_gateway = config.name.lower()
    
    async def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment transaction"""
        endpoint = "/api/payments"
        try:
            result = await self._make_request("POST", endpoint, payment_data)
            logger.info(f"💳 Payment processed via {self.config.name}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to process payment: {e}")
            raise
    
    async def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get payment transaction status"""
        endpoint = f"/api/payments/{transaction_id}/status"
        try:
            result = await self._make_request("GET", endpoint)
            logger.info(f"📊 Payment status retrieved for {transaction_id}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to get payment status: {e}")
            raise
    
    async def refund_payment(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        """Process payment refund"""
        endpoint = f"/api/payments/{transaction_id}/refund"
        data = {"amount": amount, "reason": "Service disruption"}
        try:
            result = await self._make_request("POST", endpoint, data)
            logger.info(f"💰 Refund processed for {transaction_id}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to process refund: {e}")
            raise
    
    async def send_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send payment data"""
        return await self.process_payment(data)
    
    async def receive_data(self) -> Dict[str, Any]:
        """Receive payment data"""
        return {"message": "Payment integration ready"}

class IntegrationManager:
    """Manages all external integrations"""
    
    def __init__(self):
        self.integrations: Dict[str, BaseIntegration] = {}
        self.configs: Dict[str, IntegrationConfig] = {}
    
    def register_integration(self, integration: BaseIntegration):
        """Register an integration"""
        self.integrations[integration.config.name] = integration
        logger.info(f"📝 Registered integration: {integration.config.name}")
    
    async def connect_all(self):
        """Connect all registered integrations"""
        for name, integration in self.integrations.items():
            if integration.config.enabled:
                await integration.connect()
    
    async def disconnect_all(self):
        """Disconnect all integrations"""
        for name, integration in self.integrations.items():
            await integration.disconnect()
    
    async def send_to_all(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data to all connected integrations"""
        results = {}
        for name, integration in self.integrations.items():
            if integration.is_connected:
                try:
                    result = await integration.send_data(data)
                    results[name] = {"status": "success", "data": result}
                except Exception as e:
                    results[name] = {"status": "error", "message": str(e)}
        return results
    
    def get_integration(self, name: str) -> Optional[BaseIntegration]:
        """Get specific integration by name"""
        return self.integrations.get(name)

# Example usage and configuration
def create_integration_configs() -> Dict[str, IntegrationConfig]:
    """Create integration configurations"""
    return {
        "erp_system": IntegrationConfig(
            name="erp_system",
            base_url="https://erp.tazara.rail/api",
            api_key="your-erp-api-key",
            timeout=30,
            enabled=True
        ),
        "iot_sensors": IntegrationConfig(
            name="iot_sensors",
            base_url="https://iot.tazara.rail/api",
            api_key="your-iot-api-key",
            timeout=10,
            enabled=True
        ),
        "payment_gateway": IntegrationConfig(
            name="payment_gateway",
            base_url="https://payments.tazara.rail/api",
            api_key="your-payment-api-key",
            timeout=15,
            enabled=False  # Disabled until needed
        )
    }

async def setup_integrations() -> IntegrationManager:
    """Setup all integrations"""
    manager = IntegrationManager()
    configs = create_integration_configs()
    
    # Create integration instances
    erp_integration = ERPIntegration(configs["erp_system"])
    iot_integration = IoTIntegration(configs["iot_sensors"])
    payment_integration = PaymentIntegration(configs["payment_gateway"])
    
    # Register integrations
    manager.register_integration(erp_integration)
    manager.register_integration(iot_integration)
    manager.register_integration(payment_integration)
    
    # Connect all integrations
    await manager.connect_all()
    
    return manager

# Example usage
async def example_usage():
    """Example of how to use the integration framework"""
    manager = await setup_integrations()
    
    try:
        # Send schedule data to all connected systems
        schedule_data = {
            "schedule_id": "schedule_123",
            "trains": 6,
            "cargo": 3000,
            "routes": ["DAR_KAPIRI", "DAR_MBEYA"]
        }
        
        results = await manager.send_to_all(schedule_data)
        print("Integration results:", results)
        
        # Get specific integration
        erp = manager.get_integration("erp_system")
        if erp and erp.is_connected:
            inventory = await erp.get_inventory_levels()
            print("Inventory levels:", inventory)
            
    finally:
        await manager.disconnect_all()

if __name__ == "__main__":
    asyncio.run(example_usage())
