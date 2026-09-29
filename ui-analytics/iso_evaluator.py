"""
محرك تقييم شدة الاهتزاز الميكانيكي وفق المعيار الدولي ISO 10816-3 / ISO 20816-3.
يقوم بتصنيف حالة الآلة وتحديد مناطق الخطورة (Zone A, B, C, D).
"""

from dataclasses import dataclass
from typing import Tuple

@dataclass
class ISOResult:
    zone: str               # 'A', 'B', 'C', 'D'
    status_label: str       # التسمية الفنية
    color_hex: str          # لون التنبيه
    description: str        # وصف الحالة لمهندس الصيانة
    recommendation: str     # الإجراء الموصى به

class ISO10816Evaluator:
    """
    تقييم سرعة الاهتزاز الفعالة (Vibration Velocity RMS mm/s)
    المجموعة 2: آلات متوسطة الحجم (Medium Machines 15kW - 300kW)
    قاعدة صلبة (Rigid Foundation)
    """
    # حدود المناطق الاهتزازية (mm/s RMS)
    ZONE_A_LIMIT = 1.4   # حتى 1.4 mm/s: حالة ممتازة (جديدة)
    ZONE_B_LIMIT = 2.8   # حتى 2.8 mm/s: مقبولة للتشغيل المستمر غير المقيد
    ZONE_C_LIMIT = 4.5   # حتى 4.5 mm/s: غير مرضية (تنبيه للصيانة القادمة)
    # أعلى من 4.5 mm/s: Zone D خطر حرج - إيقاف فوري للآلة

    @classmethod
    def evaluate(cls, rms_velocity: float) -> ISOResult:
        if rms_velocity <= cls.ZONE_A_LIMIT:
            return ISOResult(
                zone="A",
                status_label="ZONE A - EXCELLENT",
                color_hex="#2ecc71", # أخضر زاهي
                description="حالة الآلة ممتازة ومثالية للتشغيل المستمر.",
                recommendation="مواصلة المراقبة الروتينية الدورية."
            )
        elif rms_velocity <= cls.ZONE_B_LIMIT:
            return ISOResult(
                zone="B",
                status_label="ZONE B - ACCEPTABLE",
                color_hex="#00b894", # أخضر زمردي
                description="مستوى الاهتزاز طبيعي ومقبول للتشغيل طويل الأمد دون قيود.",
                recommendation="لا توجد إجراءات صيانة مطلوبة حالياً."
            )
        elif rms_velocity <= cls.ZONE_C_LIMIT:
            return ISOResult(
                zone="C",
                status_label="ZONE C - WARNING (ALERT)",
                color_hex="#f39c12", # برتقالي تحذيري
                description="الاهتزاز غير مرضٍ. يُحتمل وجود بداية اختلال توازن أو تآكل.",
                recommendation="التخطيط لإجراء فحص وصيانة وقائية في أقرب توقف مجدول."
            )
        else:
            return ISOResult(
                zone="D",
                status_label="ZONE D - CRITICAL DANGER",
                color_hex="#e74c3c", # أحمر خطر
                description="مستوى اهتزاز خطير جداً يتجاوز الحدود الآمنة للآلة.",
                recommendation="إيقاف تشغيل الآلة فوراً لتفادي الانهيار الكارثي للعمود أو المحامل!"
            )
