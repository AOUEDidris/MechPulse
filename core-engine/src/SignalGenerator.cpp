#include "SignalGenerator.hpp"
#include <cmath>
#include <cstdlib>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

SignalGenerator::SignalGenerator(uint32_t sample_rate, float running_speed_hz)
    : m_sample_rate(sample_rate),
      m_running_speed_hz(running_speed_hz),
      m_time(0.0f),
      m_current_fault(FaultType::NORMAL) {}

void SignalGenerator::setFaultType(FaultType type) {
    m_current_fault = type;
}

FaultType SignalGenerator::getFaultType() const {
    return m_current_fault;
}

float SignalGenerator::getGaussianNoise(float stddev) {
    // خوارزمية Box-Muller لتوليد ضوضاء غاوسية بيضاء
    float u1 = ((float)rand() + 1.0f) / ((float)RAND_MAX + 1.0f);
    float u2 = ((float)rand() + 1.0f) / ((float)RAND_MAX + 1.0f);
    return stddev * std::sqrt(-2.0f * std::log(u1)) * std::cos(2.0f * (float)M_PI * u2);
}

void SignalGenerator::generateBlock(size_t sample_count, std::vector<float>& buffer) {
    buffer.resize(sample_count);
    float dt = 1.0f / (float)m_sample_rate;
    float f1 = m_running_speed_hz;       // 1X = 25 Hz (1500 RPM)
    float f2 = 2.0f * m_running_speed_hz; // 2X = 50 Hz
    float f_bpfo = 4.8f * m_running_speed_hz; // BPFO ~ 120 Hz

    for (size_t i = 0; i < sample_count; ++i) {
        float sig = 0.0f;
        float noise = getGaussianNoise(0.25f);

        switch (m_current_fault) {
            case FaultType::NORMAL:
                // اهتزاز أساسي منخفض (سليم وفق ISO 10816 Zone A)
                sig = 0.8f * std::sin(2.0f * (float)M_PI * f1 * m_time) + noise;
                break;

            case FaultType::UNBALANCE:
                // قمة حادة وعالية في التردد الأساسي 1X
                sig = 4.8f * std::sin(2.0f * (float)M_PI * f1 * m_time) +
                      0.4f * std::sin(2.0f * (float)M_PI * f2 * m_time) + noise;
                break;

            case FaultType::MISALIGNMENT:
                // سعة عالية في التوافقين 1X و 2X و 3X
                sig = 2.5f * std::sin(2.0f * (float)M_PI * f1 * m_time) +
                      4.2f * std::sin(2.0f * (float)M_PI * f2 * m_time) +
                      1.2f * std::sin(2.0f * (float)M_PI * 3.0f * f1 * m_time) + noise;
                break;

            case FaultType::BEARING_FAULT: {
                // نبضات اصطدام حادة بتردد BPFO (عامل قمة مرتفع ونبضات صدمية)
                float pulse = 0.0f;
                float mod = std::sin(2.0f * (float)M_PI * f_bpfo * m_time);
                if (mod > 0.85f) {
                    pulse = 7.5f * (mod - 0.85f);
                }
                sig = 1.2f * std::sin(2.0f * (float)M_PI * f1 * m_time) +
                      pulse + getGaussianNoise(0.5f);
                break;
            }
        }

        buffer[i] = sig;
        m_time += dt;
        if (m_time > 1000.0f) m_time = 0.0f; // منع تراكم الخطأ العائم
    }
}
