#include "DSPProcessor.hpp"

#include <cmath>
#include <algorithm>
#include <stdexcept>

namespace mechpulse {

namespace {
    constexpr double PI_VAL = 3.14159265358979323846;
}

void DSPProcessor::applyHanningWindow(const float* input, float* output, size_t sample_count) const {
    if (!input || !output || sample_count == 0) {
        return;
    }

    if (sample_count == 1) {
        output[0] = input[0];
        return;
    }

    const double denom = static_cast<double>(sample_count - 1);
    for (size_t i = 0; i < sample_count; ++i) {
        // Hanning window formula: w[i] = 0.5 * (1.0 - cos(2.0 * pi * i / (N - 1)))
        double w = 0.5 * (1.0 - std::cos(2.0 * PI_VAL * static_cast<double>(i) / denom));
        output[i] = input[i] * static_cast<float>(w);
    }
}

void DSPProcessor::applyHanningWindow(const std::vector<float>& input, std::vector<float>& output) const {
    output.resize(input.size());
    applyHanningWindow(input.data(), output.data(), input.size());
}

void DSPProcessor::cooleyTukeyFFT(std::vector<std::complex<float>>& buffer) {
    const size_t N = buffer.size();
    if (N <= 1) {
        return;
    }

    const size_t half = N / 2;
    std::vector<std::complex<float>> even(half);
    std::vector<std::complex<float>> odd(half);

    for (size_t i = 0; i < half; ++i) {
        even[i] = buffer[2 * i];
        odd[i]  = buffer[2 * i + 1];
    }

    // Recursive Cooley-Tukey Radix-2 decomposition
    cooleyTukeyFFT(even);
    cooleyTukeyFFT(odd);

    // Recombine halves with twiddle factors W_N^k = exp(-2*pi*i*k / N)
    for (size_t k = 0; k < half; ++k) {
        double angle = -2.0 * PI_VAL * static_cast<double>(k) / static_cast<double>(N);
        std::complex<float> twiddle(static_cast<float>(std::cos(angle)),
                                    static_cast<float>(std::sin(angle)));
        std::complex<float> t = twiddle * odd[k];
        buffer[k]        = even[k] + t;
        buffer[k + half] = even[k] - t;
    }
}

void DSPProcessor::computeFFT(const float* windowed_signal, float* magnitude_spectrum, size_t sample_count) const {
    if (!windowed_signal || !magnitude_spectrum || sample_count < 2) {
        return;
    }

    // Power-of-two check
    if ((sample_count & (sample_count - 1)) != 0) {
        return;
    }

    // Populate complex buffer
    std::vector<std::complex<float>> complex_data(sample_count);
    for (size_t i = 0; i < sample_count; ++i) {
        complex_data[i] = std::complex<float>(windowed_signal[i], 0.0f);
    }

    // Compute Radix-2 FFT
    cooleyTukeyFFT(complex_data);

    // Compute single-sided magnitude spectrum (0 to sample_count / 2)
    // Scale factor: DC component is normalized by N, AC components normalized by 2/N
    const size_t num_bins = sample_count / 2;
    const float norm_dc = 1.0f / static_cast<float>(sample_count);
    const float norm_ac = 2.0f / static_cast<float>(sample_count);

    magnitude_spectrum[0] = std::abs(complex_data[0]) * norm_dc;
    for (size_t k = 1; k < num_bins; ++k) {
        magnitude_spectrum[k] = std::abs(complex_data[k]) * norm_ac;
    }
}

void DSPProcessor::computeFFT(const std::vector<float>& windowed_signal, std::vector<float>& magnitude_spectrum) const {
    if (windowed_signal.size() < 2) {
        magnitude_spectrum.clear();
        return;
    }
    magnitude_spectrum.resize(windowed_signal.size() / 2);
    computeFFT(windowed_signal.data(), magnitude_spectrum.data(), windowed_signal.size());
}

float DSPProcessor::calculateRMS(const float* signal, size_t sample_count) const {
    if (!signal || sample_count == 0) {
        return 0.0f;
    }

    double sum_squares = 0.0;
    for (size_t i = 0; i < sample_count; ++i) {
        double val = static_cast<double>(signal[i]);
        sum_squares += val * val;
    }

    return static_cast<float>(std::sqrt(sum_squares / static_cast<double>(sample_count)));
}

float DSPProcessor::calculatePeak(const float* signal, size_t sample_count) const {
    if (!signal || sample_count == 0) {
        return 0.0f;
    }

    float max_peak = 0.0f;
    for (size_t i = 0; i < sample_count; ++i) {
        float abs_val = std::fabs(signal[i]);
        if (abs_val > max_peak) {
            max_peak = abs_val;
        }
    }

    return max_peak;
}

float DSPProcessor::calculateCrestFactor(float peak, float rms) const {
    if (rms <= 1e-7f) {
        return 0.0f;
    }
    return peak / rms;
}

float DSPProcessor::calculateCrestFactor(const float* signal, size_t sample_count) const {
    float rms  = calculateRMS(signal, sample_count);
    float peak = calculatePeak(signal, sample_count);
    return calculateCrestFactor(peak, rms);
}

float DSPProcessor::calculateKurtosis(const float* signal, size_t sample_count) const {
    if (!signal || sample_count < 2) {
        return 0.0f;
    }

    // Step 1: Mean calculation
    double sum = 0.0;
    for (size_t i = 0; i < sample_count; ++i) {
        sum += static_cast<double>(signal[i]);
    }
    const double mean = sum / static_cast<double>(sample_count);

    // Step 2: Second and Fourth Central Moments
    double sum_sq_diff = 0.0;
    double sum_quad_diff = 0.0;
    for (size_t i = 0; i < sample_count; ++i) {
        double diff = static_cast<double>(signal[i]) - mean;
        double diff2 = diff * diff;
        sum_sq_diff += diff2;
        sum_quad_diff += diff2 * diff2;
    }

    const double variance = sum_sq_diff / static_cast<double>(sample_count);
    if (variance < 1e-12) {
        return 0.0f;
    }

    const double m4 = sum_quad_diff / static_cast<double>(sample_count);
    const double kurtosis = m4 / (variance * variance);

    return static_cast<float>(kurtosis);
}

} // namespace mechpulse
