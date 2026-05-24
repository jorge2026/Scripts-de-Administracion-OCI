#!/usr/bin/env python3
"""
OCI Utilities Module
Proporciona funciones comunes para interactuar con Oracle Cloud Infrastructure (OCI)
"""

import os
import sys
from datetime import datetime
import oci
from oci.config import from_file
from oci.exceptions import ServiceError


class OCIManager:
    """Gestor centralizado para interacciones con OCI"""
    
    def __init__(self, profile="DEFAULT"):
        """
        Inicializa el gestor de OCI
        
        Args:
            profile: Perfil de configuración de OCI a usar
        """
        self.profile = profile
        self.config = None
        self.compute_client = None
        self.monitoring_client = None
        self.identity_client = None
        self._authenticate()
    
    def _authenticate(self):
        """Autentica y configura los clientes de OCI"""
        try:
            config_path = os.path.expanduser("~/.oci/config")
            if not os.path.exists(config_path):
                raise FileNotFoundError(
                    "❌ Archivo de configuración no encontrado en ~/.oci/config\n"
                    "Por favor, configura tus credenciales de OCI primero."
                )
            
            self.config = from_file(config_path, self.profile)
            
            # Inicializar clientes
            self.compute_client = oci.compute.ComputeClient(self.config)
            self.monitoring_client = oci.monitoring.MonitoringClient(self.config)
            self.identity_client = oci.identity.IdentityClient(self.config)
            
            print("✓ Autenticado correctamente con OCI")
            
        except FileNotFoundError as e:
            print(f"❌ {str(e)}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error al autenticar con OCI: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    def verify_credentials(self):
        """Verifica que las credenciales sean válidas"""
        try:
            print("🔐 Verificando credenciales de OCI...")
            user = self.identity_client.get_user(self.config["user"])
            print(f"✓ Autenticado como: {user.data.description}")
            return True
        except ServiceError as e:
            print(f"❌ Error al verificar credenciales: {str(e)}", file=sys.stderr)
            return False
    
    def list_compartments(self, tenancy_id=None):
        """Lista todos los compartments disponibles"""
        try:
            if tenancy_id is None:
                tenancy_id = self.config["tenancy"]
            
            compartments = self.identity_client.list_compartments(
                compartment_id=tenancy_id,
                compartment_id_in_subtree=True
            )
            return compartments.data
        except ServiceError as e:
            print(f"❌ Error al listar compartments: {str(e)}", file=sys.stderr)
            return []
    
    def get_instance(self, instance_id, compartment_id):
        """Obtiene información de una instancia"""
        try:
            instance = self.compute_client.get_instance(instance_id)
            return instance.data
        except ServiceError as e:
            print(f"❌ Error al obtener instancia: {str(e)}", file=sys.stderr)
            return None
    
    def list_instances(self, compartment_id, state=None):
        """Lista instancias en un compartment"""
        try:
            instances = self.compute_client.list_instances(
                compartment_id=compartment_id,
                lifecycle_state=state
            )
            return instances.data
        except ServiceError as e:
            print(f"❌ Error al listar instancias: {str(e)}", file=sys.stderr)
            return []
    
    def start_instance(self, instance_id):
        """Inicia una instancia detenida"""
        try:
            self.compute_client.instance_action(instance_id, "START")
            return True
        except ServiceError as e:
            print(f"❌ Error al iniciar instancia: {str(e)}", file=sys.stderr)
            return False
    
    def stop_instance(self, instance_id):
        """Detiene una instancia en ejecución"""
        try:
            self.compute_client.instance_action(instance_id, "STOP")
            return True
        except ServiceError as e:
            print(f"❌ Error al detener instancia: {str(e)}", file=sys.stderr)
            return False
    
    def reboot_instance(self, instance_id):
        """Reinicia una instancia"""
        try:
            self.compute_client.instance_action(instance_id, "REBOOT")
            return True
        except ServiceError as e:
            print(f"❌ Error al reiniciar instancia: {str(e)}", file=sys.stderr)
            return False
    
    def update_instance(self, instance_id, display_name):
        """Actualiza el nombre de una instancia"""
        try:
            update_details = oci.compute.models.UpdateInstanceDetails(
                display_name=display_name
            )
            self.compute_client.update_instance(instance_id, update_details)
            return True
        except ServiceError as e:
            print(f"❌ Error al actualizar instancia: {str(e)}", file=sys.stderr)
            return False
    
    def get_metrics(self, instance_id, compartment_id, metric_name, minutes=60):
        """Obtiene métricas de una instancia"""
        try:
            query = (
                f"name={metric_name},Namespace=oci_compute,"
                f"resourceId={instance_id}"
            )
            
            end_time = datetime.utcnow()
            start_time = oci.util.to_datetime(
                int((end_time.timestamp() - minutes * 60) * 1000)
            )
            
            metrics = self.monitoring_client.summarize_metrics_data(
                compartment_id=compartment_id,
                summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(
                    query=query,
                    start_time=start_time,
                    end_time=end_time,
                    resolution="1m"
                )
            )
            return metrics.data
        except Exception as e:
            print(f"⚠️  No se pudieron obtener métricas: {str(e)}", file=sys.stderr)
            return []
    
    def wait_for_instance_state(self, instance_id, desired_state, max_retries=30):
        """Espera a que una instancia alcance el estado deseado"""
        import time
        
        for i in range(max_retries):
            instance = self.get_instance(instance_id, None)
            if instance is None:
                return False
            
            if instance.lifecycle_state == desired_state:
                return True
            
            time.sleep(2)
        
        return False


def format_date(date_obj):
    """Formatea una fecha para mostrar"""
    if date_obj is None:
        return "N/A"
    return date_obj.strftime("%Y-%m-%d %H:%M:%S")


def print_section(title):
    """Imprime un encabezado de sección"""
    print(f"\n{'='*100}")
    print(f"  {title}")
    print(f"{'='*100}\n")


def print_instance_info(instance, index=None):
    """Imprime información formateada de una instancia"""
    prefix = f"{index}. " if index else ""
    print(f"{prefix}{instance.display_name}")
    print(f"   ID: {instance.id}")
    print(f"   Estado: {instance.lifecycle_state}")
    print(f"   Tipo: {instance.shape}")
    print(f"   Zona de Disponibilidad: {instance.availability_domain}")
    print(f"   Fecha de Creación: {format_date(instance.time_created)}")
    print()
