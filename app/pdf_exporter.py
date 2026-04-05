"""PDF export utilities."""
import os
from datetime import datetime
from tkinter import filedialog
from app.lab_settings import load_lab_settings

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak
    REPORTLAB_AVAILABLE = True
    REPORTLAB_IMPORT_ERROR = None
except ImportError as exc:
    REPORTLAB_AVAILABLE = False
    REPORTLAB_IMPORT_ERROR = exc

from app.models import RecipeDetails


class PDFExporter:
    """Exports recipe data to PDF files."""
    DEFAULT_LAB_VOLUME_ML = 150.0
    DEFAULT_LAB_SAMPLE_G = 10.0

    @staticmethod
    def _ensure_reportlab(parent_window=None) -> bool:
        if REPORTLAB_AVAILABLE:
            return True
        msg = (
            "PDF export requires the 'reportlab' package, which is not installed in this Python environment.\n\n"
            f"Details: {REPORTLAB_IMPORT_ERROR}"
        )
        print(msg)
        try:
            from tkinter import messagebox
            messagebox.showerror("Missing Dependency", msg, parent=parent_window)
        except Exception:
            pass
        return False

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        return "".join(ch if ch.isalnum() or ch in ("-", "_", " ") else "_" for ch in name).strip().replace(" ", "_")

    @staticmethod
    def _to_float(value, default=0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _color_value(color, key, fallback=""):
        if isinstance(color, dict):
            return color.get(key, fallback)
        return getattr(color, key, fallback)

    @staticmethod
    def _lab_adjusted_percentage(color) -> float:
        base_percentage = max(0.0, PDFExporter._to_float(PDFExporter._color_value(color, "percentage", 0.0), 0.0))
        resa_percent = PDFExporter._to_float(PDFExporter._color_value(color, "resa_percent", 100.0), 100.0)
        if resa_percent <= 0:
            resa_percent = 100.0
        return base_percentage * (resa_percent / 100.0)

    @staticmethod
    def _chemical_row(chemical, lab_volume_ml):
        code = getattr(chemical, "code", "")
        name = getattr(chemical, "name", "")
        qty = PDFExporter._to_float(getattr(chemical, "quantity", 0.0))
        unit = getattr(chemical, "unit", "")

        # Lab conversion rules:
        # - Convert per-liter values to the configured lab bath volume.
        # - Applies to both ml/l and g/l
        unit_lower = str(unit).strip().lower()
        factor = lab_volume_ml / 1000.0
        if "ml/l" in unit_lower:
            lab_qty = qty * factor
        elif "g/l" in unit_lower:
            lab_qty = qty * factor
        else:
            lab_qty = qty * factor

        lab_unit = PDFExporter._normalize_lab_unit(unit)
        prod_text = f"{PDFExporter._format_number_for_pdf(qty)} {unit}".strip()
        lab_text = f"{PDFExporter._format_lab_for_pdf(lab_qty)} {lab_unit}".strip()
        return [str(code), str(name), prod_text, lab_text]

    @staticmethod
    def _format_number_for_pdf(value, decimals=1) -> str:
        try:
            n = float(value)
        except (TypeError, ValueError):
            return str(value)
        rounded = round(n, decimals)
        if abs(rounded - int(rounded)) < 1e-9:
            return str(int(rounded))
        return f"{rounded:.{decimals}f}"

    @staticmethod
    def _format_percentage_for_pdf(value) -> str:
        """Keep decimals as needed, avoid rounding tiny percentages to zero."""
        try:
            n = float(value)
        except (TypeError, ValueError):
            return str(value)
        rounded = round(n, 4)
        if abs(rounded - int(rounded)) < 1e-9:
            return str(int(rounded))
        s = f"{rounded:.4f}".rstrip("0").rstrip(".")
        return s

    @staticmethod
    def _format_lab_for_pdf(value) -> str:
        """For lab quantities: integer if whole, else up to 2 decimals."""
        try:
            n = float(value)
        except (TypeError, ValueError):
            return str(value)
        rounded = round(n, 2)
        if abs(rounded - int(rounded)) < 1e-9:
            return str(int(rounded))
        s = f"{rounded:.2f}".rstrip("0").rstrip(".")
        return s

    @staticmethod
    def _normalize_lab_unit(unit: str) -> str:
        if not unit:
            return ""
        unit_str = str(unit).strip()
        if "/" in unit_str:
            return unit_str.split("/", 1)[0].strip()
        return unit_str

    @staticmethod
    def _is_liquid_unit(unit: str) -> bool:
        base = PDFExporter._normalize_lab_unit(unit).strip().lower()
        return ("ml" in base) or ("cc" in base) or (base in {"l", "lt", "ltr", "liter", "litre"})

    @staticmethod
    def _to_ml(quantity: float, unit: str) -> float:
        base = PDFExporter._normalize_lab_unit(unit).strip().lower()
        qty = max(0.0, PDFExporter._to_float(quantity, 0.0))
        if "ml" in base or "cc" in base:
            return qty
        if base in {"l", "lt", "ltr", "liter", "litre"}:
            return qty * 1000.0
        return 0.0

    @staticmethod
    def _compute_water_required_ml(recipe_details: RecipeDetails, lab_sample_g: float, lab_volume_ml: float) -> int:
        # Colors are treated as liquids in lab basis.
        colors_liquid_ml = 0.0
        for color in getattr(recipe_details, "colors", []) or []:
            adjusted_percentage = PDFExporter._lab_adjusted_percentage(color)
            colors_liquid_ml += adjusted_percentage * lab_sample_g

        # Chemicals are defined per liter in most formulas; convert to lab-bath basis first.
        chemicals_liquid_ml = 0.0
        factor = lab_volume_ml / 1000.0
        for chemical in getattr(recipe_details, "chemicals", []) or []:
            qty = PDFExporter._to_float(getattr(chemical, "quantity", 0.0), 0.0)
            unit = str(getattr(chemical, "unit", "") or "").strip()
            if not unit or not PDFExporter._is_liquid_unit(unit):
                continue
            qty_lab = qty * factor if "/" in unit else qty
            chemicals_liquid_ml += PDFExporter._to_ml(qty_lab, unit)

        used_liquids_ml = colors_liquid_ml + chemicals_liquid_ml
        water_required_ml = max(0.0, lab_volume_ml - used_liquids_ml)
        return int(round(water_required_ml))

    @staticmethod
    def _resolve_total_percentage(recipe_details: RecipeDetails) -> float:
        total = PDFExporter._to_float(getattr(recipe_details, "total_percentage", 0.0), 0.0)
        if total > 0:
            return total

        colors = getattr(recipe_details, "colors", []) or []
        calculated_total = 0.0
        for color in colors:
            calculated_total += PDFExporter._to_float(PDFExporter._color_value(color, "percentage", 0.0), 0.0)
        return calculated_total

    @staticmethod
    def _resolve_lab_params(recipe_details: RecipeDetails):
        stored_defaults = load_lab_settings()
        defaults = {
            "sample_g": PDFExporter._to_float(stored_defaults.get("sample_g"), PDFExporter.DEFAULT_LAB_SAMPLE_G),
            "volume_ml": PDFExporter._to_float(stored_defaults.get("volume_ml"), PDFExporter.DEFAULT_LAB_VOLUME_ML),
        }
        incoming = getattr(recipe_details, "lab_params", None)
        if not isinstance(incoming, dict):
            return defaults

        sample_g = PDFExporter._to_float(incoming.get("sample_g", defaults["sample_g"]), defaults["sample_g"])
        volume_ml = PDFExporter._to_float(incoming.get("volume_ml", defaults["volume_ml"]), defaults["volume_ml"])
        if sample_g <= 0:
            sample_g = defaults["sample_g"]
        if volume_ml <= 0:
            volume_ml = defaults["volume_ml"]
        return {"sample_g": sample_g, "volume_ml": volume_ml}

    @staticmethod
    def _format_rapporto(sample_g: float, volume_ml: float) -> str:
        ratio = volume_ml / sample_g if sample_g else 0.0
        rounded = round(ratio)
        if abs(ratio - rounded) < 1e-9:
            return f"(1:{int(rounded)})"
        return f"(1:{ratio:.2f})"

    @staticmethod
    def _build_single_recipe_elements(recipe_details: RecipeDetails, styles):
        elements = []

        recipe_name = getattr(recipe_details.recipe, "name", "") or "Unnamed"
        recipe_code = getattr(recipe_details.recipe, "recipe_code", "") or "NoCode"
        created_at = getattr(recipe_details.recipe, "created_at", "") or ""

        elements.append(Paragraph("Recipe Report", styles["Title"]))
        elements.append(Spacer(1, 12))

        total_percentage = PDFExporter._resolve_total_percentage(recipe_details)
        lab_params = PDFExporter._resolve_lab_params(recipe_details)
        lab_sample_g = lab_params["sample_g"]
        lab_volume_ml = lab_params["volume_ml"]
        rapporto_bagno = PDFExporter._format_rapporto(lab_sample_g, lab_volume_ml)

        info_data = [
            ["Recipe Code", str(recipe_code)],
            ["Recipe Name", str(recipe_name)],
            ["Created At", str(created_at)],
            ["Peso", f"{PDFExporter._format_number_for_pdf(lab_sample_g)} g"],
            ["Volume", f"{PDFExporter._format_number_for_pdf(lab_volume_ml)} ml"],
            ["Rapporto Bagno", rapporto_bagno],
            ["Total Percentage", f"{PDFExporter._format_percentage_for_pdf(total_percentage)}%"],
            ["Dominant Type", str(getattr(recipe_details, "dominant_type", ""))],
            ["Estimated Cost", f"€{PDFExporter._format_number_for_pdf(PDFExporter._to_float(getattr(recipe_details, 'cost', 0.0)), decimals=1)}"],
        ]
        info_table = Table(info_data, colWidths=[140, 340])
        info_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 16))

        colors_rows = [["Code", "Name", "Production Qty", "Resa", "Lab Qty"]]
        for color in getattr(recipe_details, "colors", []) or []:
            color_code = PDFExporter._color_value(color, "code")
            color_name = PDFExporter._color_value(color, "name")
            percentage = PDFExporter._to_float(PDFExporter._color_value(color, "percentage", 0.0))
            resa_percent = PDFExporter._to_float(PDFExporter._color_value(color, "resa_percent", 100.0), 100.0)
            if resa_percent <= 0:
                resa_percent = 100.0
            adjusted_percentage = PDFExporter._lab_adjusted_percentage(color)
            # Lab color quantity scales with sample weight.
            # For 10 g sample: 0.8 -> 8 ml
            lab_color_qty = adjusted_percentage * lab_sample_g
            colors_rows.append([
                str(color_code),
                str(color_name),
                f"{PDFExporter._format_percentage_for_pdf(percentage)} %/kg",
                f"{PDFExporter._format_percentage_for_pdf(resa_percent)}%",
                f"{PDFExporter._format_lab_for_pdf(lab_color_qty)} ml",
            ])

        elements.append(Paragraph("Colors", styles["Heading2"]))
        colors_table = Table(colors_rows, repeatRows=1)
        colors_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(colors_table)
        elements.append(Spacer(1, 16))

        chemicals_rows = [["Code", "Name", "Production Qty", "Lab Qty"]]
        for chemical in getattr(recipe_details, "chemicals", []) or []:
            chemicals_rows.append(PDFExporter._chemical_row(chemical, lab_volume_ml))

        elements.append(Paragraph("Chemicals", styles["Heading2"]))
        chemicals_table = Table(chemicals_rows, repeatRows=1)
        chemicals_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(chemicals_table)
        elements.append(Spacer(1, 12))
        water_required_ml = PDFExporter._compute_water_required_ml(recipe_details, lab_sample_g, lab_volume_ml)
        elements.append(Paragraph(f"Water Required: {water_required_ml} ml", styles["Heading3"]))
        elements.append(Spacer(1, 6))
        per_liter_factor = lab_volume_ml / 1000.0
        elements.append(Paragraph(
            f"Lab basis: {PDFExporter._format_number_for_pdf(lab_sample_g)} g yarn, {PDFExporter._format_number_for_pdf(lab_volume_ml)} ml bath.",
            styles["Normal"]
        ))
        elements.append(Paragraph(
            f"Color lab: (%/kg x RESA/100) x {PDFExporter._format_number_for_pdf(lab_sample_g)} = ml.",
            styles["Normal"]
        ))
        elements.append(Paragraph(
            f"Chemicals lab: (value per liter) x {PDFExporter._format_number_for_pdf(per_liter_factor, decimals=4)}.",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 8))

        generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(f"Generated at: {generated}", styles["Normal"]))

        return elements

    @staticmethod
    def export_recipe_to_pdf(recipe_details: RecipeDetails, output_path=None, parent_window=None):
        if not PDFExporter._ensure_reportlab(parent_window=parent_window):
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            recipe_name = PDFExporter._sanitize_filename(getattr(recipe_details.recipe, "name", "Recipe") or "Recipe")
            recipe_code = PDFExporter._sanitize_filename(getattr(recipe_details.recipe, "recipe_code", "NoCode") or "NoCode")

            if not output_path:
                folder = filedialog.askdirectory(title="Select folder to save PDF", parent=parent_window)
                if not folder:
                    return None
                output_path = os.path.join(folder, f"Recipe_{recipe_code}_{recipe_name}_{timestamp}.pdf")
            else:
                folder = os.path.dirname(output_path)
                if folder and not os.path.exists(folder):
                    os.makedirs(folder, exist_ok=True)

            doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            styles = getSampleStyleSheet()
            elements = PDFExporter._build_single_recipe_elements(recipe_details, styles)
            doc.build(elements)
            return output_path if os.path.exists(output_path) else None
        except Exception as exc:
            print(f"Error creating PDF: {exc}")
            return None

    @staticmethod
    def export_recipe_to_pdf_auto(recipe_details: RecipeDetails):
        if not PDFExporter._ensure_reportlab():
            return None

        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            export_folder = os.path.join(desktop, "DyeMasterPro_Exports")
            os.makedirs(export_folder, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            recipe_name = PDFExporter._sanitize_filename(getattr(recipe_details.recipe, "name", "Recipe") or "Recipe")
            recipe_code = PDFExporter._sanitize_filename(getattr(recipe_details.recipe, "recipe_code", "NoCode") or "NoCode")
            pdf_path = os.path.join(export_folder, f"Recipe_{recipe_code}_{recipe_name}_{timestamp}.pdf")
            return PDFExporter.export_recipe_to_pdf(recipe_details, pdf_path)
        except Exception as exc:
            print(f"Error in auto export: {exc}")
            return None

    @staticmethod
    def export_multiple_recipes(recipes_details_list, output_folder=None):
        if not PDFExporter._ensure_reportlab():
            return None

        try:
            if not recipes_details_list:
                return None

            if not output_folder:
                output_folder = filedialog.askdirectory(title="Select folder to save PDF")
                if not output_folder:
                    return None

            os.makedirs(output_folder, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_folder, f"Multiple_Recipes_{timestamp}.pdf")

            doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            styles = getSampleStyleSheet()
            elements = []

            for idx, recipe_details in enumerate(recipes_details_list):
                elements.extend(PDFExporter._build_single_recipe_elements(recipe_details, styles))
                if idx < len(recipes_details_list) - 1:
                    elements.append(PageBreak())

            doc.build(elements)
            return output_path if os.path.exists(output_path) else None
        except Exception as exc:
            print(f"Error exporting multiple recipes: {exc}")
            return None
