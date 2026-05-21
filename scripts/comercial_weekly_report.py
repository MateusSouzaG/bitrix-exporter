# -*- coding: utf-8 -*-
"""
CLI: gera relatório semanal comercial (formulário + agenda #).
Uso: python scripts/comercial_weekly_report.py [--output arquivo.xlsx] [--current-week]

Validação de segunda-feira: comparar Excel gerado com planilha manual da coordenadora.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from comercial_report import build_weekly_excel_bytes  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Relatório semanal COMERCIAL")
    parser.add_argument(
        "--output",
        "-o",
        default="",
        help="Caminho do Excel de saída (padrão: Relatorio_Comercial_YYYYMMDD_HHMMSS.xlsx)",
    )
    parser.add_argument(
        "--current-week",
        action="store_true",
        help="Usar semana corrente em vez da semana anterior",
    )
    args = parser.parse_args()

    previous_week = not args.current_week
    excel_bytes, num_rows, week_start, week_end = build_weekly_excel_bytes(
        previous_week=previous_week
    )

    if args.output:
        out_path = Path(args.output)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = _ROOT / f"Relatorio_Comercial_{week_start.strftime('%Y%m%d')}_{ts}.xlsx"

    out_path.write_bytes(excel_bytes.getvalue())
    print(f"Semana: {week_start.date()} a {week_end.date()}")
    print(f"Colaboradores COMERCIAL: {num_rows}")
    print(f"Arquivo: {out_path}")
    print("Abas: Consolidado Semanal | Resumos Diários | Agenda Hash | Convenções")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
