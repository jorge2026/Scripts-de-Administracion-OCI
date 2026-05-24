#!/usr/bin/env python3
"""
Script para actualizar instancias de OCI
Permite iniciar, detener, reiniciar y renombrar instancias
"""

import argparse
import sys
import time
from oci_utils import OCIManager, format_date, print_section


def show_instance_state(manager, instance_id):
    """Muestra el estado actual de una instancia"""
    instance = manager.get_instance(instance_id, None)
    if instance:
        print(f"   Estado actual: {instance.lifecycle_state}")
        return instance
    return None


def start_instance(manager, instance_id, wait=True):
    """Inicia una instancia detenida"""
    manager.verify_credentials()
    
    print(f"\n🚀 Iniciando instancia...")
    
    instance = show_instance_state(manager, instance_id)
    if not instance:
        print("❌ No se pudo obtener la instancia")
        return False
    
    if instance.lifecycle_state == "RUNNING":
        print("⚠️  La instancia ya está en ejecución")
        return True
    
    if manager.start_instance(instance_id):
        print("   ✓ Solicitud de inicio enviada.")
        
        if wait:
            print("   ⏳ Esperando que la instancia esté en ejecución...")
            if manager.wait_for_instance_state(instance_id, "RUNNING"):
                print("   ✓ Instancia iniciada correctamente.")
                return True
            else:
                print("   ⚠️  Tiempo de espera agotado, pero la solicitud fue aceptada.")
                return True
    
    return False


def stop_instance(manager, instance_id, wait=True):
    """Detiene una instancia en ejecución"""
    manager.verify_credentials()
    
    print(f"\n⏹️  Deteniendo instancia...")
    
    instance = show_instance_state(manager, instance_id)
    if not instance:
        print("❌ No se pudo obtener la instancia")
        return False
    
    if instance.lifecycle_state == "STOPPED":
        print("⚠️  La instancia ya está detenida")
        return True
    
    if manager.stop_instance(instance_id):
        print("   ✓ Solicitud de parada enviada.")
        
        if wait:
            print("   ⏳ Esperando que la instancia se detenga...")
            if manager.wait_for_instance_state(instance_id, "STOPPED"):
                print("   ✓ Instancia detenida correctamente.")
                return True
            else:
                print("   ⚠️  Tiempo de espera agotado, pero la solicitud fue aceptada.")
                return True
    
    return False


def reboot_instance(manager, instance_id, wait=True):
    """Reinicia una instancia"""
    manager.verify_credentials()
    
    print(f"\n🔄 Reiniciando instancia...")
    
    instance = show_instance_state(manager, instance_id)
    if not instance:
        print("❌ No se pudo obtener la instancia")
        return False
    
    if instance.lifecycle_state != "RUNNING":
        print("⚠️  La instancia debe estar en ejecución para reiniciarla")
        return False
    
    if manager.reboot_instance(instance_id):
        print("   ✓ Solicitud de reinicio enviada.")
        
        if wait:
            print("   ⏳ Esperando que la instancia se reinicie...")
            if manager.wait_for_instance_state(instance_id, "RUNNING"):
                print("   ✓ Instancia reiniciada correctamente.")
                return True
            else:
                print("   ⚠️  Tiempo de espera agotado, pero la solicitud fue aceptada.")
                return True
    
    return False


def rename_instance(manager, instance_id, new_name):
    """Renombra una instancia"""
    manager.verify_credentials()
    
    print(f"\n✏️  Renombrando instancia a '{new_name}'...")
    
    instance = show_instance_state(manager, instance_id)
    if not instance:
        print("❌ No se pudo obtener la instancia")
        return False
    
    if manager.update_instance(instance_id, new_name):
        print(f"   ✓ Instancia renombrada a '{new_name}'")
        return True
    
    return False


def get_instance_info(manager, instance_id):
    """Obtiene y muestra información de una instancia"""
    manager.verify_credentials()
    
    instance = manager.get_instance(instance_id, None)
    
    if not instance:
        print("❌ No se pudo obtener información de la instancia")
        return False
    
    print_section(f"Información de Instancia")
    print(f"Nombre: {instance.display_name}")
    print(f"ID: {instance.id}")
    print(f"Estado: {instance.lifecycle_state}")
    print(f"Tipo: {instance.shape}")
    print(f"Zona de Disponibilidad: {instance.availability_domain}")
    print(f"Creada: {format_date(instance.time_created)}")
    print(f"Compartment ID: {instance.compartment_id}")
    
    if instance.public_ip:
        print(f"IP Pública: {instance.public_ip}")
    if instance.private_ip:
        print(f"IP Privada: {instance.private_ip}")
    
    print()
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Script para actualizar instancias de OCI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Iniciar una instancia detenida
  python actualizar_instancias.py --instance-id ocid1.instance.oc1..xxxxx --iniciar

  # Detener una instancia en ejecución
  python actualizar_instancias.py --instance-id ocid1.instance.oc1..xxxxx --detener

  # Reiniciar una instancia
  python actualizar_instancias.py --instance-id ocid1.instance.oc1..xxxxx --reiniciar

  # Cambiar el nombre de una instancia
  python actualizar_instancias.py --instance-id ocid1.instance.oc1..xxxxx --nombre "nuevo-nombre"

  # Ver estado actual
  python actualizar_instancias.py --instance-id ocid1.instance.oc1..xxxxx --estado
        """
    )
    
    parser.add_argument(
        "--instance-id",
        type=str,
        required=True,
        help="ID de la instancia a actualizar"
    )
    
    parser.add_argument(
        "--iniciar",
        action="store_true",
        help="Iniciar la instancia"
    )
    
    parser.add_argument(
        "--detener",
        action="store_true",
        help="Detener la instancia"
    )
    
    parser.add_argument(
        "--reiniciar",
        action="store_true",
        help="Reiniciar la instancia"
    )
    
    parser.add_argument(
        "--nombre",
        type=str,
        help="Renombrar la instancia"
    )
    
    parser.add_argument(
        "--estado",
        action="store_true",
        help="Ver estado actual de la instancia"
    )
    
    parser.add_argument(
        "--profile",
        type=str,
        default="DEFAULT",
        help="Perfil de configuración de OCI a usar (default: DEFAULT)"
    )
    
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="No esperar a que la operación se complete"
    )
    
    args = parser.parse_args()
    
    # Verificar que al menos una acción esté especificada
    if not any([args.iniciar, args.detener, args.reiniciar, args.nombre, args.estado]):
        parser.print_help()
        sys.exit(1)
    
    try:
        manager = OCIManager(profile=args.profile)
        
        wait = not args.no_wait
        
        if args.iniciar:
            start_instance(manager, args.instance_id, wait)
        elif args.detener:
            stop_instance(manager, args.instance_id, wait)
        elif args.reiniciar:
            reboot_instance(manager, args.instance_id, wait)
        elif args.nombre:
            rename_instance(manager, args.instance_id, args.nombre)
        elif args.estado:
            get_instance_info(manager, args.instance_id)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
