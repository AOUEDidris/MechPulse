#include "DSPProcessor.hpp"
#include <cmath>
#include <numeric>
#include <algorithm>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

DSPProcessor::DSPProcessor() {}

void DSPProcessor::applyHanningWindow(const std::vector<float>& input, std::vector<float>& output) {
    size_t N = input.size();
    output.resize(N);
    for (size_t i = 0; i < N; ++i) {
        float multiplier = 0.5f * (1.0f - std::cos(2.0f * (float)M_PI * i / (N - 1)));
        output[i] = input[i] * multiplier;
    }
}

void DSPProcessor::fftRecursive(std::vector<std::complex<float>>& a) {
    size_t n = a.size();
    if (n <= 1) return;

    std::vector<std::complex<float>> a0(n / 2), a1(n / 2);
    for (size_t i = 0; 2 * i < n; i++) {
        a0[i] = a[2 * i];
        a1[i] = a[2 * i + 1];
    }
    fftRecursive(a0);
    fftRecursive(a1);

    float ang = 2.0f * (float)M_PI / n;
    std::complex<float> w(1), wn(std::cos(ang), -std::sin(ang));
    for (size_t i = 0; 2 * i < n; i++) {
        a[i] = a0[i] + w * a1[i];
        a[i + n / 2] = a0[i] - w * a1[i];
        w *= wn;
    }
}

void DSPProcessor::computeFFT(const std::vector<float>& windowed_signal, std::vector<float>& magnitude_spectrum) {
    size_t N = windowed_signal.size();
    std::vector<std::complex<float>> complex_data(N);
    for (size_t i = 0; i < N; ++i) {
        complex_data[i] = std::complex<float>(windowed_signal[i], 0.0f);
    }

    fftRecursive(complex_data);

    size_t half_N = N / 2;
    magnitude_spectrum.resize(half_N);
    for (size_t i = 0; i < half_N; ++i) {
        // حساب السعة المطبعة (Normalized Amplitude)
        float mag = std::abs(complex_data[i]) * 2.0f / N;
        magnitude_spectrum[i] = mag;
    }
}

float DSPProcessor::calculateRMS(const std::vector<float>& signal) {
    if (signal.empty()) return 0.0f;
    float sum_sq = 0.0f;
    for (float val : signal) {
        sum_sq += val * val;
    }
    return std::sqrt(sum_sq / signal.size());
}

float DSPProcessor::calculatePeak(const std::vector<float>& signal) {
    float max_val = 0.0f;
    for (float val : signal) {
        float abs_val = std::abs(val);
        if (abs_val > max_val) {
            max_val = abs_val;
        }
    }
    return max_val;
}

float DSPProcessor::calculateCrestFactor(float peak, float rms) {
    if (rms < 1e-4f) return 0.0f;
    return peak / rms;
}

float DSPProcessor::calculateKurtosis(const std::vector<float>& signal, float mean) {
    if (signal.size() < 2) return 0.0f;
    float m2 = 0.0f;
    float m4 = 0.0f;

    for (float x : signal) {
        float diff = x - mean;
        float diff2 = diff * diff;
        m2 += diff2;
        m4 += diff2 * diff2;
    }

    size_t N = signal.size();
    float variance = m2 / N;
    if (variance < 1e-6f) return 3.0f; // طبيعي
    return (m4 / N) / (variance * variance);
}
