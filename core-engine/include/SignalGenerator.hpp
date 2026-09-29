#pragma once

#ifndef MECHPULSE_SIGNAL_GENERATOR_HPP
#define MECHPULSE_SIGNAL_GENERATOR_HPP

#include <cstdint>
#include <cstddef>
#include <random>
#include <vector>

namespace mechpulse {

/// @brief Mechanical condition classification modes for rotary industrial assets.
enum class FaultType : int32_t {
    Normal       = 0,  ///< Baseline nominal operation with low-amplitude Gaussian ambient noise
    Unbalance    = 1,  ///< Dynamic mass unbalance (dominant 1X shaft rotational harmonic)
    Misalignment = 2,  ///< Mechanical angular/parallel misalignment (dominant 2X harmonic)
    BearingFault = 3   ///< Outer race defect (BPFO) periodic high-frequency impulse train
};

/// @brief Industrial vibration signal synthesizer for real-time edge testing and validation.
///
/// Models realistic multi-harmonic mechanical fault signatures and structural impulse responses.
class SignalGenerator {
public:
    /// @brief Constructs a SignalGenerator instance.
    /// @param sample_rate Telemetry acquisition rate in Hz (default: 2560 Hz).
    /// @param running_speed_hz Shaft rotational frequency in Hz (default: 25.0 Hz = 1500 RPM).
    explicit SignalGenerator(uint32_t sample_rate = 2560, float running_speed_hz = 25.0f);

    ~SignalGenerator() = default;

    /// @brief Sets the active simulated mechanical fault type.
    /// @param type FaultType enum value.
    void setFaultType(FaultType type);

    /// @brief Gets the current simulated mechanical fault type.
    /// @return Active FaultType enum.
    FaultType getFaultType() const;

    /// @brief Generates a block of synthetic vibration samples.
    /// @param sample_count Number of samples to synthesize.
    /// @param buffer Destination array pointer of size at least sample_count.
    void generateBlock(size_t sample_count, float* buffer);

    /// @brief Overload of generateBlock accepting buffer pointer first.
    /// @param buffer Destination array pointer.
    /// @param sample_count Number of samples to synthesize.
    void generateBlock(float* buffer, size_t sample_count);

    /// @brief Generates a block of synthetic vibration samples returning a vector.
    /// @param sample_count Number of samples to synthesize.
    /// @return std::vector<float> Synthesized vibration samples.
    std::vector<float> generateBlock(size_t sample_count);

    /// @brief Updates the shaft running speed.
    /// @param speed_hz Rotational frequency in Hz.
    void setRunningSpeed(float speed_hz);

    /// @brief Retrieves the shaft running speed.
    /// @return Rotational frequency in Hz.
    float getRunningSpeed() const;

    /// @brief Retrieves the telemetry sample rate.
    /// @return Sampling rate in Hz.
    uint32_t getSampleRate() const;

private:
    /// @brief Generates a zero-mean Gaussian random variable using the Box-Muller transform.
    /// @param mean Mean value of the distribution (typically 0.0f).
    /// @param stddev Standard deviation (noise amplitude scaling).
    /// @return float Sample drawn from N(mean, stddev^2).
    float getGaussianNoise(float mean, float stddev);

    uint32_t  m_sampleRate;
    float     m_runningSpeedHz;
    FaultType m_faultType;
    double    m_currentTime;

    // Box-Muller cache and uniform random generator
    bool                                  m_hasSpareGaussian;
    float                                 m_spareGaussian;
    std::mt19937                          m_rng;
    std::uniform_real_distribution<float> m_uniformDist;
};

} // namespace mechpulse

#endif // MECHPULSE_SIGNAL_GENERATOR_HPP
