"""
حسابات الكيماويات والتكاليف
"""
from typing import List, Dict
from app.models import Chemical, RecipeDetails


class ChemicalCalculator:
    """حاسبة الكيماويات"""

    @staticmethod
    def calculate_chemicals(total_percentage: float, dye_type: str) -> List[Chemical]:
        """حساب الكيماويات المطلوبة بناءً على النسبة ونوع الصباغة"""
        dye_type_upper = dye_type.upper()

        if "INDANTHREN" in dye_type_upper:
            return ChemicalCalculator._calculate_indanthren(total_percentage, dye_type_upper)
        elif "REATTIVI CALDI" in dye_type_upper or "CALDI" in dye_type_upper:
            return ChemicalCalculator._calculate_reactivi_caldi(total_percentage)
        elif "REATTIVI FREDDI" in dye_type_upper or "FREDDI" in dye_type_upper:
            return ChemicalCalculator._calculate_reactivi_freddi(total_percentage)
        elif "OLTRI" in dye_type_upper or "OTHER" in dye_type_upper:
            return ChemicalCalculator._calculate_reactivi_oltri(total_percentage)
        else:
            # إذا لم يتطابق مع أي نوع، استخدم الإعدادات العامة
            return ChemicalCalculator._calculate_general(total_percentage)

    @staticmethod
    def _calculate_indanthren(total_percentage: float, dye_type: str) -> List[Chemical]:
        """حساب كيماويات Indanthren حسب النوع (IW, IN, IN SP, RS, RRN, ROSA R, BLACK)"""
        # تحديد نوع الـ Indanthren
        # ترتيب الفحص مهم جداً - نفحص الأنواع الأطول/الأكثر تحديداً أولاً
        if "IN SP" in dye_type:
            return ChemicalCalculator._indanthren_in_sp(total_percentage)
        elif "BLACK" in dye_type:
            return ChemicalCalculator._indanthren_iw(total_percentage)
        elif "RS" in dye_type:
            return ChemicalCalculator._indanthren_rs(total_percentage)
        elif "RRN" in dye_type:
            return ChemicalCalculator._indanthren_rrn(total_percentage)
        elif "ROSA" in dye_type or "ROSA R" in dye_type:
            return ChemicalCalculator._indanthren_rosa_r(total_percentage)
        elif "IW" in dye_type:
            return ChemicalCalculator._indanthren_iw(total_percentage)
        elif "IN" in dye_type:
            return ChemicalCalculator._indanthren_in(total_percentage)
        else:
            # افتراضي: IW
            return ChemicalCalculator._indanthren_iw(total_percentage)

    @staticmethod
    def _indanthren_iw(total_percentage: float) -> List[Chemical]:
        """Indanthren IW: SODA CAUSTICA + IDRO IW + SALE IW"""
        if total_percentage < 0.1:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=8.0, unit="ml/l"),
                Chemical(code="31180-IW", name="IDRO IW", quantity=3.0, unit="g/l"),
                Chemical(code="31360-IW", name="SALE IW", quantity=6.0, unit="g/l")
            ]
        elif 0.1 <= total_percentage < 0.5:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=10.0, unit="ml/l"),
                Chemical(code="31180-IW", name="IDRO IW", quantity=4.0, unit="g/l"),
                Chemical(code="31360-IW", name="SALE IW", quantity=8.0, unit="g/l")
            ]
        elif 0.5 <= total_percentage < 1.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=10.0, unit="ml/l"),
                Chemical(code="31180-IW", name="IDRO IW", quantity=4.0, unit="g/l"),
                Chemical(code="31360-IW", name="SALE IW", quantity=10.0, unit="g/l")
            ]
        elif 1.0 <= total_percentage < 1.5:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=11.0, unit="ml/l"),
                Chemical(code="31180-IW", name="IDRO IW", quantity=4.0, unit="g/l"),
                Chemical(code="31360-IW", name="SALE IW", quantity=10.0, unit="g/l")
            ]
        elif 1.5 <= total_percentage < 2.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=12.0, unit="ml/l"),
                Chemical(code="31180-IW", name="IDRO IW", quantity=5.0, unit="g/l"),
                Chemical(code="31360-IW", name="SALE IW", quantity=15.0, unit="g/l")
            ]
        elif 2.0 <= total_percentage < 3.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=13.0, unit="ml/l"),
                Chemical(code="31180-IW", name="IDRO IW", quantity=6.0, unit="g/l"),
                Chemical(code="31360-IW", name="SALE IW", quantity=15.0, unit="g/l")
            ]
        elif 3.0 <= total_percentage < 4.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=15.0, unit="ml/l"),
                Chemical(code="31180-IW", name="IDRO IW", quantity=7.0, unit="g/l"),
                Chemical(code="31360-IW", name="SALE IW", quantity=20.0, unit="g/l")
            ]
        elif 4.0 <= total_percentage < 5.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=16.0, unit="ml/l"),
                Chemical(code="31180-IW", name="IDRO IW", quantity=16.0, unit="g/l"),
                Chemical(code="31360-IW", name="SALE IW", quantity=20.0, unit="g/l")
            ]
        else:  # >= 5
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=20.0, unit="ml/l"),
                Chemical(code="31180-IW", name="IDRO IW", quantity=20.0, unit="g/l"),
                Chemical(code="31360-IW", name="SALE IW", quantity=22.0, unit="g/l")
            ]

    @staticmethod
    def _indanthren_in(total_percentage: float) -> List[Chemical]:
        """Indanthren IN: SODA CAUSTICA + IDRO IN (بدون ملح)"""
        if total_percentage < 0.1:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=15.0, unit="ml/l"),
                Chemical(code="31180-IN", name="IDRO IN", quantity=4.0, unit="g/l")
            ]
        elif 0.1 <= total_percentage < 0.5:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=16.0, unit="ml/l"),
                Chemical(code="31180-IN", name="IDRO IN", quantity=4.0, unit="g/l")
            ]
        elif 0.5 <= total_percentage < 1.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=18.0, unit="ml/l"),
                Chemical(code="31180-IN", name="IDRO IN", quantity=5.0, unit="g/l")
            ]
        elif 1.0 <= total_percentage < 1.5:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=20.0, unit="ml/l"),
                Chemical(code="31180-IN", name="IDRO IN", quantity=5.0, unit="g/l")
            ]
        elif 1.5 <= total_percentage < 2.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=22.0, unit="ml/l"),
                Chemical(code="31180-IN", name="IDRO IN", quantity=6.0, unit="g/l")
            ]
        elif 2.0 <= total_percentage < 3.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=24.0, unit="ml/l"),
                Chemical(code="31180-IN", name="IDRO IN", quantity=7.0, unit="g/l")
            ]
        elif 3.0 <= total_percentage < 4.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=26.0, unit="ml/l"),
                Chemical(code="31180-IN", name="IDRO IN", quantity=9.0, unit="g/l")
            ]
        elif 4.0 <= total_percentage < 5.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=28.0, unit="ml/l"),
                Chemical(code="31180-IN", name="IDRO IN", quantity=10.0, unit="g/l")
            ]
        else:  # >= 5
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=35.0, unit="ml/l"),
                Chemical(code="31180-IN", name="IDRO IN", quantity=12.0, unit="g/l")
            ]

    @staticmethod
    def _indanthren_in_sp(total_percentage: float) -> List[Chemical]:
        """Indanthren IN SP: SODA CAUSTICA + IDRO IN SP"""
        if total_percentage < 0.1:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=25.0, unit="ml/l"),
                Chemical(code="31180-IN-SP", name="IDRO IN SP", quantity=3.0, unit="g/l")
            ]
        elif 0.1 <= total_percentage < 0.5:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=25.0, unit="ml/l"),
                Chemical(code="31180-IN-SP", name="IDRO IN SP", quantity=4.0, unit="g/l")
            ]
        elif 0.5 <= total_percentage < 1.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=28.0, unit="ml/l"),
                Chemical(code="31180-IN-SP", name="IDRO IN SP", quantity=5.0, unit="g/l")
            ]
        elif 1.0 <= total_percentage < 1.5:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=30.0, unit="ml/l"),
                Chemical(code="31180-IN-SP", name="IDRO IN SP", quantity=5.0, unit="g/l")
            ]
        elif 1.5 <= total_percentage < 2.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=32.0, unit="ml/l"),
                Chemical(code="31180-IN-SP", name="IDRO IN SP", quantity=6.0, unit="g/l")
            ]
        elif 2.0 <= total_percentage < 3.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=34.0, unit="ml/l"),
                Chemical(code="31180-IN-SP", name="IDRO IN SP", quantity=6.0, unit="g/l")
            ]
        elif 3.0 <= total_percentage < 4.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=36.0, unit="ml/l"),
                Chemical(code="31180-IN-SP", name="IDRO IN SP", quantity=7.0, unit="g/l")
            ]
        elif 4.0 <= total_percentage < 5.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=38.0, unit="ml/l"),
                Chemical(code="31180-IN-SP", name="IDRO IN SP", quantity=8.0, unit="g/l")
            ]
        else:  # >= 5
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=40.0, unit="ml/l"),
                Chemical(code="31180-IN-SP", name="IDRO IN SP", quantity=9.0, unit="g/l")
            ]

    @staticmethod
    def _indanthren_rs(total_percentage: float) -> List[Chemical]:
        """Indanthren RS: SODA CAUSTICA + IDRO RS + GLUCOSIO"""
        if total_percentage < 0.1:
            # نسبة صغيرة جداً: نستخدم أدنى قيم RS بدلاً من قائمة فارغة لتجنب غياب الكيماويات
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=15.0, unit="ml/l"),
                Chemical(code="31180-RS", name="IDRO RS", quantity=4.0, unit="g/l"),
                Chemical(code="31160", name="GLUCOSIO", quantity=4.0, unit="g/l")
            ]
        elif 0.1 <= total_percentage < 0.5:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=17.0, unit="ml/l"),
                Chemical(code="31180-RS", name="IDRO RS", quantity=5.0, unit="g/l"),
                Chemical(code="31160", name="GLUCOSIO", quantity=5.0, unit="g/l")
            ]
        elif 0.5 <= total_percentage < 1.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=20.0, unit="ml/l"),
                Chemical(code="31180-RS", name="IDRO RS", quantity=5.0, unit="g/l"),
                Chemical(code="31160", name="GLUCOSIO", quantity=5.0, unit="g/l")
            ]
        elif 1.0 <= total_percentage < 1.5:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=22.0, unit="ml/l"),
                Chemical(code="31180-RS", name="IDRO RS", quantity=5.0, unit="g/l"),
                Chemical(code="31160", name="GLUCOSIO", quantity=5.0, unit="g/l")
            ]
        elif 1.5 <= total_percentage < 2.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=25.0, unit="ml/l"),
                Chemical(code="31180-RS", name="IDRO RS", quantity=6.0, unit="g/l"),
                Chemical(code="31160", name="GLUCOSIO", quantity=6.0, unit="g/l")
            ]
        elif 2.0 <= total_percentage < 3.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=30.0, unit="ml/l"),
                Chemical(code="31180-RS", name="IDRO RS", quantity=6.0, unit="g/l"),
                Chemical(code="31160", name="GLUCOSIO", quantity=5.0, unit="g/l")
            ]
        elif 3.0 <= total_percentage < 4.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=35.0, unit="ml/l"),
                Chemical(code="31180-RS", name="IDRO RS", quantity=7.0, unit="g/l"),
                Chemical(code="31160", name="GLUCOSIO", quantity=5.0, unit="g/l")
            ]
        elif 4.0 <= total_percentage < 5.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=40.0, unit="ml/l"),
                Chemical(code="31180-RS", name="IDRO RS", quantity=8.0, unit="g/l"),
                Chemical(code="31160", name="GLUCOSIO", quantity=5.0, unit="g/l")
            ]
        else:  # >= 5
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=44.0, unit="ml/l"),
                Chemical(code="31180-RS", name="IDRO RS", quantity=9.0, unit="g/l"),
                Chemical(code="31160", name="GLUCOSIO", quantity=5.0, unit="g/l")
            ]

    @staticmethod
    def _indanthren_rrn(total_percentage: float) -> List[Chemical]:
        """Indanthren RRN: SODA CAUSTICA + IDRO RRN"""
        if total_percentage < 0.1:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=10.0, unit="ml/l"),
                Chemical(code="31180-RRN", name="IDRO RRN", quantity=3.0, unit="g/l")
            ]
        elif 0.1 <= total_percentage < 0.5:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=12.0, unit="ml/l"),
                Chemical(code="31180-RRN", name="IDRO RRN", quantity=3.0, unit="g/l")
            ]
        elif 0.5 <= total_percentage < 1.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=14.0, unit="ml/l"),
                Chemical(code="31180-RRN", name="IDRO RRN", quantity=4.0, unit="g/l")
            ]
        elif 1.0 <= total_percentage < 1.5:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=18.0, unit="ml/l"),
                Chemical(code="31180-RRN", name="IDRO RRN", quantity=4.0, unit="g/l")
            ]
        elif 1.5 <= total_percentage < 2.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=20.0, unit="ml/l"),
                Chemical(code="31180-RRN", name="IDRO RRN", quantity=5.0, unit="g/l")
            ]
        elif 2.0 <= total_percentage < 3.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=24.0, unit="ml/l"),
                Chemical(code="31180-RRN", name="IDRO RRN", quantity=5.0, unit="g/l")
            ]
        elif 3.0 <= total_percentage < 4.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=30.0, unit="ml/l"),
                Chemical(code="31180-RRN", name="IDRO RRN", quantity=6.0, unit="g/l")
            ]
        elif 4.0 <= total_percentage < 5.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=35.0, unit="ml/l"),
                Chemical(code="31180-RRN", name="IDRO RRN", quantity=7.0, unit="g/l")
            ]
        else:  # >= 5
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=40.0, unit="ml/l"),
                Chemical(code="31180-RRN", name="IDRO RRN", quantity=8.0, unit="g/l")
            ]

    @staticmethod
    def _indanthren_rosa_r(total_percentage: float) -> List[Chemical]:
        """Indanthren ROSA R: SODA CAUSTICA + IDRO ROSA R"""
        if total_percentage < 0.1:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=8.0, unit="ml/l"),
                Chemical(code="31180-ROSA", name="IDRO ROSA R", quantity=3.0, unit="g/l")
            ]
        elif 0.1 <= total_percentage < 0.5:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=10.0, unit="ml/l"),
                Chemical(code="31180-ROSA", name="IDRO ROSA R", quantity=3.0, unit="g/l")
            ]
        elif 0.5 <= total_percentage < 1.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=12.0, unit="ml/l"),
                Chemical(code="31180-ROSA", name="IDRO ROSA R", quantity=4.0, unit="g/l")
            ]
        elif 1.0 <= total_percentage < 1.5:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=14.0, unit="ml/l"),
                Chemical(code="31180-ROSA", name="IDRO ROSA R", quantity=4.0, unit="g/l")
            ]
        elif 1.5 <= total_percentage < 2.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=15.0, unit="ml/l"),
                Chemical(code="31180-ROSA", name="IDRO ROSA R", quantity=5.0, unit="g/l")
            ]
        elif 2.0 <= total_percentage < 3.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=17.0, unit="ml/l"),
                Chemical(code="31180-ROSA", name="IDRO ROSA R", quantity=5.0, unit="g/l")
            ]
        elif 3.0 <= total_percentage < 4.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=19.0, unit="ml/l"),
                Chemical(code="31180-ROSA", name="IDRO ROSA R", quantity=6.0, unit="g/l")
            ]
        elif 4.0 <= total_percentage < 5.0:
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=20.0, unit="ml/l"),
                Chemical(code="31180-ROSA", name="IDRO ROSA R", quantity=6.0, unit="g/l")
            ]
        else:  # >= 5
            return [
                Chemical(code="31310", name="SODA CAUSTICA", quantity=24.0, unit="ml/l"),
                Chemical(code="31180-ROSA", name="IDRO ROSA R", quantity=8.0, unit="g/l")
            ]

    @staticmethod
    def _calculate_reactivi_freddi(total_percentage: float) -> List[Chemical]:
        """حساب كيماويات Reattivi Freddi بناءً على جدول النسب"""
        # جدول: Liquor ratio at and above 8:1
        # Dye% | Salt (g/l) | Soda ash (g/l) | NaOH (ml/l)
        if total_percentage < 0.5:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=30.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=8.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=0.0, unit="ml/l")
            ]
        elif 0.5 <= total_percentage < 1:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=40.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=5.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=0.5, unit="ml/l")
            ]
        elif 1 <= total_percentage < 2:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=50.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=5.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=1.0, unit="ml/l")
            ]
        elif 2 <= total_percentage < 3:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=60.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=5.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=1.25, unit="ml/l")
            ]
        elif 3 <= total_percentage < 4:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=80.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=5.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=1.5, unit="ml/l")
            ]
        elif 4 <= total_percentage < 5:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=80.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=5.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=2.0, unit="ml/l")
            ]
        else:  # total_percentage >= 5
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=100.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=5.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=2.5, unit="ml/l")
            ]

    @staticmethod
    def _calculate_reactivi_caldi(total_percentage: float) -> List[Chemical]:
        """حساب كيماويات Reattivi Caldi — نطاقات متصلة بدون فجوات"""
        if total_percentage < 0.5:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=70.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=6.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=1.2, unit="ml/l")
            ]
        elif total_percentage < 1.0:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=70.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=6.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=1.5, unit="ml/l")
            ]
        elif total_percentage < 1.5:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=70.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=6.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=1.5, unit="ml/l")
            ]
        elif total_percentage < 2.0:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=70.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=6.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=1.8, unit="ml/l")
            ]
        elif total_percentage < 2.5:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=90.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=6.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=1.6, unit="ml/l")
            ]
        elif total_percentage < 3.2:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=90.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=6.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=1.8, unit="ml/l")
            ]
        elif total_percentage < 3.5:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=90.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=6.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=2.1, unit="ml/l")
            ]
        elif total_percentage < 4.5:
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=90.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=6.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=2.4, unit="ml/l")
            ]
        else:  # >= 4.5
            return [
                Chemical(code="31360", name="SOLFATO SODICO", quantity=110.0, unit="g/l"),
                Chemical(code="31330", name="SODIO CARBONATO", quantity=6.0, unit="g/l"),
                Chemical(code="31310", name="SODA CAUSTICA", quantity=3.0, unit="ml/l")
            ]

    @staticmethod
    def _calculate_reactivi_oltri(total_percentage: float) -> List[Chemical]:
        """حساب كيماويات Reattivi Oltri"""
        return [
            Chemical(code="31360", name="SOLFATO SODICO", quantity=50.0, unit="g/l"),
            Chemical(code="31330", name="SODIO CARBONATO", quantity=total_percentage * 0.8, unit="g/l"),
            Chemical(code="", name="Leveling Agent", quantity=0.5, unit="g/l")
        ]

    @staticmethod
    def _calculate_general(total_percentage: float) -> List[Chemical]:
        """حساب كيماويات عامة"""
        return [
            Chemical(code="31360", name="SOLFATO SODICO", quantity=50.0, unit="g/l"),
            Chemical(code="31330", name="SODIO CARBONATO", quantity=total_percentage * 0.5, unit="g/l"),
            Chemical(code="", name="Wetting Agent", quantity=0.2, unit="g/l")
        ]

    @staticmethod
    def calculate_recipe_details(recipe_name: str, selected_colors: List[Dict]) -> RecipeDetails:
        """حساب تفاصيل الوصفة"""
        total_percent = sum(color["percentage"] for color in selected_colors)

        # تحديد نوع الصباغة المهيمن
        type_totals = {}
        for color in selected_colors:
            dye_type = color["dye_type"]
            type_totals[dye_type] = type_totals.get(dye_type, 0) + color["percentage"]

        if not type_totals:
            dominant_type = "GENERAL"
        else:
            dominant_type = max(type_totals, key=type_totals.get)

        # حساب الكيماويات
        chemicals = ChemicalCalculator.calculate_chemicals(total_percent, dominant_type)

        # حساب التكلفة
        total_cost = sum(
            (color["percentage"] / 100) * color.get("price_kg", 0)
            for color in selected_colors
        )

        return RecipeDetails(
            recipe=None,
            colors=selected_colors,
            chemicals=chemicals,
            total_percentage=total_percent,
            dominant_type=dominant_type,
            cost=total_cost
        )


class CostCalculator:
    """حاسبة التكاليف"""

    @staticmethod
    def calculate_recipe_cost(colors: List[Dict]) -> float:
        """حساب تكلفة الوصفة"""
        total_cost = 0.0
        for color in colors:
            percentage = color.get("percentage", 0)
            price_kg = color.get("price_kg", 0)
            color_cost = (percentage / 100) * price_kg
            total_cost += color_cost

        return total_cost

    @staticmethod
    def calculate_batch_cost(recipe_cost: float, batch_size: float) -> float:
        """حساب تكلفة الدفعة"""
        return recipe_cost * batch_size

    @staticmethod
    def calculate_with_waste(recipe_cost: float, waste_percentage: float = 5) -> float:
        """حساب التكلفة مع الهالك"""
        waste_factor = 1 + (waste_percentage / 100)
        return recipe_cost * waste_factor


# دوال مساعدة
def get_chemical_display_name(chemical: Chemical) -> str:
    """الحصول على اسم كيميائي للعرض"""
    return f"[{chemical.code}] {chemical.name}: {chemical.quantity} {chemical.unit}"


def format_chemicals_list(chemicals: List[Chemical]) -> str:
    """تنسيق قائمة الكيماويات كسلسلة نصية"""
    if not chemicals:
        return "No chemicals required"

    return " | ".join([get_chemical_display_name(chem) for chem in chemicals])
