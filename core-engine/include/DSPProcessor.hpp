#pragma once

#ifndef MECHPULSE_DSP_PROCESSOR_HPP
#define MECHPULSE_DSP_PROCESSOR_HPP

#include <cstddef>
#include <vector>
#include <complex>

namespace mechpulse {

/// @brief Digital Signal Processing processor for industrial vibration monitoring and diagnostics.
///
/// Implements edge DSP algorithms including Hanning windowing, Radix-2 Cooley-Tukey FFT,
/// and statistical time-domain feature extraction (RMS, Peak, Crest Factor, Kurtosis)
/// according to industrial standard ISO 10816.
class DSPProcessor {
public:
    DSPProcessor() = default;
    ~DSPProcessor() = default;

    /// @brief Applies a Hanning (Hann) window to a time-domain signal array.
    ///
    /// The window equation is:
    ///   w[i] = 0.5 * (1 - cos(2 * PI * i / (N - 1)))
    ///
    /// @param input Pointer to the raw time-domain samples.
    /// @param output Pointer to the destination buffer for windowed samples.
    /// @param sample_count Number of samples in the input/output buffer.
    void applyHanningWindow(const float* input, float* output, size_t sample_count) const;

    /// @brief Applies a Hanning (Hann) window to a vector of samples.
    /// @param input Input time-domain signal vector.
    /// @param output Destination vector for windowed signal (resized to match input).
    void applyHanningWindow(const std::vector<float>& input, std::vector<float>& output) const;

    /// @brief Computes single-sided magnitude spectrum using Radix-2 Cooley-Tukey FFT.
    ///
    /// The input length must be a power of two (e.g. 256).
    /// The output buffer must have capacity for sample_count / 2 bins (e.g. 128).
    /// Magnitudes are normalized to represent physical peak amplitude.
    ///
    /// @param windowed_signal Pointer to windowed time-domain samples of length sample_count.
    /// @param magnitude_spectrum Pointer to destination buffer for single-sided magnitude spectrum.
    /// @param sample_count Number of samples in time-domain input (must be power of 2).
    void computeFFT(const float* windowed_signal, float* magnitude_spectrum, size_t sample_count) const;

    /// @brief Computes single-sided magnitude spectrum for vector inputs.
    /// @param windowed_signal Input windowed signal vector.
    /// @param magnitude_spectrum Output vector for magnitude spectrum.
    void computeFFT(const std::vector<float>& windowed_signal, std::vector<float>& magnitude_spectrum) const;

    /// @brief Calculates the Root Mean Square (RMS) of a signal buffer.
    ///
    /// RMS = sqrt( (1 / N) * sum(x[i]^2) )
    ///
    /// @param signal Pointer to signal buffer.
    /// @param sample_count Number of samples.
    /// @return float Computed RMS value (in mm/s or g).
    float calculateRMS(const float* signal, size_t sample_count) const;

    /// @brief Calculates the Peak value (maximum absolute amplitude) of a signal buffer.
    ///
    /// Peak = max(|x[i]|)
    ///
    /// @param signal Pointer to signal buffer.
    /// @param sample_count Number of samples.
    /// @return float Computed peak amplitude.
    float calculatePeak(const float* signal, size_t sample_count) const;

    /// @brief Calculates the Crest Factor from peak and RMS amplitudes.
    ///
    /// Crest Factor = Peak / RMS
    ///
    /// @param peak Peak amplitude.
    /// @param rms RMS amplitude.
    /// @return float Crest factor ratio, or 0.0f if RMS is negligible.
    float calculateCrestFactor(float peak, float rms) const;

    /// @brief Calculates the Crest Factor directly from a signal buffer.
    /// @param signal Pointer to signal buffer.
    /// @param sample_count Number of samples.
    /// @return float Computed crest factor ratio.
    float calculateCrestFactor(const float* signal, size_t sample_count) const;

    /// @brief Calculates Pearson Kurtosis of a signal buffer.
    ///
    /// Kurtosis = E[(x - mean)^4] / variance^2
    /// A healthy machine exhibits Kurtosis ~ 3.0 (Gaussian). Impulsive bearing faults elevate Kurtosis > 4.0.
    ///
    /// @param signal Pointer to signal buffer.
    /// @param sample_count Number of samples.
    /// @return float Computed kurtosis.
    float calculateKurtosis(const float* signal, size_t sample_count) const;

private:
    /// @brief In-place recursive Radix-2 Cooley-Tukey Fast Fourier Transform.
    /// @param buffer Complex vector of length N (N must be power of 2).
    static void cooleyTukeyFFT(std::vector<std::complex<float>>& buffer);
};

} // namespace mechpulse

#endif // MECHPULSE_DSP_PROCESSOR_HPP
