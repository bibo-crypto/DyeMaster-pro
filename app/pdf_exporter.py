"""PDF export utilities."""
import os
from datetime import datetime
from tkinter import filedialog

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
    def _chemical_row(chemical):
        code = getattr(chemical, "code", "")
        name = getattr(chemical, "name", "")
        qty = PDFExporter._to_float(getattr(chemical, "quantity", 0.0))
        unit = getattr(chemical, "unit", "")
        return [str(code), str(name), f"{qty:.2f}", str(unit)]

    @staticmethod
    def _build_single_recipe_elements(recipe_details: RecipeDetails, styles):
        elements = []

        recipe_name = getattr(recipe_details.recipe, "name", "") or "Unnamed"
        recipe_code = getattr(recipe_details.recipe, "recipe_code", "") or "NoCode"
        created_at = getattr(recipe_details.recipe, "created_at", "") or ""

        elements.append(Paragraph("Recipe Report", styles["Title"]))
        elements.append(Spacer(1, 12))

        info_data = [
            ["Recipe Code", str(recipe_code)],
            ["Recipe Name", str(recipe_name)],
            ["Created At", str(created_at)],
            ["Total Percentage", f"{PDFExporter._to_float(getattr(recipe_details, 'total_percentage', 0.0)):.2f}%"],
            ["Dominant Type", str(getattr(recipe_details, "dominant_type", ""))],
            ["Estimated Cost", f"EUR {PDFExporter._to_float(getattr(recipe_details, 'cost', 0.0)):.2f}"],
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

        colors_rows = [["Code", "Name", "Type", "Percentage", "Supplier", "Price/KG"]]
        for color in getattr(recipe_details, "colors", []) or []:
            color_code = PDFExporter._color_value(color, "code")
            color_name = PDFExporter._color_value(color, "name")
            dye_type = PDFExporter._color_value(color, "dye_type")
            percentage = PDFExporter._to_float(PDFExporter._color_value(color, "percentage", 0.0))
            supplier = PDFExporter._color_value(color, "supplier")
            price = PDFExporter._to_float(PDFExporter._color_value(color, "price_kg", 0.0))
            colors_rows.append([
                str(color_code),
                str(color_name),
                str(dye_type),
                f"{percentage:.2f}%",
                str(supplier),
                f"EUR {price:.2f}",
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

        chemicals_rows = [["Code", "Name", "Quantity", "Unit"]]
        for chemical in getattr(recipe_details, "chemicals", []) or []:
            chemicals_rows.append(PDFExporter._chemical_row(chemical))

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
            export_folder = os.path.join(desktop, "ColorChem_Exports")
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
