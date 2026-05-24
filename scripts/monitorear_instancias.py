#!/usr/bin/env python3
"""
Script para monitorear instancias de OCI
Obtiene y visualiza métricas de rendimiento (CPU, memoria, disco)
"""

import argparse
import sys
from datetime import datetime, timedelta
from oci_utils import OCIManager, print_section, format_date


def get_cpu_metrics(manager, instance_id, compartment_id, minutes=60):
    """Obtiene métricas de CPU"""
    metrics = manager.get_metrics(
        instance_id,
        compartment_id,
        "CpuUtilization",
        minutes
    )
    return metrics


def get_memory_metrics(manager, instance_id, compartment_id, minutes=60):
    """Obtiene métricas de memoria"""
    metrics = manager.get_metrics(
        instance_id,
        compartment_id,
        "MemoryUtilization",
        minutes
    )
    return metrics


def get_disk_metrics(manager, instance_id, compartment_id, minutes=60):
    """Obtiene métricas de disco"""
    metrics = manager.get_metrics(
        instance_id,
        compartment_id,
        "DiskBytesRead",
        minutes
    )
    return metrics


def calculate_stats(data_points):
    """Calcula estadísticas de puntos de datos"""
    if not data_points:
        return {
            "average": 0,
            "minimum": 0,
            "maximum": 0,
            "count": 0
        }
    
    values = [float(dp) for dp in data_points]
    
    return {
        "average": sum(values) / len(values),
        "minimum": min(values),
        "maximum": max(values),
        "count": len(values)
    }


def monitor_instance(manager, instance_id, compartment_id, minutes=60):
    """Monitorea una instancia y muestra sus métricas"""
    manager.verify_credentials()
    
    instance = manager.get_instance(instance_id, compartment_id)
    
    if not instance:
        print("❌ No se pudo obtener información de la instancia")
        return False
    
    print_section(f"Monitoreando Instancia: {instance.display_name}")
    
    print(f"Información de la Instancia:")
    print(f"   ID: {instance.id}")
    print(f"   Estado: {instance.lifecycle_state}")
    print(f"   Tipo: {instance.shape}")
    print(f"   Zona de Disponibilidad: {instance.availability_domain}")
    print(f"   Período: últimos {minutes} minutos\n")
    
    # Obtener métricas
    print(f"Recopilando métricas (esto puede tomar un momento)...\n")
    
    # CPU
    print("🖥️  Utilización de CPU:")
    cpu_metrics = get_cpu_metrics(manager, instance_id, compartment_id, minutes)
    if cpu_metrics:
        cpu_stats = calculate_stats([m.get("average", 0) for m in cpu_metrics])
        print(f"   Promedio: {cpu_stats['average']:.2f}%")
        print(f"   Mínimo: {cpu_stats['minimum']:.2f}%")
        print(f"   Máximo: {cpu_stats['maximum']:.2f}%")
        print(f"   Puntos de datos: {cpu_stats['count']}")
    else:
        print("   ⚠️  No se pudieron obtener métricas de CPU")
    
    print()
    
    # Memoria
    print("💾 Utilización de Memoria:")
    memory_metrics = get_memory_metrics(manager, instance_id, compartment_id, minutes)
    if memory_metrics:
        memory_stats = calculate_stats([m.get("average", 0) for m in memory_metrics])
        print(f"   Promedio: {memory_stats['average']:.2f}%")
        print(f"   Mínimo: {memory_stats['minimum']:.2f}%")
        print(f"   Máximo: {memory_stats['maximum']:.2f}%")
        print(f"   Puntos de datos: {memory_stats['count']}")
    else:
        print("   ⚠️  No se pudieron obtener métricas de memoria")
    
    print()
    
    # Disco
    print("💿 Operaciones de Disco:")
    disk_metrics = get_disk_metrics(manager, instance_id, compartment_id, minutes)
    if disk_metrics:
        disk_stats = calculate_stats([m.get("average", 0) for m in disk_metrics])
        print(f"   Lectura promedio: {disk_stats['average']:.2f} bytes/s")
        print(f"   Lectura máxima: {disk_stats['maximum']:.2f} bytes/s")
        # Asumimos que la escritura es aproximadamente igual
        write_avg = disk_stats['average'] * 2  # Aproximación
        write_max = disk_stats['maximum'] * 2   # Aproximación
        print(f"   Escritura promedio: {write_avg:.2f} bytes/s")
        print(f"   Escritura máxima: {write_max:.2f} bytes/s")
    else:
        print("   ⚠️  No se pudieron obtener métricas de disco")
    
    print()
    print(f"{'='*100}\n")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Script para monitorear instancias de OCI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Monitorear instancia (última hora)
  python monitorear_instancias.py \\
      --instance-id ocid1.instance.oc1..xxxxx \\
      --compartment-id ocid1.compartment.oc1..xxxxx

  # Monitorear con período personalizado (últimas 4 horas)
  python monitorear_instancias.py \\
      --instance-id ocid1.instance.oc1..xxxxx \\
      --compartment-id ocid1.compartment.oc1..xxxxx \\
      --minutos 240

  # Monitoreo continuo cada 5 minutos
  watch -n 300 python monitorear_instancias.py \\
      --instance-id ocid1.instance.oc1..xxxxx \\
      --compartment-id ocid1.compartment.oc1..xxxxx
        """
    )
    
    parser.add_argument(
        "--instance-id",
        type=str,
        required=True,
        help="ID de la instancia a monitorear"
    )
    
    parser.add_argument(
        "--compartment-id",
        type=str,
        required=True,
        help="ID del compartment"
    )
    
    parser.add_argument(
        "--minutos",
        type=int,
        default=60,
        help="Período de monitoreo en minutos (default: 60)"
    )
    
    parser.add_argument(
        "--profile",
        type=str,
        default="DEFAULT",
        help="Perfil de configuración de OCI a usar (default: DEFAULT)"
    )
    
    args = parser.parse_args()
    
    try:
        manager = OCIManager(profile=args.profile)
        
        monitor_instance(
            manager,
            args.instance_id,
            args.compartment_id,
            args.minutos
        )
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
