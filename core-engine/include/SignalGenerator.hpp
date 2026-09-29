#pragma once
#include <vector>
#include <cstdint>

enum class FaultType : int32_t {
    NORMAL = 0,         // حالة سليمة طبيعية
    UNBALANCE = 1,      // اختلال توازن الدوار (Unbalance 1X)
    MISALIGNMENT = 2,   // عدم محاذاة المحاور (Misalignment 2X)
    BEARING_FAULT = 3   // عيب محمل الكريات (Bearing Outer Race BPFO)
};

class SignalGenerator {
public:
    SignalGenerator(uint32_t sample_rate = 1000, float running_speed_hz = 25.0f);

    void setFaultType(FaultType type);
    FaultType getFaultType() const;

    // توليد عينات إشارة اهتزازية لكتلة زمنية
    void generateBlock(size_t sample_count, std::vector<float>& buffer);

private:
    uint32_t m_sample_rate;
    float m_running_speed_hz; // 25 Hz = 1500 RPM
    float m_time;
    FaultType m_current_fault;

    float getGaussianNoise(float stddev = 0.2f);
};
