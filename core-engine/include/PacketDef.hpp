#pragma once
#include <cstdint>

// بنية بيانات الحزمة الثنائية (Binary Packed Struct) لضمان الصفرية في زمن التأخير
#pragma pack(push, 1)
struct VibrationPacket {
    double timestamp;       // الطابع الزمني بالثواني (Unix Timestamp)
    float rms_velocity;     // السرعة الاهتزازية الفعالة (mm/s RMS)
    float peak_accel;       // أقصى تسارع (Peak Acceleration - g)
    float crest_factor;     // عامل القمة لكشف تآكل المحامل (Crest Factor)
    float kurtosis;         // معامل التفرطح (Kurtosis)
    uint32_t sample_rate;   // معدل أخذ العينات (Hz - مثلاً 1000 أو 2000)
    uint32_t sample_count;  // عدد العينات في الحزمة (256)
    int32_t fault_mode;     // نوع الحالة: 0=طبيعي، 1=اختلال توازن، 2=عدم محاذاة، 3=تلف محمل
    float samples[256];     // مصفوفة عينات المجال الزمني (Waveform Samples)
    float fft_spectrum[128];// سعة طيف الترددات (FFT Magnitude Spectrum)
};
#pragma pack(pop)
