from __future__ import annotations

import re
from typing import Dict, List, Tuple

from django.core.management.base import BaseCommand
from django.db import transaction

from auditoria.models import Actividad
from inventario.templatetags.format_numbers import format_money
from ventas.models import Fiado


class Command(BaseCommand):
    help = (
        "Normaliza actividades antiguas de actualización de Fiado. "
        "Ej: 'Actualización Fiado id=5 por usuario: saldo: ...; estado: ...' -> 'Fiado <Cliente> por usuario: Saldo: ...; Estado: ...'"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Aplica los cambios (por defecto solo muestra lo que haría).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Límite de actividades a modificar (0 = sin límite).",
        )

    def handle(self, *args, **options):
        apply_changes: bool = bool(options.get("apply"))
        limit: int = int(options.get("limit") or 0)

        # Captura id y (opcional) ' por usuario' y el resto de cambios
        # Ejemplos vistos:
        # - Actualización Fiado id=5 por mundaca: saldo: '1500' -> '0'; estado: 'ABIERTO' -> 'PAGADO'
        # - Actualización Fiado id=5: saldo: ...
        re_base = re.compile(
            r"^Actualizaci\w*\s+Fiado\s+id=(\d+)(\s+por\s+[^:]+)?\s*:\s*(.*)$",
            re.IGNORECASE,
        )

        qs = Actividad.objects.filter(tipo_accion="EDICION_REGISTRO", descripcion__icontains="Actualiz")

        candidates: List[Tuple[Actividad, int, str, str]] = []
        fiado_ids: List[int] = []
        for a in qs.only("id", "descripcion"):
            desc = (a.descripcion or "").strip()
            m = re_base.match(desc)
            if not m:
                continue
            fiado_id = int(m.group(1))
            # Mantener el espacio inicial de " por usuario" si viene
            user_part = (m.group(2) or "").rstrip()
            # Normalizar whitespace por si el texto histórico tuvo saltos de línea
            changes_part = re.sub(r"\s+", " ", (m.group(3) or "")).strip()
            candidates.append((a, fiado_id, user_part, changes_part))
            fiado_ids.append(fiado_id)

        fiados_map: Dict[int, Fiado] = {
            f.pk: f for f in Fiado.objects.filter(pk__in=fiado_ids).only("id", "cliente_nombre")
        }

        cambios: List[Tuple[Actividad, str]] = []

        def _fmt_money_any(val: str) -> str:
            try:
                return format_money(val)
            except Exception:
                return val

        # repara cada item del tipo "saldo: '1500' -> '0'"
        item_re = re.compile(r"^(\w+)\s*:\s*'([^']*)'\s*->\s*'([^']*)'$", re.IGNORECASE)

        for act, fiado_id, user_part, changes_part in candidates:
            fiado = fiados_map.get(fiado_id)
            if not fiado:
                continue
            cliente = (fiado.cliente_nombre or "").strip()
            if not cliente:
                continue

            items = [s.strip() for s in changes_part.split(';') if s.strip()]
            parts_readable: List[str] = []
            for it in items:
                m = item_re.match(it)
                if not m:
                    continue
                field = m.group(1).strip().lower()
                old_val = m.group(2)
                new_val = m.group(3)

                if field == 'saldo':
                    parts_readable.append(f"Saldo: ${_fmt_money_any(old_val)} -> ${_fmt_money_any(new_val)}")
                elif field == 'estado':
                    parts_readable.append(f"Estado: {old_val} -> {new_val}")
                else:
                    parts_readable.append(f"{field}: {old_val} -> {new_val}")

            if not parts_readable:
                continue

            new_desc = f"Fiado {cliente}{user_part}: " + '; '.join(parts_readable)
            if act.descripcion != new_desc:
                cambios.append((act, new_desc))
                if limit and len(cambios) >= limit:
                    break

        if not cambios:
            self.stdout.write("No hay actividades de actualización de Fiado para normalizar.")
            return

        self.stdout.write(f"Encontradas {len(cambios)} actividades para normalizar.")
        show_n = min(20, len(cambios))
        for i in range(show_n):
            act, new_desc = cambios[i]
            self.stdout.write(f"- Actividad id={act.id}: '{act.descripcion}' -> '{new_desc}'")
        if len(cambios) > show_n:
            self.stdout.write(f"(y {len(cambios) - show_n} más...)")

        if not apply_changes:
            self.stdout.write("\nModo DRY-RUN (no se aplicó nada). Ejecuta con --apply para guardar.")
            return

        with transaction.atomic():
            to_update: List[Actividad] = []
            for act, new_desc in cambios:
                act.descripcion = new_desc
                to_update.append(act)
            Actividad.objects.bulk_update(to_update, ["descripcion"])

        self.stdout.write(f"\nOK: actualizadas {len(cambios)} actividades.")
