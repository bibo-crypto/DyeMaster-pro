"""
مصدر PDF للريتشتات
"""
import os
from datetime import datetime
from tkinter import filedialog

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from app.models import RecipeDetails


class PDFExporter:


    """مصدر PDF للريتشتات"""





    @staticmethod


    def export_recipe_to_pdf(recipe_details: RecipeDetails, output_path=None, parent_window=None):


        """تصدير الوصفة إلى PDF"""


        try:


            # إنشاء اسم الملف


            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


            recipe_name = recipe_details.recipe.name.replace(" ", "_")


            recipe_code = recipe_details.recipe.recipe_code or "NoCode"





            if not output_path:


                # الحصول على مسار المستندات


                folder = filedialog.askdirectory(title="Select folder to save PDF", parent=parent_window)


                if not folder:


                    return None





                output_path = os.path.join(folder, f"Recipe_{recipe_code}_{recipe_name}_{timestamp}.pdf")


            else:


                # تأكد من وجود المجلد


                folder = os.path.dirname(output_path)


                if folder and not os.path.exists(folder):


                    os.makedirs(folder)





            # إنشاء المستند


            doc = SimpleDocTemplate(


                output_path,


                pagesize=A4,


                rightMargin=72,


                leftMargin=72,


                topMargin=72,


                bottomMargin=72


            )





            elements = []





            # الأنماط


            styles = getSampleStyleSheet()





            # عنوان رئيسي


            title_style = ParagraphStyle(


                'CustomTitle',


                parent=styles['Heading1'],


                fontSize=18,


                alignment=TA_CENTER,


                textColor=colors.HexColor('#2C3E50'),


                spaceAfter=30,


                fontName='Helvetica-Bold'


            )





            # عنوان فرعي


            subtitle_style = ParagraphStyle(


                'CustomSubtitle',


                parent=styles['Heading2'],


                fontSize=14,


                alignment=TA_LEFT,


                textColor=colors.HexColor('#34495E'),


                spaceAfter=15,


                fontName='Helvetica-Bold'


            )





            # نص عادي


            normal_style = ParagraphStyle(


                'NormalStyle',


                parent=styles['Normal'],


                fontSize=10,


                alignment=TA_LEFT,


                spaceAfter=6


            )





            # ========== العنوان الرئيسي ==========
            elements.append(Paragraph(f"Recipe: {recipe_details.recipe.name} ({recipe_details.recipe.recipe_code})", title_style))
            elements.append(Spacer(1, 20))

            # ========== معلومات إضافية ==========
            info_data = [
                [Paragraph('<b>Cost Recipe:</b>', normal_style), Paragraph(f"€{recipe_details.cost:.2f} / kg", normal_style)],
                [Paragraph('<b>Dye Type:</b>', normal_style), Paragraph(recipe_details.dominant_type, normal_style)],
                [Paragraph('<b>Printed At:</b>', normal_style), Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), normal_style)]
            ]

            info_table = Table(info_data, colWidths=[4 * cm, 11 * cm])
            info_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
                ('PADDING', (0, 0), (-1, -1), 6)
            ]))

            elements.append(info_table)
            elements.append(Spacer(1, 30))

            # ========== الألوان المستخدمة ==========
            elements.append(Paragraph("1. COLORS DETAILS", subtitle_style))





            if recipe_details.colors:


                colors_data = [["No.", "Color Code", "Color Name", "Percentage %", "Lab (ml/l)"]]





                total_lab_ml_l = 0


                for i, color in enumerate(recipe_details.colors, 1):


                    # التعامل مع كائنات RecipeColor أو القواميس
                    if isinstance(color, dict):
                        percentage = color.get('percentage', 0)
                        code = color.get("code", "")
                        name = color.get("name", "")
                    else:
                        # كائن RecipeColor
                        percentage = getattr(color, 'percentage', 0)
                        code = getattr(color, 'code', '') or getattr(color, 'color_code', '')
                        name = getattr(color, 'name', '') or getattr(color, 'color_name', '')
                    
                    lab_ml_l = percentage * 15


                    total_lab_ml_l += lab_ml_l





                    colors_data.append([


                        str(i),


                        code,


                        name,


                        f"{percentage:.4f}",


                        f"{lab_ml_l:.2f}",


                    ])





                # إضافة صف المجموع


                colors_data.append([


                    "", "", "TOTAL:",


                    f"{recipe_details.total_percentage:.4f}%",


                    f"{total_lab_ml_l:.2f}",


                ])





                colors_table = Table(colors_data, colWidths=[1*cm, 3*cm, 5.5*cm, 3*cm, 3*cm])


                colors_table.setStyle(TableStyle([


                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86C1')),


                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),


                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),


                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),


                    ('FONTSIZE', (0, 0), (-1, -1), 9),


                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),


                    ('TOPPADDING', (0, 0), (-1, -1), 6),


                    ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#D5D8DC')),


                    ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#F2F3F4')),


                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#AED6F1')),


                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),


                    ('GRID', (0, -1), (-1, -1), 0.5, colors.HexColor('#2E86C1'))


                ]))





                elements.append(colors_table)


            else:


                elements.append(Paragraph("No colors in this recipe.", normal_style))





            elements.append(Spacer(1, 30))





            # ========== الكيماويات المطلوبة ==========


            elements.append(Paragraph("2. CHEMICALS REQUIRED", subtitle_style))





            if recipe_details.chemicals:


                chemicals_data = [["No.", "Code", "Chemical Name", "Quantity", "Unit", "Lab Prep. (ml/l)"]]

                for i, chemical in enumerate(recipe_details.chemicals, 1):
                    lab_prep = ""

                    # Handle both dict and Chemical objects
                    if isinstance(chemical, dict):
                        unit = chemical.get('unit', '') or ''
                        quantity = chemical.get('quantity', 0) or 0
                        code = chemical.get('code', '') or ''
                        name = chemical.get('name', '') or ''
                    else:
                        # Chemical object
                        unit = getattr(chemical, 'unit', '') or ''
                        quantity = getattr(chemical, 'quantity', 0) or 0
                        code = getattr(chemical, 'code', '') or ''
                        name = getattr(chemical, 'name', '') or ''

                    # Calculate lab_prep based on unit
                    try:
                        if unit == 'ml/l':
                            lab_prep = f"{float(quantity) * 10:.2f}"
                        elif unit == 'g/l':
                            lab_prep = f"{float(quantity):.2f}"
                        else:
                            lab_prep = f"{float(quantity):.2f}"
                    except (ValueError, TypeError):
                        lab_prep = "0.00"

                    chemicals_data.append([
                        str(i),
                        str(code),
                        str(name),
                        str(quantity),
                        str(unit),
                        lab_prep
                    ])





                chemicals_table = Table(chemicals_data, colWidths=[1*cm, 2*cm, 5.5*cm, 2*cm, 1.5*cm, 3*cm])


                chemicals_table.setStyle(TableStyle([


                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),


                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),


                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),


                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),


                    ('FONTSIZE', (0, 0), (-1, -1), 10),


                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),


                    ('TOPPADDING', (0, 0), (-1, -1), 8),


                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ABEBC6')),


                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#EAFAF1'))


                ]))





                elements.append(chemicals_table)


            else:


                elements.append(Paragraph("No chemicals calculated for this recipe.", normal_style))





            elements.append(Spacer(1, 20))





            # ملاحظات الكيماويات


            notes_text = """


            <b>Notes:</b><br/>


            • Quantities are per liter of dye bath.<br/>


            • Lab Prep. column shows the amount of stock solution (1:10 dilution) to use.<br/>


            • Color Lab (ml/l) is calculated for a 1:100 stock solution.<br/>


            • Adjust based on fabric weight and liquor ratio.<br/>


            • Always conduct lab tests before full production.<br/>


            • Store chemicals in cool, dry places.


            """


            notes_para = Paragraph(notes_text, normal_style)


            elements.append(notes_para)





            # بناء المستند


            doc.build(elements)





            # التحقق من إنشاء الملف


            if os.path.exists(output_path):


                file_size = os.path.getsize(output_path) / 1024  # حجم الملف بالكيلوبايت


                print(f"PDF created successfully: {output_path} ({file_size:.1f} KB)")


                return output_path


            else:


                print("PDF creation failed")


                return None





        except Exception as e:


            print(f"Error creating PDF: {e}")





            import traceback


            traceback.print_exc()


            return None





    @staticmethod


    def export_recipe_to_pdf_auto(recipe_details: RecipeDetails):


        """تصدير الوصفة إلى PDF مع مسار تلقائي (بدون سؤال المستخدم)"""


        try:


            # إنشاء مجلد Exports إذا لم يكن موجوداً


            desktop = os.path.join(os.path.expanduser("~"), "Desktop")


            export_folder = os.path.join(desktop, "ColorChem_Exports")





            if not os.path.exists(export_folder):


                os.makedirs(export_folder)





            # إنشاء اسم الملف


            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


            recipe_name_clean = recipe_details.recipe.name.replace(" ", "_").replace("/", "_")


            recipe_code_clean = recipe_details.recipe.recipe_code or "NoCode"





            pdf_filename = f"Recipe_{recipe_code_clean}_{recipe_name_clean}_{timestamp}.pdf"


            pdf_path = os.path.join(export_folder, pdf_filename)





            # استخدام الدالة الأصلية مع المسار المحدد


            return PDFExporter.export_recipe_to_pdf(recipe_details, pdf_path)





        except Exception as e:


            print(f"Error in auto export: {e}")


            return None





    @staticmethod


    def export_multiple_recipes(recipes_details_list, output_folder=None):


        """تصدير عدة ريتشتات في ملف PDF واحد"""


        try:


            if not recipes_details_list:


                return None





            if not output_folder:


                from tkinter import filedialog


                output_folder = filedialog.askdirectory(title="Select folder to save PDF")


                if not output_folder:


                    return None





            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


            output_path = os.path.join(output_folder, f"Multiple_Recipes_{timestamp}.pdf")





            doc = SimpleDocTemplate(output_path, pagesize=A4)


            elements = []





            styles = getSampleStyleSheet()


            title_style = ParagraphStyle(


                'MultiTitle',


                parent=styles['Heading1'],


                fontSize=16,


                alignment=TA_CENTER,


                spaceAfter=30


            )





            elements.append(Paragraph("MULTIPLE RECIPES REPORT", title_style))





            for idx, recipe_details in enumerate(recipes_details_list, 1):


                # عنوان كل وصفة


                recipe_title = f"{idx}. {recipe_details.recipe.name} ({recipe_details.recipe.recipe_code})"


                elements.append(Paragraph(recipe_title, styles['Heading2']))





                # معلومات مختصرة


                summary_data = [


                    ["Total Colors:", str(len(recipe_details.colors))],


                    ["Total Percentage:", f"{recipe_details.total_percentage:.2f}%"],


                    ["Dominant Type:", recipe_details.dominant_type],


                    ["Cost per kg:", f"€{recipe_details.cost:.2f}"]


                ]





                summary_table = Table(summary_data, colWidths=[3 * cm, 4 * cm])


                summary_table.setStyle(TableStyle([


                    ('FONTSIZE', (0, 0), (-1, -1), 9),


                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),


                    ('PADDING', (0, 0), (-1, -1), 5)


                ]))





                elements.append(summary_table)


                elements.append(Spacer(1, 20))





            doc.build(elements)


            return output_path





        except Exception as e:


            print(f"Error creating multi-recipe PDF: {e}")


            return None

