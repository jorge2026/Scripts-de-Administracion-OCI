#!/usr/bin/env python3
"""
Script para listar instancias de OCI
Permite visualizar todas las instancias en compartments específicos
"""

import argparse
import sys
from oci_utils import OCIManager, print_section, print_instance_info


def list_compartments(manager):
    """Lista todos los compartments disponibles"""
    print_section("Compartments Disponibles")
    
    compartments = manager.list_compartments()
    
    if not compartments:
        print("❌ No se encontraron compartments")
        return
    
    print(f"📁 Se encontraron {len(compartments)} compartment(s):\n")
    
    for comp in compartments:
        print(f"   • {comp.name}")
        print(f"     ID: {comp.id}")
        print()


def list_instances(manager, compartment_id, state=None):
    """Lista instancias en un compartment"""
    manager.verify_credentials()
    
    instances = manager.list_instances(compartment_id, state)
    
    if not instances:
        print("❌ No se encontraron instancias")
        return
    
    status_icon = "✓"
    status_text = "Se encontraron"
    
    print(f"\n📋 {status_text} {len(instances)} instancia(s):\n")
    
    for i, instance in enumerate(instances, 1):
        print_instance_info(instance, i)
    
    print(f"{'='*100}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Script para listar instancias de OCI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Listar compartments disponibles
  python listar_instancias.py --list-compartments

  # Listar todas las instancias en un compartment
  python listar_instancias.py --compartment-id ocid1.compartment.oc1..xxxxx

  # Listar solo instancias en ejecución
  python listar_instancias.py --compartment-id ocid1.compartment.oc1..xxxxx --estado RUNNING

  # Usar un perfil específico
  python listar_instancias.py --compartment-id ocid1.compartment.oc1..xxxxx --profile PROD
        """
    )
    
    parser.add_argument(
        "--list-compartments",
        action="store_true",
        help="Listar todos los compartments disponibles"
    )
    
    parser.add_argument(
        "--compartment-id",
        type=str,
        help="ID del compartment a listar"
    )
    
    parser.add_argument(
        "--estado",
        type=str,
        choices=["PROVISIONING", "RUNNING", "STARTING", "STOPPING", "STOPPED", "TERMINATED"],
        help="Filtrar por estado de la instancia"
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
        
        if args.list_compartments:
            list_compartments(manager)
        elif args.compartment_id:
            list_instances(manager, args.compartment_id, args.estado)
        else:
            parser.print_help()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
