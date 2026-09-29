#include "SignalGenerator.hpp"

#include <cmath>
#include <chrono>

namespace mechpulse {

namespace {
    constexpr double PI_VAL = 3.14159265358979323846;
}

SignalGenerator::SignalGenerator(uint32_t sample_rate, float running_speed_hz)
    : m_sampleRate(sample_rate),
      m_runningSpeedHz(running_speed_hz),
      m_faultType(FaultType::Normal),
      m_currentTime(0.0),
      m_hasSpareGaussian(false),
      m_spareGaussian(0.0f),
      m_rng(static_cast<uint32_t>(std::chrono::system_clock::now().time_since_epoch().count())),
      m_uniformDist(0.0f, 1.0f) {
}

void SignalGenerator::setFaultType(FaultType type) {
    m_faultType = type;
}

FaultType SignalGenerator::getFaultType() const {
    return m_faultType;
}

void SignalGenerator::setRunningSpeed(float speed_hz) {
    m_runningSpeedHz = speed_hz;
}

float SignalGenerator::getRunningSpeed() const {
    return m_runningSpeedHz;
}

uint32_t SignalGenerator::getSampleRate() const {
    return m_sampleRate;
}

float SignalGenerator::getGaussianNoise(float mean, float stddev) {
    // Return cached value if available from previous Box-Muller transform
    if (m_hasSpareGaussian) {
        m_hasSpareGaussian = false;
        return mean + stddev * m_spareGaussian;
    }

    constexpr double TWO_PI = 2.0 * PI_VAL;
    float u1 = 0.0f;
    do {
        u1 = m_uniformDist(m_rng);
    } while (u1 <= 1e-9f); // Avoid log(0) singularity
    float u2 = m_uniformDist(m_rng);

    // Box-Muller transformation
    float radius = std::sqrt(-2.0f * std::log(u1));
    float theta  = static_cast<float>(TWO_PI * static_cast<double>(u2));

    m_spareGaussian = radius * std::sin(theta);
    m_hasSpareGaussian = true;

    return mean + stddev * (radius * std::cos(theta));
}

void SignalGenerator::generateBlock(size_t sample_count, float* buffer) {
    if (!buffer || sample_count == 0) {
        return;
    }

    const double dt = 1.0 / static_cast<double>(m_sampleRate);
    const double omega1 = 2.0 * PI_VAL * static_cast<double>(m_runningSpeedHz);       // 1X fundamental
    const double omega2 = 2.0 * omega1;                                               // 2X harmonic
    const double omega3 = 3.0 * omega1;                                               // 3X harmonic

    // Ball Pass Frequency Outer race (BPFO) defect frequency
    const double bpfo_freq = 4.8 * static_cast<double>(m_runningSpeedHz);
    const double bpfo_period = 1.0 / bpfo_freq;

    for (size_t i = 0; i < sample_count; ++i) {
        float sample = 0.0f;
        const double t = m_currentTime;

        switch (m_faultType) {
            case FaultType::Normal: {
                // Normal signature: 0.8 * sin(1X) + gaussian noise(0.25)
                float fundamental = 0.8f * static_cast<float>(std::sin(omega1 * t));
                float noise = getGaussianNoise(0.0f, 0.25f);
                sample = fundamental + noise;
                break;
            }

            case FaultType::Unbalance: {
                // Unbalance signature: 4.8 * sin(1X) + 0.4 * sin(2X) + noise -> strong 1X peak
                float comp1X = 4.8f * static_cast<float>(std::sin(omega1 * t));
                float comp2X = 0.4f * static_cast<float>(std::sin(omega2 * t));
                float noise  = getGaussianNoise(0.0f, 0.25f);
                sample = comp1X + comp2X + noise;
                break;
            }

            case FaultType::Misalignment: {
                // Misalignment signature: 2.5 * sin(1X) + 4.2 * sin(2X) + 1.2 * sin(3X) + noise -> 2X dominant
                float comp1X = 2.5f * static_cast<float>(std::sin(omega1 * t));
                float comp2X = 4.2f * static_cast<float>(std::sin(omega2 * t));
                float comp3X = 1.2f * static_cast<float>(std::sin(omega3 * t));
                float noise  = getGaussianNoise(0.0f, 0.25f);
                sample = comp1X + comp2X + comp3X + noise;
                break;
            }

            case FaultType::BearingFault: {
                // BearingFault signature: 1.2 * sin(1X) + BPFO impulse train at 4.8 * running_speed + heavier noise
                float comp1X = 1.2f * static_cast<float>(std::sin(omega1 * t));

                // BPFO periodic impact modeling with structural ringing decay
                double tau = std::fmod(t, bpfo_period);
                // Structural resonance ringing at 850 Hz excited by defect impact
                float impulse = 6.0f * std::exp(-static_cast<float>(tau) / 0.002f) *
                                static_cast<float>(std::sin(2.0 * PI_VAL * 850.0 * tau));

                // Heavier acoustic & friction noise from outer race spall
                float noise = getGaussianNoise(0.0f, 0.65f);
                sample = comp1X + impulse + noise;
                break;
            }
        }

        buffer[i] = sample;

        // Advance simulation time
        m_currentTime += dt;

        // Reset time at 1000.0 seconds to prevent floating point precision drift
        // Using integer reduction (1000.0 is an exact multiple of 25.0 Hz and 120.0 Hz)
        if (m_currentTime >= 1000.0) {
            m_currentTime -= 1000.0;
        }
    }
}

void SignalGenerator::generateBlock(float* buffer, size_t sample_count) {
    generateBlock(sample_count, buffer);
}

std::vector<float> SignalGenerator::generateBlock(size_t sample_count) {
    std::vector<float> buffer(sample_count);
    generateBlock(sample_count, buffer.data());
    return buffer;
}

} // namespace mechpulse
