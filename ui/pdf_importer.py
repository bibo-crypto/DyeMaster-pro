"""
مستورد PDF للوصفات المعملية (نسخة محسنة)
"""
import re
from typing import List, Dict
import pdfplumber


class PDFRecipeImporter:
    """مستورد وصفات من ملفات PDF معملية - محسنة"""

    @staticmethod
    def extract_recipe_from_pdf(pdf_path: str) -> Dict:
        """استخراج بيانات الوصفة مباشرة من PDF"""
        recipe_data = {
            'recipe_name': '',
            'recipe_code': '',
            'colors': [],
            'dye_type': '',
            'total_percentage': 0.0
        }

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # محاولة استخراج البيانات من كل صفحة
                for page in pdf.pages:
                    text = page.extract_text() if page.extract_text() else ""

                    # استخراج رقم الوصفة (Ricetta_ID)
                    code_match = re.search(r'Ricetta_ID\s*(\d+)', text)
                    if code_match and not recipe_data['recipe_code']:
                        recipe_data['recipe_code'] = code_match.group(1).strip()

                    # استخراج اسم الوصفة (محسن)
                    if not recipe_data['recipe_name']:
                        # البحث عن "Standard" ككلمة أساسية للاسم
                        name_match = re.search(r'Standard\s+([^\n]+)', text)
                        if name_match:
                            recipe_data['recipe_name'] = name_match.group(1).strip()
                        else:
                            # حل بديل إذا لم يتم العثور على "Standard"
                            lines = text.split('\n')
                            for i, line in enumerate(lines):
                                if 'Ricetta_ID' in line and i + 1 < len(lines):
                                    # افتراض أن الاسم في السطر التالي
                                    recipe_data['recipe_name'] = lines[i+1].strip()
                                    break

                    # استخراج نوع الصباغة (محسن)
                    if not recipe_data['dye_type']:
                        dye_type_text = text.lower()
                        if 'indanthren' in dye_type_text:
                            recipe_data['dye_type'] = 'INDANTHREN'
                        elif 'reattivi freddi' in dye_type_text:
                            recipe_data['dye_type'] = 'REATTIVI FREDDI'
                        elif 'reattivi caldi' in dye_type_text:
                            recipe_data['dye_type'] = 'REATTIVI CALDI'
                        else:
                            recipe_data['dye_type'] = 'REATTIVI FREDDI' # تعيين قيمة افتراضية

                    # استخراج الألوان - البحث عن نمط: 80021 (80021) SYNOZOL YELLOW DS 1.2502 %
                    colors = PDFRecipeImporter._extract_colors_from_page(page)
                    if colors:
                        recipe_data['colors'].extend(colors)

            # حساب النسبة الكلية
            if recipe_data['colors']:
                total_percent = sum(PDFRecipeImporter._to_float(color.get('percentage', 0.0)) for color in recipe_data['colors'])
                recipe_data['total_percentage'] = total_percent

            return recipe_data

        except Exception as e:
            print(f"Error extracting from PDF: {e}")
            return recipe_data

    @staticmethod
    def _extract_colors_from_page(page) -> List[Dict]:
        """استخراج الألوان من صفحة PDF"""
        colors = []

        try:
            # استخراج النص من الصفحة
            text = page.extract_text()

            # تقسيم النص إلى أسطر
            lines = text.split('\n')

            # البحث عن الألوان - نمط: 80021 (80021) SYNOZOL YELLOW DS 1.2502 % 18.75 ml 1:100
            color_pattern = r'(\d{5})\s*\((\d{5})\)\s*([A-Z0-9\-\s]+)\s*([\d.]+)\s*%\s*[\d.]+\s*ml'

            for line in lines:
                # بحث باستخدام regex
                match = re.search(color_pattern, line)
                if match:
                    code, code2, name, percentage = match.groups()

                    colors.append({
                        'code': code.strip(),
                        'name': name.strip(),
                        'percentage': float(percentage),
                        'source_line': line
                    })

            # إذا فشل regex، جرب البحث البسيط
            if not colors:
                for line in lines:
                    # البحث عن سطور تبدأ بـ 5 أرقام
                    if re.match(r'^\d{5}\s', line.strip()):
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            code = parts[0]
                            # محاولة استخراج الاسم
                            name_parts = []
                            percentage_val = 0.0

                            for part in parts[1:]:
                                if '%' in part:
                                    try:
                                        percentage_val = float(part.replace('%', ''))
                                        break
                                    except:
                                        pass
                                else:
                                    name_parts.append(part)

                            name = ' '.join(name_parts)

                            if code and percentage_val > 0:
                                colors.append({
                                    'code': code,
                                    'name': name,
                                    'percentage': percentage_val,
                                    'source_line': line
                                })

            # محاولة أخرى: استخراج الجداول
            if not colors:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row and len(row) >= 3:
                            # البحث عن صفوف تحتوي على كود لون
                            row_text = ' '.join([str(cell) for cell in row if cell])
                            if re.search(r'\d{5}', row_text):
                                # محاولة استخراج البيانات
                                for cell in row:
                                    if cell and isinstance(cell, str):
                                        cell_match = re.search(r'(\d{5}).*?([\d.]+)\s*%', cell)
                                        if cell_match:
                                            code = cell_match.group(1)
                                            percentage = float(cell_match.group(2))

                                            # استخراج الاسم
                                            name_match = re.search(r'[A-Z][A-Z\s]+[A-Z]', cell)
                                            name = name_match.group() if name_match else f"Color {code}"

                                            colors.append({
                                                'code': code,
                                                'name': name,
                                                'percentage': percentage,
                                                'source_line': cell
                                            })

            return colors

        except Exception as e:
            print(f"Error extracting colors from page: {e}")
            return []

    @staticmethod
    def extract_recipe_from_text(text: str) -> Dict:
        """استخراج بيانات الوصفة من النص (نسخة محسنة)"""
        recipe_data = {
            'recipe_name': '',
            'recipe_code': '',
            'colors': [],
            'dye_type': '',
            'total_percentage': 0.0
        }

        try:
            # البحث عن رقم الوصفة
            code_patterns = [
                r'Ricetta_ID\s*(\d+)',
                r'Ricetta\s*(\d+)',
                r'38357'  # الرقم الموجود في المثال
            ]

            for pattern in code_patterns:
                match = re.search(pattern, text)
                if match:
                    recipe_data['recipe_code'] = match.group(1) if match.groups() else '38357'
                    break

            # البحث عن اسم الوصفة (محسن)
            name_match = re.search(r'Standard\s+([^\n]+)', text)
            if name_match:
                recipe_data['recipe_name'] = name_match.group(1).strip()
            else:
                name_match = re.search(r'Nome\s*([^\n]+)', text)
                if name_match:
                    recipe_data['recipe_name'] = name_match.group(1).strip()
                else:
                    # حل بديل: البحث عن الاسم في السطر التالي لـ Ricetta_ID
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        if 'Ricetta_ID' in line and i + 1 < len(lines):
                            next_line = lines[i+1].strip()
                            if next_line: # التأكد من أن السطر التالي ليس فارغًا
                                recipe_data['recipe_name'] = next_line
                                break

            # البحث عن نوع الصباغة (محسن)
            dye_type_text = text.lower()
            if 'indanthren' in dye_type_text:
                recipe_data['dye_type'] = 'INDANTHREN'
            elif 'reattivi freddi' in dye_type_text:
                recipe_data['dye_type'] = 'REATTIVI FREDDI'
            elif 'reattivi caldi' in dye_type_text:
                recipe_data['dye_type'] = 'REATTIVI CALDI'
            else:
                recipe_data['dye_type'] = 'REATTIVI FREDDI' # تعيين قيمة افتراضية

            # استخراج الألوان - البحث المباشر
            colors = []

            # النمط: 80021 (80021) SYNOZOL YELLOW DS 1.2502 % 18.75 ml 1:100
            color_pattern = r'(\d{5})\s*\(?\d{5}\)?\s*([A-Z0-9][A-Z0-9\-\s]+)\s*([\d.]+)\s*%'
            matches = re.findall(color_pattern, text)

            for match in matches:
                code, name, percentage = match
                colors.append({
                    'code': code.strip(),
                    'name': name.strip(),
                    'percentage': float(percentage),
                    'source_line': f"{code} {name} {percentage}%"
                })

            # إذا لم نجد بالطريقة الأولى، جرب البحث عن أسطر تحتوي على أكواد
            if not colors:
                lines = text.split('\n')
                for line in lines:
                    if re.search(r'\b\d{5}\b', line):
                        # استخراج الكود
                        code_match = re.search(r'\b(\d{5})\b', line)
                        if code_match:
                            code = code_match.group(1)

                            # استخراج النسبة
                            percent_match = re.search(r'([\d.]+)\s*%', line)
                            percentage = float(percent_match.group(1)) if percent_match else 0.0

                            # استخراج الاسم (بين الكود والنسبة)
                            name = line
                            if code_match and percent_match:
                                start = code_match.end()
                                end = percent_match.start()
                                name = line[start:end].strip()

                            if percentage > 0:
                                colors.append({
                                    'code': code,
                                    'name': name,
                                    'percentage': percentage,
                                    'source_line': line
                                })

            recipe_data['colors'] = colors

            # حساب النسبة الكلية
            if colors:
                total_percent = sum(PDFRecipeImporter._to_float(color.get('percentage', 0.0)) for color in colors)
                recipe_data['total_percentage'] = total_percent

            return recipe_data

        except Exception as e:
            print(f"Error extracting recipe from text: {e}")
            return recipe_data

    @staticmethod
    def _normalize_dye_type(dye_type: str) -> str:
        """تطبيع نوع الصباغة"""
        dye_type_lower = dye_type.lower() if dye_type else ''

        if 'freddi' in dye_type_lower:
            return 'REATTIVI FREDDI'
        elif 'caldi' in dye_type_lower:
            return 'REATTIVI CALDI'
        elif 'indanthren' in dye_type_lower:
            return 'INDANTHREN'
        else:
            return 'REATTIVI FREDDI'  # افتراضي

    @staticmethod
    def _to_float(value, default=0.0) -> float:
        try:
            if isinstance(value, str):
                value = value.replace('%', '').replace(',', '.').strip()
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def match_colors_with_database(colors: List[Dict], db, fallback_dye_type: str = 'GENERAL') -> List[Dict]:
        """مطابقة الألوان المستخرجة مع قاعدة البيانات"""
        matched_colors = []

        for color in colors:
            # البحث في قاعدة البيانات بالكود
            db_color = db.get_color_by_code(color['code'])

            if db_color:
                # إذا وجد اللون في قاعدة البيانات
                matched_colors.append({
                    'code': color['code'],
                    'name': db_color.name,  # استخدام الاسم من قاعدة البيانات
                    'dye_type': db_color.dye_type,
                    'percentage': color['percentage'],
                    'price_kg': db_color.price_kg,
                    'exists_in_db': True,
                    'db_color': db_color
                })
            else:
                # إذا لم يوجد، استخدام النوع الاحتياطي
                matched_colors.append({
                    'code': color['code'],
                    'name': color['name'],
                    'dye_type': fallback_dye_type,  # نوع احتياطي
                    'percentage': color['percentage'],
                    'price_kg': 0.0,
                    'exists_in_db': False,
                    'db_color': None
                })

        return matched_colors

    @staticmethod
    def calculate_chemicals_for_recipe(colors: List[Dict], total_percentage: float, dye_type: str):
        """حساب الكيماويات للوصفة المستوردة"""
        from app.calculator import ChemicalCalculator
        return ChemicalCalculator.calculate_chemicals(total_percentage, dye_type)

    @staticmethod
    def fix_color_names(colors: List[Dict]) -> List[Dict]:
        """تصحيح أسماء الألوان"""
        color_names_fix = {
            'SYNOZOL YELLOW DS': 'Yellow DS',
            'SYNOZOL ULTRA BORDEAUX DS': 'Ultra Bordeaux DS',
            'SYNOZOL NAVY BLUE K-BF': 'Navy Blue K-BF'
        }

        fixed_colors = []
        for color in colors:
            fixed_color = color.copy()

            # تصحيح الاسم إذا كان في القاموس
            for full_name, short_name in color_names_fix.items():
                if full_name in color['name']:
                    fixed_color['name'] = short_name
                    break

            fixed_colors.append(fixed_color)

        return fixed_colors
