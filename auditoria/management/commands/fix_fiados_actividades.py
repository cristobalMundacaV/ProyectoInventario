from __future__ import annotations

import re
from typing import Dict, List, Tuple

from django.core.management.base import BaseCommand
from django.db import transaction

from auditoria.models import Actividad
from inventario.templatetags.format_numbers import format_money
from ventas.models import Fiado, FiadoAbono


class Command(BaseCommand):
	help = (
		"Normaliza descripciones antiguas en auditoría para Fiados/Abonos. "
		"Ej: 'Creado FiadoAbono id=5' -> 'Abono fiado <Cliente> $<Monto>'"
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
		parser.add_argument(
			"--include-fiado",
			action="store_true",
			help="También normaliza 'Creado Fiado id=X' -> 'Creado Fiado <Cliente> $<Total>'.",
		)

	def handle(self, *args, **options):
		apply_changes: bool = bool(options.get("apply"))
		limit: int = int(options.get("limit") or 0)
		include_fiado: bool = bool(options.get("include_fiado"))

		fiadoabono_re = re.compile(r"^Creado\s+FiadoAbono\s+id=(\d+)\s*$", re.IGNORECASE)
		fiado_re = re.compile(r"^Creado\s+Fiado\s+id=(\d+)\s*$", re.IGNORECASE)

		cambios: List[Tuple[Actividad, str]] = []

		# --- FiadoAbono ---
		abono_qs = Actividad.objects.filter(
			tipo_accion="CREACION_REGISTRO",
			descripcion__startswith="Creado FiadoAbono id=",
		).only("id", "descripcion")

		abono_matches: List[Tuple[Actividad, int]] = []
		abono_ids: List[int] = []
		for act in abono_qs:
			m = fiadoabono_re.match((act.descripcion or "").strip())
			if not m:
				continue
			pk = int(m.group(1))
			abono_matches.append((act, pk))
			abono_ids.append(pk)

		abonos_map: Dict[int, FiadoAbono] = {
			a.pk: a for a in FiadoAbono.objects.filter(pk__in=abono_ids).select_related("fiado")
		}

		for act, abono_pk in abono_matches:
			abono = abonos_map.get(abono_pk)
			if not abono:
				continue
			cliente = ""
			try:
				cliente = (abono.fiado.cliente_nombre or "").strip()
			except Exception:
				cliente = ""
			if not cliente:
				continue

			try:
				monto_fmt = format_money(abono.monto)
			except Exception:
				monto_fmt = str(abono.monto)

			new_desc = f"Abono fiado {cliente} ${monto_fmt}"
			if act.descripcion != new_desc:
				cambios.append((act, new_desc))
				if limit and len(cambios) >= limit:
					break

		# --- Fiado (opcional) ---
		if include_fiado and (not limit or len(cambios) < limit):
			fiado_qs = Actividad.objects.filter(
				tipo_accion="CREACION_REGISTRO",
				descripcion__startswith="Creado Fiado id=",
			).only("id", "descripcion")

			fiado_matches: List[Tuple[Actividad, int]] = []
			fiado_ids: List[int] = []
			for act in fiado_qs:
				m = fiado_re.match((act.descripcion or "").strip())
				if not m:
					continue
				pk = int(m.group(1))
				fiado_matches.append((act, pk))
				fiado_ids.append(pk)

			fiados_map: Dict[int, Fiado] = {
				f.pk: f
				for f in Fiado.objects.filter(pk__in=fiado_ids).only("id", "cliente_nombre", "total")
			}

			for act, fiado_pk in fiado_matches:
				fiado = fiados_map.get(fiado_pk)
				if not fiado:
					continue
				cliente = (fiado.cliente_nombre or "").strip()
				if not cliente:
					continue
				try:
					total_fmt = format_money(fiado.total)
				except Exception:
					total_fmt = str(fiado.total)

				new_desc = f"Creado Fiado {cliente} ${total_fmt}"
				if act.descripcion != new_desc:
					cambios.append((act, new_desc))
					if limit and len(cambios) >= limit:
						break

		if not cambios:
			self.stdout.write("No hay actividades para normalizar.")
			return

		# Preview
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

		# Apply
		with transaction.atomic():
			to_update: List[Actividad] = []
			for act, new_desc in cambios:
				act.descripcion = new_desc
				to_update.append(act)
			Actividad.objects.bulk_update(to_update, ["descripcion"])

		self.stdout.write(f"\nOK: actualizadas {len(cambios)} actividades.")

